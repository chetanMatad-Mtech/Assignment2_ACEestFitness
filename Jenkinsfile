pipeline {
    agent any

    environment {
        DOCKER_IMAGE = "chetanmatadmtech/fitness-app:latest"
        DOCKER_REGISTRY = "docker.io"
        FLASK_APP = "Application.py"
        FLASK_RUN_HOST = "0.0.0.0"
        FLASK_ENV = "production"
    }

    stages {
        stage('Checkout SCM') {
            steps {
                checkout([$class: 'GitSCM', 
                          branches: [[name: 'develop']],
                          userRemoteConfigs: [[
                              url: 'https://github.com/chetanMatad-Mtech/Assignment2_ACEestFitness.git',
                              credentialsId: 'DOCKER_HUB_CREDENTIALS'
                          ]]
                ])
            }
        }

        stage('Setup Environment') {
            steps {
                sh '''
                #!/bin/bash
                python3 -m venv venv
                . venv/bin/activate
                pip install --upgrade pip
                pip install -r requirements.txt
                '''
            }
        }

        stage('Run Tests') {
            steps {
                sh '''
                #!/bin/bash
                . venv/bin/activate
                pytest
                '''
            }
        }

        stage('Build Docker Image') {
            steps {
                sh '''
                docker build -t $DOCKER_IMAGE .
                '''
            }
        }

        stage('Push Docker Image to Docker Hub') {
            steps {
                withDockerRegistry([credentialsId: 'DOCKER_HUB_CREDENTIALS', url: "https://$DOCKER_REGISTRY"]) {
                    sh '''
                    docker push $DOCKER_IMAGE
                    '''
                }
            }
        }

        stage('Update ECS Task Definition') {
            steps {
                sh '''
                # Assumes Jenkins is running on EC2 with IAM role having ECS permissions
                aws ecs update-service \
                    --cluster fitness-cluster \
                    --service fitness-service \
                    --force-new-deployment
                '''
            }
        }
    }

    post {
        success {
            echo "Pipeline completed successfully!"
        }
        failure {
            echo "Pipeline failed!"
        }
    }
}

