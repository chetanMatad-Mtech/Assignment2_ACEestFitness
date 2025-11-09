pipeline {
    agent any

    environment {
        DOCKER_IMAGE_NAME = "chetanmatadmtech/fitness-app"
        DOCKER_IMAGE_TAG  = "${BUILD_NUMBER}"
        DOCKER_REGISTRY   = "docker.io"
        FLASK_APP         = "Application.py"
        FLASK_RUN_HOST    = "0.0.0.0"
        FLASK_ENV         = "production"
    }

    stages {

        stage('Checkout SCM') {
            steps {
                git branch: 'develop', url: 'https://github.com/chetanMatad-Mtech/Assignment2_ACEestFitness.git', credentialsId: 'DOCKER_HUB_CREDENTIALS'
            }
        }

        stage('Setup Environment') {
            steps {
                sh '''
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
                    . venv/bin/activate
                    pytest
                '''
            }
        }

        stage('Build Docker Image') {
            steps {
                sh '''
                    docker build -t $DOCKER_IMAGE_NAME:$DOCKER_IMAGE_TAG .
                '''
            }
        }

        stage('Push Docker Image to Docker Hub') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'DOCKER_HUB_CREDENTIALS', 
                                                 usernameVariable: 'DOCKER_USER', 
                                                 passwordVariable: 'DOCKER_PASS')]) {
                    sh '''
                        echo "$DOCKER_PASS" | docker login -u "$DOCKER_USER" --password-stdin
                        docker push $DOCKER_IMAGE_NAME:$DOCKER_IMAGE_TAG
                        docker tag $DOCKER_IMAGE_NAME:$DOCKER_IMAGE_TAG $DOCKER_IMAGE_NAME:latest
                        docker push $DOCKER_IMAGE_NAME:latest
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

