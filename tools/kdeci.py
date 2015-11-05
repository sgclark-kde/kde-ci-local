#
# <one line to give the library's name and an idea of what it does.>
# Copyright 2015  <copyright holder> <email>
# 
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of
# the License or (at your option) version 3 or any later version
# accepted by the membership of KDE e.V. (or its successor approved
# by the membership of KDE e.V.), which shall act as a proxy
# defined in Section 14 of version 3 of the license.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
# 
#
# Python library to help manage and run the KDE Continuous Integration system
import re
import os
import sys
import time
import copy
import ConfigParser
import json
import shlex
import shutil
import argparse
import subprocess
from distutils import dir_util
from collections import defaultdict
from os.path import expanduser
import urllib2
from pprint import pprint
import socket

# Settings
hostname = socket.gethostname()

def localAwareJoin(local, *p):
    if local:
        return os.path.join(*p)
    else:
        return "/".join(p)

def makeRelativeLocation(path):
    if sys.platform == "win32":
        return path[3:]
    else:
        return path[1:]

class ProjectManager(object):
    # Projects which we know, keyed by their identifier
    _projects = {}
    # Regex for the dependency rules
    _dependencyRuleRe = re.compile(r"""
        (?P<project>[^\[]+)
        \s*
        (?:
            \[
                (?P<project_branch>[^ ]+)
            \]
        )?
        \s*
        :
        \s*
        (?P<ignore_dependency>-)?
        (?P<dependency>[^\[]+)
        \s*
        (:?
            \[
                (?P<dependency_branch>[^ ]+)
            \]
        )?
        """,re.X)

    # Sets up a project from a configuration file
    @staticmethod
    def load_extra_project( projectFilename ):
        # Read the project configuration
        projectData = ConfigParser.SafeConfigParser()
        projectData.read( projectFilename )

        # Determine if we already know a project by this name (ie. override rather than create)
        identifier = projectData.get('Project', 'identifier')
        project = ProjectManager.lookup( identifier )
        if project is None:
            project = Project()
            project.identifier = identifier
            ProjectManager._projects[ project.identifier ] = project

        # Are we overriding the path?
        if projectData.has_option('Project', 'path'):
            project.path = projectData.get('Project', 'path')

        # Are we overriding the url?
        if projectData.has_option('Project', 'url'):
            project.url = projectData.get('Project', 'url')

        # Are we changing the general dependency state?
        if projectData.has_option('Project', 'sharedDependency'):
            project.sharedDependency = projectData.getboolean('Project', 'sharedDependency')

        # Are we registering any branch group associations?
        if projectData.has_section('BranchGroups'):
            for symName in projectData.options('BranchGroups'):
                project.branchGroups[ symName ] = projectData.get('SymbolicBranches', symName)

    # Load the kde_projects.xml data in
    @staticmethod
    def load_projects( object ):
        # Get a list of all repositories, then create projects for them
        data_file = json.loads(open('kde_projects.json').read()) 
        for x in data_file:
            repoData = (x['repositories'])
            for repos in repoData:
                pprint( repos )
                projectData = repos.getParent()
                pprint( projectData )
            # Create the new project and set the bare essentials
            project = Project()
            project.identifier = projectData.get('identifier')
            project.path = projectData.find('path').text
            project.url = repoData.find('url[@protocol="git"]').text

            # What branches has this project got?
            for branchItem in repoData.iterfind('branch'):
                # Maybe this branch is invalid?
                if branchItem.text is None or branchItem.text == 'none':
                    continue

                # Must be a normal branch then
                project.branches.append( branchItem.text )

            # Register this project now - all setup is completed
            ProjectManager._projects[ project.identifier ] = project

    # Load in information concerning project branch groups
    @staticmethod
    def setup_branch_groups( moduleStructure ):
        # Let's go over the given groups and categorise them appropriately
        for entry, groups in moduleStructure['groups'].items():
            # If it is dynamic, then store it away appropriately
            if entry[-1] == '*':
                Project.wildcardBranchGroups[entry] = groups
                continue

            # If it isn't dynamic, then find out the project it belongs to
            project = ProjectManager.lookup( entry )
            if project != None:
                project.branchGroups = groups

    # Setup ignored project metadata
    @staticmethod
    def setup_ignored( ignoreData ):
        # First, remove any empty lines as well as comments
        ignoreList = [ project.strip() for project in ignoreData if project.find("#") == -1 and project.strip() ]
        # Now mark any listed project as ignored
        for entry in ignoreList:
            project = ProjectManager.lookup( entry )
            project.ignore = True

    # Setup the dependencies from kde-projects.json
    @staticmethod
    def setup_dependencies( depData ):
        for depEntry in depData:
            # Cleanup the dependency entry and remove any comments
            commentPos = depEntry.find("#")
            if commentPos >= 0:
                depEntry = depEntry[0:commentPos]

            # Prepare to extract the data and skip if the extraction fails
            match = ProjectManager._dependencyRuleRe.search( depEntry.strip() )
            if not match:
                continue

            # Determine which project is being assigned the dependency
            projectName = match.group('project').lower()
            project = ProjectManager.lookup( projectName )
            # Validate it (if the project lookup failed and it is not dynamic, then it is a virtual dependency)
            if project == None and projectName[-1] != '*':
                # Create the virtual dependency
                project = Project()
                project.path = projectName
                project.virtualDependency = True
                # Generate an identifier for it
                splitted = projectName.split('/')
                project.identifier = splitted[-1]
                # Now register it - we can continue normally after this
                ProjectManager._projects[ project.identifier ] = project

            # Ensure we know the dependency - if it is marked as "ignore" then we skip this
            dependencyName = match.group('dependency').lower()
            dependency = ProjectManager.lookup( dependencyName )
            if dependency == None or dependency.ignore:
                continue

            # Are any branches specified for the project or dependency?
            projectBranch = dependencyBranch = '*'
            if match.group('project_branch'):
                projectBranch = match.group('project_branch')
            if match.group('dependency_branch'):
                dependencyBranch = match.group('dependency_branch')

            # Is this a dynamic project?
            if projectName[-1] == '*':
                dependencyEntry = ( projectName, projectBranch, dependency, dependencyBranch )
                # Is it negated or not?
                if match.group('ignore_dependency'):
                    Project.dynamicNegatedDeps.append( dependencyEntry )
                else:
                    Project.dynamicDependencies.append( dependencyEntry )
            # Otherwise it must be a project specific rule
            else:
                dependencyEntry = ( dependency, dependencyBranch )
                # Is it negated or not?
                if match.group('ignore_dependency'):
                    project.negatedDeps[ projectBranch ].append( dependencyEntry )
                else:
                    project.dependencies[ projectBranch ].append( dependencyEntry )

    # Lookup the given project name
    @staticmethod
    def lookup( projectName ):
        # We may have been passed a path, reduce it down to a identifier
        splitted = projectName.split('/')
        identifier = splitted[-1]
        # Now we try to return the desired project
        try:
            return ProjectManager._projects[identifier]
        except Exception:
            return

def check_jenkins_environment():
    # Prepare
    arguments = argparse.Namespace()
    print os.environ
    # Do we have a job name?
    if 'JOB_NAME' in os.environ:
        # Split it out
        jobMatch = re.match("(?P<project>[^\s]+)\s?(?P<branch>[^\s]+)\s?(?P<branchGroup>[^//]+)?", os.environ['JOB_NAME'])
        # Now transfer in any non-None attributes
        # If we have the project name, transfer it
        if jobMatch.group('project') is not None:
            arguments.project = jobMatch.group('project')
            # Determine our branch group, based on the given branch/base combo
            arguments.branchGroup = jobMatch.group('branchGroup')             
            arguments.branch = jobMatch.group('branch')
            
#     if 'PLATFORM' in os.environ:
#         arguments.platform = os.environ('PLATFORM')
#             
#     if 'compiler' in os.environ:
#         arguments.compiler = os.environ('compiler')
           
    # Do we have a workspace?
    if 'WORKSPACE' in os.environ:
        arguments.sources = os.environ['WORKSPACE']

    # Do we have a build variation?
    if 'Variation' in os.environ:
        # We need this to determine our specific build variation
        arguments.variation = os.environ['Variation']
    
    # Do we need to change into the proper working directory?
    if 'JENKINS_SLAVE_HOME' in os.environ: 
        os.chdir( os.environ['JENKINS_SLAVE_HOME'] ) 
    else: 
        os.chdir( expanduser("~") + "/scripts/" ) 
        
    print arguments
    return arguments    

def load_project_configuration( project, branchGroup, platform, compiler, variation = None ):
    # Create a configuration parser
    config = ConfigParser.SafeConfigParser()
    # List of prospective files to parse
    configFiles =  ['global.cfg', '{compiler}.cfg', '{platform}.cfg', '{branchGroup}.cfg', '{host}.cfg']
    configFiles += ['{branchGroup}-{platform}.cfg']
    configFiles += ['{project}/project.cfg', '{project}/{platform}.cfg', '{project}/{variation}.cfg', '{project}/{branchGroup}.cfg']
    configFiles += ['{project}/{branchGroup}-{platform}.cfg', '{project}/{branchGroup}-{variation}.cfg']
    # Go over the list and load in what we can
    for confFile in configFiles:
        confFile = confFile.format( host=socket.gethostname(), branchGroup=branchGroup, compiler=compiler, platform=platform, project=project, variation=variation )
        config.read( 'config/build/' + confFile )        
        # All done, return the configuration        
        return config
        
def load_all_projects( projectFile, configDirectory ):
    data_file = json.loads(open(projectFile).read()) 
    # Now load the list of projects into the project manager    
    try:
        ProjectManager.load_projects( data_file )
    except:          
        return False
    
    # Now load the list of projects into the project manager
    with open(projectFile, 'r') as fileHandle:
        try:
            ProjectManager.load_projects( json.load(fileHandle) )
        except:            
            return False

    # Load the branch group data now
    with open(projectFile, 'r') as fileHandle:
        ProjectManager.setup_branch_groups( json.load(fileHandle) )

    # Finally, load special projects
    for dirname, dirnames, filenames in os.walk( configDirectory ):
        for filename in filenames:
            filePath = os.path.join( dirname, filename )
            ProjectManager.load_extra_project( filePath )

    # We are successful
    return True

