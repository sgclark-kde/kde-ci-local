/**
 * 
 */
package helper

/**
 * @author Scarlett Clark
 *
 */
import static groovy.json.JsonOutput.*
import groovy.lang.Closure;
import java.util.ArrayList;
import org.jenkinsci.*

class Platform {
	static Map PlatformToCompiler = [:]
	static Map RepoData = [:]
	String protocol
	static List platformCompilers = []
	static List platformsToBuild = []
	String platform	
	boolean build
	String shell
	Closure build_step
	String compilers
	String platform_email
	String platform_irc
	static Map branch
	String currbranch
	String address
	ArrayList tracks
	String path
	String tarname
	boolean showbrowser
	Map combinations
	ArrayList Variation
	ArrayList VariationLinux
	ArrayList VariationWindows
	ArrayList VariationOSX
	ArrayList VariationAndroid
	ArrayList VariationUbuntuP
		
	Platform() {		
	}	
	Platform(String platform, boolean build, String compilers, String platform_email, String platform_irc, \
		Map repositories, ArrayList tracks, ArrayList VariationLinux, ArrayList VariationWindows, ArrayList VariationOSX, \
		ArrayList VariationAndroid, ArrayList VariationUbuntuP) {
		this.platform = platform
		this.build = build
		this.compilers = compilers
		this.platform_email	= platform_email
		this.platform_irc = platform_irc		
		this.tracks = tracks		
		this.Variation = Variation
		this.VariationLinux = VariationLinux
		this.VariationWindows = VariationWindows
		this.VariationOSX = VariationOSX
		this.VariationAndroid = VariationAndroid
		this.VariationUbuntuP = VariationUbuntuP
		this.RepoData = [:] << repositories
		this.RepoData.each { path ->			
			this.path = path.key			
			this.RepoData = [:] << path.value
			this.branch = [:] << RepoData.getAt("branch")
			this.showbrowser = RepoData.showwebgit.value
			this.RepoData.protocol.each { protocolinfo ->
				this.address = protocolinfo.value.getAt("address")
				this.protocol = protocolinfo.key
			}
		}	
	}
	def addPlatform(String key, String compiler, String track) {			
		if(this.build != false && this.tracks.contains(track)) {			
			this.platformsToBuild << key
			this.platformCompilers << compiler				
		}
		this.PlatformToCompiler << ["${key}" : ' ' + compiler]
		
	}
	def newTrack()	{		
		platformCompilers = []		
		platformsToBuild = []	
		PlatformToCompiler = [:]		
	} 
	def newCombinations(String platform, String compiler) {
		this.combinations = [
			    { 'PLATFORM:' platform, 'compiler:' compiler }				
		]
	}
	def initialPlatformBlock(PlatformToCompiler) {
		def home
		return { project ->
			project.name = 'matrix-project'
			this.platformsToBuild.each { platform ->				
				if (platform == "windows") {
					this.shell = 'BatchFile'
					home = "D:\\kderoot"
				} else if (platform == "osx") {					
					home = "/Users/jenkins/"
					this.shell = 'Shell'
				} else {
					home = "/home/jenkins/"
					this.shell = 'Shell'
				}
				def compiler = PlatformToCompiler.find { key, value -> key == platform }
				
				project / builders <<
				'org.jenkinsci.plugins.conditionalbuildstep.singlestep.SingleConditionalBuilder' {
					condition(class: 'org.jenkins_ci.plugins.run_condition.core.StringsMatchCondition') {
						arg1 '${ENV,var="PLATFORM"}'
						arg2 platform
						ignoreCase false
					}
					runner(class: "org.jenkins_ci.plugins.run_condition.BuildStepRunner\$Fail")
					buildStep(class: 'hudson.tasks.' + "${this.shell}") {
						command "python ${home}/scripts/tools/update-setup-sandbox.py \n" + \
								"python ${home}/scripts/tools/prepare-environment.py" + \
								' --platform ' + platform + ' --compiler ' + compiler.value
					}
				}
			}
		}
		
	}
	def GenerateSCM(jobname, currbranch) {
				
			switch(this.protocol) {
				case 'svn':
					return { project ->
						project / scm(class: 'hudson.scm.SubversionSCM') {
							locations {
								'hudson.scm.SubversionSCM_-ModuleLocation' {
									remote this.address
									local '.'
								}
							}
							excludedRegions ''
							includedRegions ''
							excludedUsers ''
							excludedRevprop ''
							excludedCommitMessages ''
							workspaceUpdater(class: "hudson.scm.subversion.UpdateUpdater")	
						}				
					}
					break
				case 'git':
					return { project ->
						project.name = 'matrix-project'
						project / scm(class: 'hudson.plugins.git.GitSCM') {
							userRemoteConfigs {
								'hudson.plugins.git.UserRemoteConfig' {
									url this.address
								}
							}
							relativeTargetDir '${WORKSPACE}'
							branches {
								'hudson.plugins.git.BranchSpec' {
									name currbranch
								}
							}
							if (showbrowser)	{
								browser(class: 'hudson.plugins.git.browser.GitWeb') {
									url 'https://quickgit.kde.org/?p=' + jobname + '.git'
								}
							}
							extensions {
								'hudson.plugins.git.extensions.impl.CloneOption' {
									shallow false
									timeout '20'
								}
							}
						}
					}
					break
				case 'lp':
					return { project ->
						project.name = 'matrix-project'
						project / scm(class: 'hudson.plugins.bazaar.BazaarSCM') {
							source this.address
							cleantree false
							checkout true
							}
						}
					break
				case 'hg': 
					return { project ->
						project.name = 'matrix-project'
						project / scm(class: 'hudson.plugins.mercurial.MercurialSCM') {
							source this.address
							modules ''
							revisionType BRANCH
							revision 'default'
							credentialsId ''
							clean true
							disableChangeLog false
						}
					}
					break
				case 'tar':
					return { project ->
						project.name = 'matrix-project'
						buildStep(class: 'hudson.tasks.' + "${this.shell}") {
								"wget " + this.address + " \n" \
								+ "tar --strip-components=1 -xf" + this.tarname + "\n" \
								+ "rm " + this.tarname
						}
					}
				default:			
					return { project ->
						project.name = 'matrix-project'
						project / scm(class: 'hudson.plugins.git.GitSCM') {
							userRemoteConfigs {
								'hudson.plugins.git.UserRemoteConfig' {
									url this.address
								}
							}
							relativeTargetDir '${WORKSPACE}'
							branches {
								'hudson.plugins.git.BranchSpec' {
									name currbranch
								}
							}					
							extensions {
								'hudson.plugins.git.extensions.impl.CloneOption' {
									shallow false
									timeout '20'
								}
							}
						}
					}
					break
				}
			}		
	
	def BuildTriggers(repo, track, jobname) {
		
		def tokenid =  "PNcTKQORJW653QKVTwL0GV64OZA-${jobname}"
		if(token) {
			return { project ->
				project << authToken( "${tokenid}")
				scm('')
			}
		} else {
			return scm('weekly')
		}			
	}
}
