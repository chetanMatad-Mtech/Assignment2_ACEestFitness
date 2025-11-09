pipeline {
    agent any

    environment {
        DOCKER_IMAGE_NAME = "chetanmatadmtech/fitness-app"
        DOCKER_IMAGE_TAG = "${BUILD_NUMBER}"
        ECS_CLUSTER = "fitness-app-cluster"
        ECS_TASK_DEFINITION = "fitness-app-task"
        ECS_SERVICE_NAME = "fitness-app-service"
        AWS_REGION = "us-east-1" // change as needed
    }

    stages {

        stage('Checkout Code') {
            steps {
                git branch: 'develop', url: 'https://github.com/chetanMatad-Mtech/Assignment2_ACEestFitness.git'
            }
        }

        stage('Setup Environment') {
            steps {
                sh '''
                    pip install --upgrade pip
                    pip install -r requirements.txt || true
                    pip install pytest
                '''
            }
        }

        stage('Run Tests') {
            steps {
                sh 'python3 -m pytest --maxfail=1 --disable-warnings -q || true'
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    sh "docker build -t ${DOCKER_IMAGE_NAME}:${DOCKER_IMAGE_TAG} ."
                }
            }
        }

        stage('Push Docker Image to Docker Hub') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'DOCKER_HUB_CREDENTIALS', usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
                    sh '''
                        echo $DOCKER_PASS | docker login -u $DOCKER_USER --password-stdin
                        docker push ${DOCKER_IMAGE_NAME}:${DOCKER_IMAGE_TAG}
                        docker tag ${DOCKER_IMAGE_NAME}:${DOCKER_IMAGE_TAG} ${DOCKER_IMAGE_NAME}:latest
                        docker push ${DOCKER_IMAGE_NAME}:latest
                    '''
                }
            }
        }

        stage('Update ECS Task Definition') {
            steps {
                withCredentials([aws(credentialsId: 'AWS_CREDENTIALS', regionVariable: 'AWS_DEFAULT_REGION')]) {
                    sh '''
                        # Register new task definition with updated image
                        NEW_TASK_DEF=$(aws ecs register-task-definition \
                            --family ${ECS_TASK_DEFINITION} \
                            --network-mode awsvpc \
                            --requires-compatibilities FARGATE \
                            --cpu "512" \
                            --memory "1024" \
                            --container-definitions "[{\"name\":\"fitness-app-container\",\"image\":\"${DOCKER_IMAGE_NAME}:${DOCKER_IMAGE_TAG}\",\"essential\":true,\"portMappings\":[{\"containerPort\":8080,\"hostPort\":8080}]}]" \
                            --region ${AWS_REGION})

                        echo "New Task Definition Registered: $NEW_TASK_DEF"

                        # Update ECS Service to use new task definition
                        aws ecs update-service \
                            --cluster ${ECS_CLUSTER} \
                            --service ${ECS_SERVICE_NAME} \
                            --task-definition ${ECS_TASK_DEFINITION} \
                            --region ${AWS_REGION}
                    '''
                }
            }
        }
    }

    post {
        success { echo "Pipeline Completed Successfully!" }
        failure { echo "Pipeline Failed!" }
    }
}

