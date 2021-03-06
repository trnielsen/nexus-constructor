@Library('ecdc-pipeline')
import ecdcpipeline.ContainerBuildNode
import ecdcpipeline.PipelineBuilder

project = "nexus-constructor"

// Set number of old artefacts to keep.
properties([
    buildDiscarder(
        logRotator(
            artifactDaysToKeepStr: '',
            artifactNumToKeepStr: '5',
            daysToKeepStr: '',
            numToKeepStr: ''
        )
    )
])

container_build_nodes = [
  'centos7': ContainerBuildNode.getDefaultContainerBuildNode('centos7')
]

pipeline_builder = new PipelineBuilder(this, container_build_nodes)

builders = pipeline_builder.createBuilders { container ->
    
    pipeline_builder.stage("Checkout") {
        dir(pipeline_builder.project) {
            scm_vars = checkout scm
        }
        // Copy source code to container
        container.copyTo(pipeline_builder.project, pipeline_builder.project)
    }  // stage
    
    pipeline_builder.stage("Create virtualenv") {
        container.sh """
            cd ${project}
            python3.6 -m venv build_env
        """
    } // stage
    
    pipeline_builder.stage("Install requirements") {
        container.sh """
            cd ${project}
            build_env/bin/pip --proxy ${https_proxy} install --upgrade pip
            build_env/bin/pip --proxy ${https_proxy} install -r requirements-dev.txt
            git submodule update --init
            """
    } // stage
    
    pipeline_builder.stage("Check formatting") {
        container.sh """
            cd ${project}
            build_env/bin/python -m black . --check
        """
    } // stage
    
    pipeline_builder.stage("Run Linter") {
        container.sh """
                cd ${project}
                build_env/bin/flake8
            """
    } // stage
    
    pipeline_builder.stage("Run tests") {
        def testsError = null
        try {
                container.sh """
                    cd ${project}
                    build_env/bin/python -m pytest -s ./tests --ignore=build_env --ignore=tests/ui_tests
                """
            }
            catch(err) {
                testsError = err
                currentBuild.result = 'FAILURE'
            }

    } // stage
    
    if (env.CHANGE_ID) {
        pipeline_builder.stage('Build Executable'){
            container.sh "cd ${project} && build_env/bin/python setup.py build_exe"
        }
        
        pipeline_builder.stage('Archive Executable') {
            def git_commit_short = scm_vars.GIT_COMMIT.take(7)
            container.copyFrom("${project}/build/", './build')
            sh "tar czvf nexus-constructor_linux_${git_commit_short}.tar.gz ./build "
            archiveArtifacts artifacts: 'nexus-constructor*.tar.gz', fingerprint: true
        } // stage
    } // if
    
}

def get_win10_pipeline() {
return {
    node('windows10') {
      // Use custom location to avoid Win32 path length issues
      ws('c:\\jenkins\\') {
          cleanWs()
          dir("${project}") {
            stage("Checkout") {
              scm_vars = checkout scm
            }  // stage
            stage("Setup") {
                  bat """
                  git submodule update --init
                  python -m pip install --upgrade virtualenv
                  python -m pip install --user -r requirements-dev.txt
                  python -m pip install codecov==2.0.15
                """
            } // stage
            stage("Run tests") {
                bat """
                set PYTEST_QT_API=pyside2
                python -m pytest . -s --ignore=definitions --assert=plain --cov=nexus_constructor --cov-report=xml --junit-xml=test_results.xml
                """

        withCredentials([string(credentialsId: 'nexus-constructor-codecov-token', variable: 'TOKEN')]) {
            bat """
                codecov -t ${TOKEN} -c ${scm_vars.GIT_COMMIT} -f coverage.xml
                """
        }
                junit "test_results.xml"
            } // stage
            if (env.CHANGE_ID) {
                stage("Build Executable") {
                    bat """
                    python setup.py build_exe"""
                } // stage
                stage('Archive Executable') {
                    def git_commit_short = scm_vars.GIT_COMMIT.take(7)
                    powershell label: 'Archiving build folder', script: "Compress-Archive -Path .\\build -DestinationPath nexus-constructor_windows_${git_commit_short}.zip"
                    archiveArtifacts 'nexus-constructor*.zip'
                } // stage
                stage("Test executable") {
                    timeout(time:15, unit:'SECONDS') {
                        bat """
                        cd build\\e*\\
                        NexusConstructor.exe --help
                        """
                        }
                } // stage
            } // if
          } // dir
      } //ws
    } // node
  } // return
} // def

def get_macos_pipeline() {
    return {
        node('macos') {
            cleanWs()
            dir("${project}") {
                stage('Checkout') {
                    try {
                        checkout scm
                    } catch (e) {
                        failure_function(e, 'MacOSX / Checkout failed')
                    } // catch
                } // stage
                stage('Setup') {
                    sh "python3 -m pip install --user -r requirements-dev.txt && git submodule update --init"
                } // stage
                stage('Run tests') {
                    sh "python3 -m pytest . -s --ignore=definitions/ --ignore=tests/ui_tests/"
                } // stage
            } // dir
        } // node
    } // return
} // def

node("docker") {
    cleanWs()
    
    stage('Checkout') {
        dir("${project}") {
            try {
                scm_vars = checkout scm
            } catch (e) {
                failure_function(e, 'Checkout failed')
            }
        }
    }
    
    builders['macOS'] = get_macos_pipeline()
    builders['windows10'] = get_win10_pipeline()
    parallel builders
}
