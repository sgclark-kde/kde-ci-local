#!/usr/bin/python

import sys
import time
import argparse
from kdeci import *

# Load our command line arguments
parser = argparse.ArgumentParser(description='Utility to initialize a git repository before hand over to the build executor.')
parser.add_argument('--project', type=str)
parser.add_argument('--branchGroup', type=str, default='kf5-qt5')
parser.add_argument('--sources', type=str)
parser.add_argument('--delay', type=int, default=10)
parser.add_argument('--platform', type=str, required=True, choices=['ubuntu', 'osx', 'windows', 'android', 'ubuntu-phone'], default='ubuntu')
parser.add_argument('--compiler', type=str, required=True, choices=['gcc', 'clang', 'vs2013', 'android-sdk', 'ubuntu-sdk'], default='gcc')

# Parse the arguments
environmentArgs = check_jenkins_environment()
print environmentArgs
arguments = parser.parse_args( namespace=environmentArgs )

# Load the various configuration files, and the projects
config = load_project_configuration( arguments.project, arguments.branchGroup, arguments.platform, arguments.compiler )
print arguments.project 
print arguments.branchGroup
print arguments.platform
print arguments.compiler
if not load_all_projects( 'metadata/kde_projects.json', 'config/projects'):
	sys.exit("Failure to load projects - unable to continue")

# # Load the requested project
# project = ProjectManager.lookup( arguments.project )
# if project is None:
# 	sys.exit("Requested project %s was not found." % arguments.project)
# 
# # First we must wait for the anongit mirrors to settle
# time.sleep( arguments.delay )
# 
# # Prepare the sources and handover to Jenkins
# manager = BuildManager(project, arguments.branchGroup, arguments.sources, config, arguments.platform)
# 
# print "\nPreparing to perform KDE Continuous Integration build"
# print "== Setting Up Sources\n"
# manager.checkout_sources()
# 
# print "\n== Cleaning Source Tree\n"
# manager.cleanup_sources()
