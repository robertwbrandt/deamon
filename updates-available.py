#!/usr/bin/env python2.7
"""
Script to find the updates available for a system
"""
import argparse, textwrap, platform, json
import fnmatch, subprocess, re, datetime
import xml.etree.ElementTree as ElementTree

# Import Brandt Common Utilities
import sys, os
sys.path.append( os.path.realpath( os.path.join( os.path.dirname(__file__), "/opt/brandt/common" ) ) )
import brandt
sys.path.pop()

args = {}
args['output'] = 'text'
args['target'] = []
args['delimiter'] = ""
version = 0.3
encoding = 'utf-8'



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
			print "Usage: " + self.__prog + " [options]"
			print "Script to find the updates available for a system.\n"
			print "Options:"
			options = []
			options.append(("-h, --help",            "Show this help message and exit"))
			options.append(("-v, --version",         "Show program's version number and exit"))
			options.append(("-o, --output OUTPUT",   "Type of output {text | csv | xml | json}"))
			options.append(("-d, --delimiter DELIM", "Character to use instead of TAB for field delimiter"))      
			length = max( [ len(option[0]) for option in options ] )
			for option in options:
				description = textwrap.wrap(option[1], (self.__row - length - 5))
				print "  " + option[0].ljust(length) + "   " + description[0]
			for n in range(1,len(description)): print " " * (length + 5) + description[n]
		exit(self.__exit)
def command_line_args():
	global args, version
	parser = argparse.ArgumentParser(add_help=False)
	parser.add_argument('-v', '--version', action=customUsageVersion, version=version, max=80)
	parser.add_argument('-h', '--help', action=customUsageVersion)
	parser.add_argument('-d', '--delimiter',
					required=False,
					default=args['delimiter'],
					type=str,
					help="Character to use instead of TAB for field delimiter")
	parser.add_argument('-o', '--output',
					required=False,
					default=args['output'],
					choices=['text', 'csv', 'xml', 'json'],
					help="Display output type.")
	args.update(vars(parser.parse_args()))
	if args['delimiter']: args['delimiter'] = args['delimiter'][0]
	if not args['delimiter'] and args['output'] == "csv": args['delimiter'] = ","

def get_ubuntu_data():
	global args
	command = 'apt-get update'
	p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

	command = '/usr/lib/update-notifier/apt-check'
	p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
	out,err = p.communicate()
	out = out.strip().split(";") + ['0','0']
	return {"total":out[0], "security":out[1]}

# Start program
if __name__ == "__main__":
	try:
		output = ""
		error = ""
		xmldata = ""
		exitcode = 0
		
		command_line_args()
		
		updates = {"total":0, "security":0}
		if platform.system() == 'Linux':
			try:
				distro = platform.linux_distribution()
			except AttributeError:
				distro = platform.dist()
			except:
				distro = ('Unknown','Unknown','Unknown')

			try:
				if distro[0] in ['Ubuntu','Debian']:
					updates = get_ubuntu_data()
			except:
				pass

	except SystemExit as err:
		pass
	except Exception as err:
		try:
			exitcode = int(err[0])
			errmsg = str(" ".join(err[1:]))
		except:
			exitcode = -1
			errmsg = str(err)

		if args['output'] != 'xml': 
			error = "(" + str(exitcode) + ") " + str(errmsg) + "\nCommand: " + " ".join(sys.argv)
		else:
			xmldata = ElementTree.Element('error', code=brandt.strXML(exitcode), 
																						 msg=brandt.strXML(errmsg), 
																						 cmd=brandt.strXML(" ".join(sys.argv)))
	finally:
		if args['output'] == 'xml':
			xml = ElementTree.Element('updates-available', **updates)
			if xmldata: xml.append(xmldata)
			print '<?xml version="1.0" encoding="' + encoding + '"?>\n' + ElementTree.tostring(xml, encoding=encoding, method="xml")
		else:
			if error:
				sys.stderr.write( str(error) + "\n" )

			elif args['output'] == 'text':
				print updates['total'], 'packages can be updated.'
				print updates['security'], 'updates are security updates.'
			elif args['output'] == 'csv':
				print args['delimiter'].join(["Security","Total"])
				print args['delimiter'].join([updates['security'], updates['total']])
			elif args['output'] == 'json':
				print json.dumps(updates, sort_keys=True, indent=2)

		sys.exit(exitcode)
