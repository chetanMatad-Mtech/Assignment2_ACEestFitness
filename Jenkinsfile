pipeline {
    agent any
    environment {
        DOCKER_IMAGE_NAME = "chetanmatadmtech/Fitness-app"
    }
    stages {
        stage('Checkout') {
            steps {
                git url: 'https://github.com/chetanMatad-Mtech/Assignment2_ACEestFitness.git', branch: 'develop'
            }
        }
        stage('Build Docker Image') {
            steps {
                sh 'docker build -t $DOCKER_IMAGE_NAME .'
            }
        }
        stage('Push Docker Image') {
            steps {
                withCredentials([string(credentialsId: 'dockerhub-password', variable: 'DOCKERHUB_PASS')]) {
                    sh '''
                        echo $DOCKERHUB_PASS | docker login -u chetanmatadmtech --password-stdin
                        docker push $DOCKER_IMAGE_NAME
                    '''
                }
            }
        }
    }
}

