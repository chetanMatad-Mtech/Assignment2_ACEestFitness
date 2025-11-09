pipeline {
    agent any

    environment {
        // Docker Hub credentials stored in Jenkins credentials (Username/Password)
        DOCKER_HUB_CREDENTIALS = credentials('DOCKER_HUB_CREDENTIALS')
        IMAGE_NAME = "chetanmatadmtech/fitness-app"
        FLASK_APP = "Application.py"
        FLASK_RUN_HOST = "0.0.0.0"
        FLASK_ENV = "production"
    }

    stages {
        stage('Checkout SCM') {
            steps {
                git branch: 'develop',
                    url: 'https://github.com/chetanMatad-Mtech/Assignment2_ACEestFitness.git',
                    credentialsId: 'DOCKER_HUB_CREDENTIALS'
            }
        }

        stage('Setup Environment') {
            steps {
                sh '''
                python3 -m venv venv
                source venv/bin/activate
                pip install --upgrade pip
                pip install -r requirements.txt
                '''
            }
        }

        stage('Run Tests') {
            steps {
                sh '''
                source venv/bin/activate
                pytest
                '''
            }
        }

        stage('Build Docker Image') {
            steps {
                sh """
                docker build -t $IMAGE_NAME:latest .
                """
            }
        }

        stage('Push Docker Image to Docker Hub') {
            steps {
                script {
                    docker.withRegistry('https://index.docker.io/v1/', 'DOCKER_HUB_CREDENTIALS') {
                        sh "docker push $IMAGE_NAME:latest"
                    }
                }
            }
        }

        stage('Update ECS Task Definition') {
            steps {
                sh """
                # Assuming ECS service & cluster names
                CLUSTER_NAME="fitness-cluster"
                SERVICE_NAME="fitness-service"

                # Force ECS to deploy the latest Docker image
                aws ecs update-service \
                    --cluster $CLUSTER_NAME \
                    --service $SERVICE_NAME \
                    --force-new-deployment
                """
            }
        }
    }

    post {
        success {
            echo 'Pipeline completed successfully!'
        }
        failure {
            echo 'Pipeline failed!'
        }
    }
}

