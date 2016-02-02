#!/usr/bin/env python2.7
"""
Class used to control system Deamons, either Upstart or SysV.
"""
import argparse, textwrap, errno
import fnmatch, subprocess, re, datetime
import xml.etree.ElementTree as ElementTree

# Import Brandt Common Utilities
import sys, os
sys.path.append( os.path.realpath( os.path.join( os.path.dirname(__file__), "/opt/brandt/common" ) ) )
import brandt
sys.path.pop()

version = 0.3
args = {}
args['output'] = "text"
args['arguments'] = []
args['debug'] = False
args['autocomplete'] = False
args['setup'] = False
args['list'] = False
args['status_all'] = False
args['upstart'] = False
args['sysv'] = False
args['name'] = ''
args['diskspace'] = False
args['preamble'] = False
args['command'] = False
encoding = "utf-8"

class customUsageVersion(argparse.Action):
  def __init__(self, option_strings, dest, **kwargs):
    self.__version = str(kwargs.get('version', ''))
    self.__prog = str(kwargs.get('prog', os.path.basename(__file__)))
    self.__row = min(int(kwargs.get('max', 80)), brandt.getTerminalSize()[0])
    self.__exit = int(kwargs.get('exit', 0))
    super(customUsageVersion, self).__init__(option_strings, dest, nargs=0)
  def __call__(self, parser, namespace, values, option_string=None):
    # print('%r %r %r' % (namespace, values, option_string))
    if self.__version:
      print self.__prog + " " + self.__version
      print "Copyright (C) 2013 Free Software Foundation, Inc."
      print "License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>."
      version  = "This program is free software: you can redistribute it and/or modify "
      version += "it under the terms of the GNU General Public License as published by "
      version += "the Free Software Foundation, either version 3 of the License, or "
      version += "(at your option) any later version."
      print textwrap.fill(version, self.__row)
      version  = "This program is distributed in the hope that it will be useful, "
      version += "but WITHOUT ANY WARRANTY; without even the implied warranty of "
      version += "MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the "
      version += "GNU General Public License for more details."
      print textwrap.fill(version, self.__row)
      print "\nWritten by Bob Brandt <projects@brandt.ie>."
    else:
      print "Usage: " + self.__prog + " [-o {text,xml,pretty}] [-n NAME] [--list] [--status-all]"
      print " " * (len(self.__prog) + 7), "[-u|s] Deamon Command"
      print " " * (len(self.__prog) + 3), "or  -c Command Arguments ..."
      print " " * (len(self.__prog) + 3), "or  -d [DiskPercent]"
      print " " * (len(self.__prog) + 3), "or  -p"
      print "\nScript used to controlUpstart and SysV Deamons.\n"
      print "Options:"
      options = []
      options.append(("-h, --help",       "Show this help message and exit"))
      options.append(("-v, --version",    "Show program's version number and exit"))
      options.append(("-o, --output",     "Display output type. {text,xml,pretty}"))
      options.append(("-l, --list",       "List all Deamons"))
      options.append(("-a, --status-all", "Show the status of all deamons"))
      options.append(("-u, --upstart",    "Use the Upstart version of the deamon"))
      options.append(("-s, --sysv",       "Use the SysV version of the deamon"))
      options.append(("-n, --name NAME",  "Use the given NAME in the \"pretty\" output"))
      options.append(("-c, --command",    "Run the command given"))
      options.append(("-d, --diskspace",  "Return Disk Space Usage"))
      options.append(("-p, --preamble",   "Return Uptime and Load averages, Task and CPU states and Memory usage (Not available via xml output)"))
      length = max( [ len(option[0]) for option in options ] )
      for option in options:
        description =  textwrap.wrap(option[1], (self.__row - length - 5))
        print "  " + option[0].ljust(length) + "   " + description[0]
        for n in range(1,len(description)): print " " * (length + 5) + description[n]
    exit(self.__exit)
def command_line_args():
  global args
  parser = argparse.ArgumentParser(add_help=False)
  parser.add_argument('-v', '--version', action=customUsageVersion, version=version, max=80)
  parser.add_argument('-h', '--help', action=customUsageVersion)
  parser.add_argument('-o', '--output',
                    required=False,
                    default=args['output'],
                    choices=['text', 'xml', 'pretty'],
                    help='Display output type.')
  parser.add_argument('--setup',
                    required=False,
                    action='store_true')    
  parser.add_argument('--debug',
                    required=False,
                    action='store_true')  
  parser.add_argument('--autocomplete',
                    required=False,
                    action='store_true')
  parser.add_argument('--list',
                    required=False,
                    action='store_true')
  parser.add_argument('-a', '--status-all',
                    required=False,
                    action='store_true')
  parser.add_argument('-u', '--upstart',
                    required=False,
                    action='store_true')
  parser.add_argument('-s', '--sysv',
                    required=False,
                    action='store_true')
  parser.add_argument('-n', '--name',
                    required=False,
                    action='store',
                    type=str)
  parser.add_argument('-d', '--diskspace',
                    required=False,
                    action='store_true')
  parser.add_argument('-p', '--preamble',
                    required=False,
                    action='store_true')
  parser.add_argument('-c', '--command',
                    required=False,
                    action='store_true')  
  parser.add_argument('arguments',
                    nargs=argparse.REMAINDER,
                    type=str)
  args.update(vars(parser.parse_args()))

def setup():
  if os.geteuid() != 0:
    exit("You need to have root privileges to setup this script.\nPlease try again, this time using 'sudo'.\nExiting.")

  # Create Symbolic link at /usr/local/bin
  src = os.path.realpath( __file__ )
  dst = os.path.join( '/usr/local/bin', os.path.splitext(os.path.basename(__file__))[0] )
  try:
    os.symlink(src, dst)
  except OSError, e:
    if e.errno == errno.EEXIST:
      os.remove(dst)
      os.symlink(src, dst)

  exit()

class outputPretty(object):
  """
  Return a string that will display a color coded status message of a command
  formated to the width of the current terminal.
  """
  def __init__(self):
    # Get Terminal Width and Height
    def ioctl_GWINSZ(fd):
      try:
        import fcntl, termios, struct
        cr = struct.unpack('hh', fcntl.ioctl(fd, termios.TIOCGWINSZ, '1234'))
      except:
        return
      return cr
    cr = ioctl_GWINSZ(0) or ioctl_GWINSZ(1) or ioctl_GWINSZ(2)
    if not cr:
      try:
        fd = os.open(os.ctermid(), os.O_RDONLY)
        cr = ioctl_GWINSZ(fd)
        os.close(fd)
      except:
        pass
    if not cr:
      try:
        cr = os.popen('stty size', 'r').read().split()
      except:
        pass
    if not cr:
      cr = (os.environ.get('LINES', 25), os.environ.get('COLUMNS', 80))
    self.rows, self.columns = cr
    self.backspace = 10

    self.esc='\033'
    self.cr = '\015'
    self.extd=self.esc + '[1m'
    self.attn=self.esc + '[1;33m'
    self.done=self.esc + '[1;32m'
    self.norm=self.esc + '[m\017'
    self.warn=self.esc + '[1;31m'
    self.stat=self.cr + self.esc + '[' + str(self.columns) + 'C' + self.esc + '[' + str(self.backspace) + 'D'

    self.state={"unused": self.stat + self.extd + 'unused' + self.norm,
                      "unknown": self.stat + self.attn + 'unknown' + self.norm,
                      "failed": self.stat + self.warn + 'failed' + self.norm,
                      "missed": self.stat + self.warn + 'missing' + self.norm,
                      "skipped": self.stat + self.attn + 'skipped' + self.norm,
                      "running": self.stat + self.done + 'running' + self.norm,
                      "done": self.stat + self.done + 'done' + self.norm,
                      "dead": self.stat + self.warn + 'dead' + self.norm }

  def write(self, prefix, command, returncode):
    if command in ['status', 'test']:
      states = ["running", "dead", "dead", "unused", "unknown", "dead"]
    else:
      states = ["done", "failed", "failed", "missed", "failed", "skipped", "unused", "failed"]
    returncode = int(returncode)

    if returncode < 0 or  returncode >= len(states):
      s = states[-1]
    else:
      s = states[returncode]

    return prefix + self.state[s]


def getCommand(cmdList, output, name = "", xmlAttribs = {}):
  """
  Run a specified command and return a string with the output
  """
  p = subprocess.Popen(cmdList, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  out, err = p.communicate()
  rc = p.returncode

  if not name: name = cmdList[0]
  if output == "xml":
    xml = ElementTree.Element('deamons')
    xmlAttribs.update({'name':name, 'cmdStr':" ".join(cmdList), "returncode":rc })
    cmd = ElementTree.SubElement(xml, 'deamon', attrib={ k:str(xmlAttribs[k]) for k in xmlAttribs.keys() } )
    o =  ElementTree.SubElement(cmd, 'output')
    o.text = str(out).strip()
    if err:
      e =  ElementTree.SubElement(cmd, 'error')
      e.text = str(err).strip()
    return rc, '<?xml version="1.0" encoding="' + encoding + '"?>\n' + ElementTree.tostring(xml, encoding=encoding, method="xml")
  elif output == "text":
    if err: out = out + '\n' + err    
    return rc, out
  else:
    return rc, outputPretty().write(name, "status", rc)




class deamonClass(object):
  def __toggle(self, sysv = None, upstart = None):
    if (sysv == upstart) :
      self.__show = set(["sysv","upstart"])
    elif sysv == False:
      self.__show = set(["upstart"])
    elif upstart == False:
      self.__show = set(["sysv"])
    elif sysv is None:
      self.__show = set(["upstart"])
    elif upstart is None:
      self.__show = set(["sysv"])
    else:
      self.__show = set(["sysv","upstart"])

  def __filterList(self, lists, filters):
    if filters:
      tmp = set()
      for f in filters:
        tmp.update( fnmatch.filter(lists, f) )
      return tmp
    else:
      return lists

  def __debugPrint(self, *strings):
    if self.__debug:
      sys.stderr.write(" ".join( [str(s) for s in strings] ) + '\n')

  def __init__(self, filters = None, sysv = None, upstart = None, debug = False, xmlEncoding = "utf-8"):
    self.__debug = debug
    self.__debugPrint('Checking for root privilege')
    if os.geteuid() != 0:
      exit("You need to have root privileges to run this class.\nPlease try again, this time using 'sudo'.\nExiting.")

    self.__encoding = encoding
    self.__deamons = {}
    self.__commands = {'start':'Starting ', 
                       'stop':'Stopping ', 
                       'restart':'Restarting ', 
                       'reload':'Reloading ', 
                       'status':'Checking for ', 
                       'test':'Checking for ',
                       'try-restart':'Restarting ', 
                       'condrestart':'Restarting ', 
                       'force-reload':'Reloading ', 
                       'probe':'Probing '}
                       #Probe = Conditional Reload
    self.__upstartcommands = ['start', 'stop', 'restart', 'reload', 'status', 'list', 'emit', 'reload-configuration', 'version', 'log-priority', 'show-config', 'check-config', 'notify-disk-writeable', ' notify-dbus-address', 'list-env', 'reset-env', 'list-sessions']
    self.__encoding = xmlEncoding

    self.__toggle(sysv,upstart)
    if filters is None:
      self.__filters = []
    else:
      self.__filters = list(filters)    

  isloaded   = property(lambda self: bool(self.__deamons))
  deamons    = property(lambda self: self.__deamons)
  deamonKeys = property(lambda self: sorted(self.__deamons.keys()))
  show       = property(lambda self: sorted(self.__show))
  encoding   = property(lambda self: self.__encoding)

  def upstart(self, deamon):
    if str(deamon).lower() in self.deamonKeys:
      deamon = str(deamon).lower() 
      return bool( self.__deamons[deamon].has_key('upstart') and self.__deamons[deamon]['upstart'].has_key('config') )
    return False

  def sysv(self, deamon):
    if str(deamon).lower() in self.deamonKeys:
      deamon = str(deamon).lower() 
      return bool( self.__deamons[deamon].has_key('sysv') )
    return False

  def load(self, filters = None, sysv = None, upstart = None):
    if (not sysv is None) or (not upstart is None):
      self.__toggle(sysv,upstart)

    if not filters is None:
      self.__filters = list(filters)

    self.__deamons = {}
    if 'upstart' in self.show:
      for (dirpath, dirnames, filenames) in os.walk('/etc/init/'):
        tmp = self.__filterList( [ str(f)[:-5] for f in filenames if f and str(f).lower()[-5:] == '.conf' ], self.__filters)

        for f in tmp:
          self.__debugPrint("Processing upstart script" ,f + ".conf")

          p = subprocess.Popen(['initctl', 'show-config', '-e', f], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
          out, err = p.communicate()
          rc = p.returncode
          if err or rc > 0: pass

          self.__debugPrint("Upstart Script", f + ".conf", 'is valid')

          out = out.split('\n')
          if len(out) > 0: out = out[1:]
          out = [str(s).strip() for s in out if s]

          if not self.__deamons.has_key(f.lower()): self.__deamons[f.lower()] = {}
          self.__deamons[f.lower()]['upstart'] = {'deamon':f, 'config':out}
        break

    if 'sysv' in self.show:
      self.__rcdir = ''
      if os.path.isdir('/etc/init.d/rc0.d'): self.__rcdir = '/etc/init.d'
      if os.path.isdir('/etc/rc0.d'): self.__rcdir = '/etc'
      self.__debugPrint('SysV RC directories are at', self.__rcdir)

      if self.__rcdir:
        for (dirpath, dirnames, filenames) in os.walk('/etc/init.d/'):
          for f in self.__filterList(filenames,self.__filters):
            if not f or f[0] == '.': continue
            if f in ['README', 'rc', 'rc.local', 'skeleton']: continue

            if not self.__deamons.has_key(f.lower()): self.__deamons[f.lower()] = {}
            self.__deamons[f.lower()]['sysv'] = {'deamon':f}

            for runlevel in ['rc0.d','rc1.d','rc2.d','rc3.d','rc4.d','rc5.d','rc6.d','rcS.d']:
              for (dirpath2, dirnames2, filenames2) in os.walk(os.path.join(self.__rcdir, runlevel)):
                for f2 in filenames2:
                  if os.path.islink(os.path.join(dirpath2,f2)):
                    if os.path.basename(os.readlink(os.path.join(dirpath2,f2))) == f:
                      if not self.__deamons[f.lower()]['sysv'].has_key(runlevel): self.__deamons[f.lower()]['sysv'][runlevel] = []
                      self.__deamons[f.lower()]['sysv'][runlevel].append(os.path.join(dirpath2,f2))
                break
          break

  def list(self, filters = None, output = "text", sysv = None, upstart = None):
    output = str(output).lower()
    if output not in ["text", "xml"]: output = "text"

    if not filters is None:
      tmpKeys = self.__filterList(self.deamonKeys, list(filters))
    else:
      tmpKeys = self.deamonKeys

    tmpShow = self.show
    if not sysv is None or not upstart is None:
      self.__toggle(sysv,upstart)

    if output == "xml":
      output = ""      
      xml = ElementTree.Element('deamons')
      for k in tmpKeys:
        d = ElementTree.SubElement(xml, 'deamon', attrib={'name':k})
        if 'upstart' in self.show and self.__deamons[k].has_key('upstart') and self.__deamons[k]['upstart'].has_key('config'):
          up = ElementTree.SubElement(d, 'upstart', attrib={'name':self.__deamons[k]['upstart']['deamon']})
          for line in self.__deamons[k]['upstart']['config']:
            config = ElementTree.SubElement(up, 'config')
            config.text = line
        if 'sysv' in self.show and self.__deamons[k].has_key('sysv'):
          sysv = ElementTree.SubElement(d, 'sysv', attrib={'rc0':str(self.__deamons[k]['sysv'].has_key('rc0.d')), 
                                                                                       'rc1':str(self.__deamons[k]['sysv'].has_key('rc1.d')), 
                                                                                       'rc2':str(self.__deamons[k]['sysv'].has_key('rc2.d')), 
                                                                                       'rc3':str(self.__deamons[k]['sysv'].has_key('rc3.d')), 
                                                                                       'rc4':str(self.__deamons[k]['sysv'].has_key('rc4.d')), 
                                                                                       'rc5':str(self.__deamons[k]['sysv'].has_key('rc5.d')), 
                                                                                       'rc6':str(self.__deamons[k]['sysv'].has_key('rc6.d')), 
                                                                                       'rcS':str(self.__deamons[k]['sysv'].has_key('rcS.d')),
                                                                                       'name':self.__deamons[k]['sysv']['deamon'] })
      output = '<?xml version="1.0" encoding="' + self.__encoding + '"?>\n' + ElementTree.tostring(xml, encoding=self.__encoding, method="xml")
    else:
      output = ""
      maxlen = max([0] + [len(k) for k in self.deamonKeys]) + 3
      for k in sorted(tmpKeys):
        if 'upstart' in self.show and self.__deamons[k].has_key('upstart') and self.__deamons[k]['upstart'].has_key('config'):
          for l in range(len(self.__deamons[k]['upstart']['config'])):
            if l == 0:
              output += str(k + ":").ljust(maxlen) + self.__deamons[k]['upstart']['config'][l] + "\n"
            else:
              output += str("").ljust(maxlen) + self.__deamons[k]['upstart']['config'][l] + "\n"
        if 'sysv' in self.show and self.__deamons[k].has_key('sysv'):
          s = str(k + ":").ljust(maxlen)
          for runlevel in ['rc0.d','rc1.d','rc2.d','rc3.d','rc4.d','rc5.d','rc6.d','rcS.d']:
            if self.__deamons[k]['sysv'].has_key(runlevel):
              s += str( runlevel[2] + ":on").ljust(7)
            else:
              s += str( runlevel[2] + ":    ").ljust(7)
          output += s + "\n"
      output = output.rstrip()

    self.__show = tmpShow
    return output

  def execute(self, deamon, command, arguments = [], sysv = None, upstart = None, output = "text", name=""):

    tmpShow = self.show
    if not sysv is None or not upstart is None:
      self.__toggle(sysv,upstart)

    count = 0
    for k in self.__filterList(self.deamonKeys, [deamon]):
      if 'upstart' in self.show and self.__deamons[k].has_key('upstart') and self.__deamons[k]['upstart'].has_key('config'):
        count += 1
        deamon = k
        show = 'upstart'
      if 'sysv' in self.show and self.__deamons[k].has_key('sysv'):
        count += 1
        deamon = k
        show = 'sysv'
    if count != 1:
      raise NameError('You must specify exactly 1 deamon (' + deamon + ') to execute the command (' + command + '). ' + str(count) + ' found!)') 

    if show == 'upstart':
      if not command in self.__upstartcommands:
        raise NameError('"' + command + '" is not a valid command for an upstart job!')       
      self.__debugPrint('Processing ' + command + ' command on upstart deamon', deamon)
      if not name: name = self.__deamons[deamon]['upstart']['deamon']
      cmdList = ['initctl', command, self.__deamons[deamon]['upstart']['deamon']]
    else:
      self.__debugPrint('Processing ' + command + ' command on SysV deamon', deamon)
      cmdList = ['/etc/init.d/' + self.__deamons[deamon]['sysv']['deamon'], command] + list(arguments)

    attrib = {}
    if not name: name = self.__deamons[deamon][show]['deamon']
    if output == 'pretty':
      name = self.__commands.get(command, 'Checking for ') + name + ' (' + str(show).title() + ') deamon '

    return getCommand(cmdList, output, name, attrib)


def getDiskSpace(output, name = "", separator = " ", warning = 80):
  """
  Retrieve information about the Mounted filesystems and return that in the format requested.
  """
  def rightSplit(s):
    tmp = str(s).rsplit(' ',1)
    if len(tmp) == 1:
      tmp.insert(0,'')
    return ( str(tmp[0]).strip(), str(tmp[1]).strip() )

  def humanReadable(n):
    n = int(n)
    for (multi,label) in ( (1.0, 'K'), (1024.0, 'M'), (1048576.0, 'G'), (1073741824.0, 'T'), (1099511627776.0, 'P'), (1125899906842624.0, 'E'), (1152921504606846976.0, 'Z') ):
      if n/multi < 1000:
        return str( "%1.1f" % (n/multi) ) + label
    return str( "%1.1f" % (n/1180591620717411303424.0) ) + 'Y'

  diskSpace = {}

  # Process df output
  p = subprocess.Popen(['df'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  out, err = p.communicate()
  rc = p.returncode

  # Process mount output
  p = subprocess.Popen(['mount'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  out2, err2 = p.communicate()
  rc2 = p.returncode

  tmp = []
  for line in str(out).split('\n')[1:]:
    if line:
      tmp.append([ str(s).strip() for s in str(line).split('%',1) ])

  # Correct df output wrap
  count = 0
  while ( count < len(tmp) ):
    if (len(tmp[count]) == 1) and ((count+1) < len(tmp)):
      tmp[count+1][0] = tmp[count][0] + " " + tmp[count+1][0]
      del tmp[count]
    count += 1

  for line in tmp:
    mount = line[1]
    line, percent = rightSplit(line[0])
    line, available = rightSplit(line)
    line, used = rightSplit(line)
    filesystem, size = rightSplit(line)
    diskSpace[mount] = {'filesystem':filesystem, 'size':size, 'used':used, 'available':available, 'percent':percent, 'warning':bool(int(percent)>=int(warning))}
    if int(percent) >= int(warning): rc = 1

  tmp = []
  for line in str(out2).split('\n'):
    if line and line[0] != '#' and ' on ' in line and ' type ' in line:
      device, line = [ str(s).strip() for s in str(line).split(' on ',1) ]
      mount, line = [ str(s).strip() for s in str(line).split(' type ',1) ]
      fstype, options = [ str(s).strip() for s in str(line).split(' ',1) ]
      options = str(options).strip("()")
      if diskSpace.has_key(mount):
        diskSpace[mount].update( {'fstype':fstype, 'options':options} )
  for key in diskSpace.keys():
    if not diskSpace[key].has_key('fstype'):
      diskSpace.update({'fstype':'', 'options':''})

    if output == "xml":
      if not name: name = "diskspace"      
      xml = ElementTree.Element('deamons')
      d = ElementTree.SubElement(xml, 'deamon', attrib={'name':str(name), 'returncode':str(rc)})
      for k in diskSpace.keys():
        attrib = { tmpKey: str(diskSpace[k][tmpKey]) for tmpKey in diskSpace[k].keys() }
        attrib.update( {"mount":k, 'sizeHuman':humanReadable(diskSpace[k]['size']), 'usedHuman':humanReadable(diskSpace[k]['used']), 'availableHuman':humanReadable(diskSpace[k]['available']) } )
        ElementTree.SubElement(d, 'filesystem', attrib=attrib)
      return rc, '<?xml version="1.0" encoding="' + encoding + '"?>\n' + ElementTree.tostring(xml, encoding=encoding, method="xml")
  else:
    width = {'filesystem':10, 'size':5, 'used':5, 'available':5, 'percent':4, 'mount':10, 'fstype':5, 'options':6}
    for k in diskSpace.keys():
      width['filesystem'] = max( width['filesystem'], len(diskSpace[k]['filesystem']) )
      width['mount'] = max( width['mount'], len(k) )
      width['size'] = max( width['size'], len( humanReadable(diskSpace[k]['size']))  )
      width['used'] = max( width['used'], len( humanReadable(diskSpace[k]['used'])) )
      width['available'] = max( width['available'], len( humanReadable(diskSpace[k]['available'])) )
      width['percent'] = max( width['percent'], len(diskSpace[k]['percent']) + 1 )
      if output == "text":
        width['fstype'] = max( width['fstype'], len(diskSpace[k]['fstype']) )
        width['options'] = max( width['options'], len(diskSpace[k]['options']) )

    tmp = [ "Filesystem".ljust(width['filesystem']) ]
    tmp.append( "Size".rjust(width['size']) )
    tmp.append( "Used".rjust(width['used']) )
    tmp.append( "Avail".rjust(width['available']) )
    tmp.append( "Use".rjust(width['percent']) )
    tmp.append( "Mounted".ljust(width['mount']) )
    if output == "text":
      tmp.append( "FSType".center(width['fstype']) )
      tmp.append( "Options".center(width['options']) )
    outputList = [ str(separator).join(tmp) ]
    for k in sorted( diskSpace.keys() ):
      tmp = [ diskSpace[k]['filesystem'].ljust(width['filesystem']) ]
      tmp.append( humanReadable(diskSpace[k]['size']).rjust(width['size']) )
      tmp.append( humanReadable(diskSpace[k]['used']).rjust(width['used']) )
      tmp.append( humanReadable(diskSpace[k]['available']).rjust(width['available']) )
      tmp.append( str(diskSpace[k]['percent']+"%").rjust(width['percent']) )
      tmp.append( k.ljust(width['mount']) )
      red = norm = ""
      if output == "text":
        tmp.append( diskSpace[k]['fstype'].rjust(width['fstype']) )
        tmp.append( diskSpace[k]['options'].ljust(width['options']) )
      elif diskSpace[k]['warning']:
        red = "\033[1;91m"
        norm = "\033[m\017"
      outputList.append( red + str(separator).join(tmp) + norm )
    return rc, '\n'.join(outputList)

def getPreamble(output, name = ""):
  # Process top output
  p = subprocess.Popen(['top', '-n', '1'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  out, err = p.communicate()
  rc = int(bool( not err == "" ))

  # Remove ANSI format characters
  out = out.split("\n")[:5]
  ansi_escape = re.compile(r'\x1b[^m]*[mK]')
  out = [ ansi_escape.sub('', line) for line in out ]
  preamble = re.compile(r'^\D*')
  out[0] = preamble.sub('', out[0])
  out = "\n".join(out)

  if output == "xml":
    if not name: name = "preamble"
    xml = ElementTree.Element('deamons')
    d = ElementTree.SubElement(xml, 'deamon', attrib={'name':str(name), 'returncode':str(rc)})
    o =  ElementTree.SubElement(d, 'output')
    o.text = out
    if err:
      e =  ElementTree.SubElement(d, 'error')
      e.text = err
    return rc, '<?xml version="1.0" encoding="' + encoding + '"?>\n' + ElementTree.tostring(xml, encoding=encoding, method="xml")
  else:
    if err: out = out + '\n' + err
    return rc, out


# Start program
if __name__ == "__main__":
  command_line_args()
  if args['autocomplete']: autocomplete(deamons, args['arguments'])
  if args['setup']: setup()

  if args['diskspace']:
    if args['arguments']:
      args['arguments'] = int(args['arguments'][0])
    else:
      args['arguments'] = 80
    rc, output = getDiskSpace(output = args['output'], name = args['name'], separator = " ", warning = args['arguments'])
    print output
    exit(rc)

  if args['preamble']:
    rc, output = getPreamble(output = args['output'], name = args['name'])
    print output
    exit(rc)

  if args['command']:
    rc, output = getCommand(args['arguments'],args['output'])
    print output
    exit(rc)

  deamonFilter = "*"
  command = "status"
  arguments = []
  if len(args['arguments']) > 0: deamonFilter = args['arguments'][0]
  if len(args['arguments']) > 1: 
    command = args['arguments'][1]
    arguments = args['arguments'][2:]
  if args['status_all']: 
    command = "status"
    args['name'] = ""

  deamon = deamonClass(filters=[deamonFilter], sysv=args['sysv'], upstart=args['upstart'], debug = args['debug'], xmlEncoding = encoding)
  deamon.load()

  if args['list']:
    print deamon.list(output=args["output"])
    exit()

  totalRC = 0

  attrib = {'host':os.uname()[1], 'date':datetime.datetime.strftime(datetime.datetime.now(),'%Y%m%d%H%M%S')} 
  xmlNew = ElementTree.Element('deamons', attrib = attrib)
  for d in deamon.deamonKeys:
    upstart = deamon.deamons[d].has_key('upstart')
    sysv = deamon.deamons[d].has_key('sysv')
    if upstart and sysv: sysv = False
    rc, output = deamon.execute(d, command, arguments, upstart=upstart, sysv=sysv, output=args["output"], name=args["name"])
    totalRC = totalRC | rc
    if args["output"] == "xml":
      for child in ElementTree.fromstring(output):
        if child.tag == "deamon": xmlNew.append(child)
    else:
      print output

  if args["output"] == "xml":
    print '<?xml version="1.0" encoding="' + encoding + '"?>'
    print ElementTree.tostring(xmlNew, encoding=encoding, method="xml")

  exit(totalRC)
