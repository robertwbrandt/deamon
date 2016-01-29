#!/usr/bin/env python
"""
Script for a user friendly dashboard showing all necessary deamons and stats
"""
import argparse, textwrap
import fnmatch, subprocess, re
import xml.etree.ElementTree as ElementTree

# Import Brandt Common Utilities
import sys, os
sys.path.append( os.path.realpath( os.path.join( os.path.dirname(__file__), "/opt/brandt/common" ) ) )
import brandt
sys.path.pop()

version = 0.3
args = {}
args['setup'] = False
args['xml'] = False
args['config'] = "/etc/brandt/dashboard.conf"

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
      print "Usage: " + self.__prog + " [-x] [-c CONFIG]"
      print "\nUser friendly dashboard showing all necessary deamons and stats\n"
      print "Options:"
      options = []
      options.append(("-h, --help",           "Show this help message and exit"))
      options.append(("-v, --version",        "Show program's version number and exit"))
      options.append(("-x, --xml",            "Display output in XML"))
      options.append(("-c, --config CONFIG",  "Use the given CONFIG file rather then the default"))
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
  parser.add_argument('--setup',
                    required=False,
                    action='store_true')    
  parser.add_argument('-x', '--xml',
                    required=False,
                    action='store_true')
  parser.add_argument('-c', '--config',
                    required=False,
                    default=args['config'],
                    action='store',
                    type=str)
  args.update(vars(parser.parse_args()))

def setup():
  global args 
  if os.geteuid() != 0:
    exit("You need to have root privileges to setup this script.\nPlease try again, this time using 'sudo'.\nExiting.")

  # Create Symbolic link at /usr/local/bin
  src = os.path.realpath( __file__ )
  dst = os.path.join( '/usr/local/bin', os.path.splitext(os.path.basename(__file__))[0] )
  os.symlink(src, dst)

  if not os.path.isfile(args['config']):
    f = open(args['config'], "w")
    f.write( """
#     Configuration file for the Brandt Dashboard script"
#     Bob Brandt <projects@brandt.ie>
#
###############################################################################
# {first|
#  present|
#  last},   name,                    present,               status command
first,      Uptime,                  /usr/bin/top,          deamon -p
present,    Network,                 /etc/init.d/network,   deamon -s network status
present,    Network Time Protocol,   /etc/init.d/ntp,       deamon -s ntp status
last,       Disk Usage,              /bin/df,               deamon -d 84
###############################################################################
""")
  f.close()
  exit()


def runCommands(commands):
  global args   
  for line in commands:
    name, present, cmd = line[1], line[2], str(line[3]).split(" ")

    if cmd[0] == "deamon":
      del cmd[0]
      cmd = ["--name",name] + cmd
      if ("-o" not in cmd) and ("--output" not in cmd):
        if args['xml']:
          cmd = ["--output","xml"] + cmd
        else:
          cmd = ["--output","pretty"] + cmd        
      cmd = ["deamon"] + cmd

    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out,err = p.communicate()
    rc = p.returncode
    print str(out).strip()

# Start program
if __name__ == "__main__":
  command_line_args()
  if args['setup']: setup()

  config =[]
  f = open(args['config'], "r")
  for line in f.read().split('\n'):
    if line and str(line)[0] not in ["#",";"," ","\t"]:        
      config.append( [ l.strip() for l in line.split(",") ] )
  f.close()

  xml = ""
  # Run FIRST lines first
  tmp = runCommands( [ l for l in config if l[0] == "first" ] )

  # Run non FIRST or LAST lines
  tmp = runCommands( [ l for l in config if l[0] not in ["first","last"] ] )

  # Run LAST lines last
  tmp = runCommands( [ l for l in config if l[0] == "last" ] )

