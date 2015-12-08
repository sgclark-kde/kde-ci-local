package helper;

public class GeneratePublishers {
	def FlexiblePublish(create, compiler) {
		if(create) {
			switch(compiler) {
				case 'gcc':
					return { project ->
					// Linux compiler warnings (gcc)
						project / publishers << 'org.jenkins__ci.plugins.flexible__publish.FlexiblePublisher' {
							publishers {
								'org.jenkins__ci.plugins.flexible__publish.ConditionalPublisher' {
									condition(class: 'org.jenkins_ci.plugins.run_condition.core.StringsMatchCondition') {
										arg1 '${ENV,var="compiler"}'
										arg2 'gcc'
										ignoreCase false
									}
									publisherList {
										'hudson.plugins.warnings.WarningsPublisher' {
											canRunOnFailed false
											usePreviousBuildAsReference false
											useStableBuildAsReference false
											useDeltaValues false
											shouldDetectModules false
											dontComputeNew true
											doNotResolveRelativePaths true
											parserConfigurations {}
											consoleParsers {
												'hudson.plugins.warnings.ConsoleParser' {
													parserName 'Missing Dependencies'
												}
												'hudson.plugins.warnings.ConsoleParser' {
													parserName 'GNU C Compiler 4 (gcc)'
												}
											}
										}
									}
									runner(class: "org.jenkins_ci.plugins.run_condition.BuildStepRunner\$Fail")
								}
							}
						}
					}
					break
				case 'clang':
					return { project ->
						project / publishers << 'org.jenkins__ci.plugins.flexible__publish.FlexiblePublisher' {
							publishers {
								'org.jenkins__ci.plugins.flexible__publish.ConditionalPublisher' {
									condition(class: 'org.jenkins_ci.plugins.run_condition.core.StringsMatchCondition') {
										arg1 '${ENV,var="compiler"}'
										arg2 'clang'
										ignoreCase false
									}
									publisherList {
										'hudson.plugins.warnings.WarningsPublisher' {
											canRunOnFailed false
											usePreviousBuildAsReference false
											useStableBuildAsReference false
											useDeltaValues false
											shouldDetectModules false
											dontComputeNew true
											doNotResolveRelativePaths true
											parserConfigurations {}
											consoleParsers {
												'hudson.plugins.warnings.ConsoleParser' {
													parserName 'Missing Dependencies'
												}
												'hudson.plugins.warnings.ConsoleParser' {
													parserName 'Clang (LLVM based)'
												}
											}
										}
									}
									runner(class: "org.jenkins_ci.plugins.run_condition.BuildStepRunner\$Fail")
								}
							}
						}
					}
			}
		}
		}
}