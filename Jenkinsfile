def context = [:]
def app_name = "gpx-server"
def namespace = "production"

pipeline {
  agent any

  parameters {
    // build configs
    string(name: "branch", defaultValue: "master", description: "Branch to build")
  }

  stages {
    stage("Set contexts") {
      steps{
        script {
          context.image = "${env.GCR_IMAGE_PREFIX}${app_name}:${namespace}-${env.BUILD_NUMBER}"
        }
      }
    }
    stage("Building Image") {
      steps{
        script {
          context.dockerImage = docker.build("${context.image}",  '-f ./Dockerfile .')
        }
      }
    }
    stage("Testing Image") {
      steps{
        script {
          docker.image('mdillon/postgis:11-alpine').withRun("-e POSTGRES_PASSWORD=aaaa") { db_c ->
            def postgres_ip = sh(script: "docker inspect -f {{.NetworkSettings.IPAddress}} ${db_c.id}", returnStdout: true)

            docker.image('mdillon/postgis').inside("-u root") {
              sh "while ! pg_isready -h\"${postgres_ip}\" ; do sleep 1; done"
            }
            docker.image("${context.image}").inside("-u root -e GPX_DB_USER=postgres -e GPX_DB_NAME=postgres -e GPX_DB_PASSWORD=aaaa -e GPX_DB_HOST=${postgres_ip}") {
              sh "cd /gpx && ./manage.py test --noinput"
            }
          }
        }

      }
    }
    stage("Push and Deploy") {
      steps {
        build job: 'push_and_deploy', parameters: [
          [$class: 'StringParameterValue', name: 'full_image', value: context.image],
          [$class: 'StringParameterValue', name: 'namespace', value: namespace],
          [$class: 'StringParameterValue', name: 'app_name', value: app_name],
          [$class: 'BooleanParameterValue', name: 'deploy', value: false],
        ]
      }
    }
  }
}
