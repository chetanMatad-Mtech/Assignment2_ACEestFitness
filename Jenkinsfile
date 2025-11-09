pipeline {
    agent any

    environment {
        DOCKER_HUB_CREDENTIALS = credentials('DOCKER_HUB_CREDENTIALS')
        IMAGE_NAME = "chetanmatadmtech/fitness-app:latest"
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
                #!/bin/bash
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
                #!/bin/bash
                source venv/bin/activate
                pytest
                '''
            }
        }

        stage('Build Docker Image') {
            steps {
                sh '''
                docker build -t $IMAGE_NAME .
                '''
            }
        }

        stage('Push Docker Image to Docker Hub') {
            steps {
                withDockerRegistry([credentialsId: 'DOCKER_HUB_CREDENTIALS', url: '']) {
                    sh "docker push $IMAGE_NAME"
                }
            }
        }

        stage('Update ECS Task Definition') {
            steps {
                sh '''
                #!/bin/bash
                # Assuming Jenkins is running on EC2 with an IAM role having ECS permissions
                # Update task definition and force service update
                TASK_FAMILY="fitness-app-task"
                CONTAINER_NAME="fitness-app-container"
                NEW_IMAGE="$IMAGE_NAME"

                # Register new task definition revision with updated image
                TASK_DEF_JSON=$(aws ecs describe-task-definition --task-definition $TASK_FAMILY)
                NEW_TASK_DEF=$(echo $TASK_DEF_JSON | \
                    jq --arg IMAGE "$NEW_IMAGE" '.taskDefinition |
                        {family: .family,
                         containerDefinitions: [.containerDefinitions[] | .image=$IMAGE],
                         networkMode: .networkMode,
                         requiresCompatibilities: .requiresCompatibilities,
                         cpu: .cpu,
                         memory: .memory,
                         executionRoleArn: .executionRoleArn,
                         taskRoleArn: .taskRoleArn
                        }')
                
                aws ecs register-task-definition --cli-input-json "$NEW_TASK_DEF"

                # Update service to use new task definition
                aws ecs update-service --cluster fitness-app-cluster --service fitness-app-service --force-new-deployment
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

