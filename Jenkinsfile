pipeline {
    agent any

    environment {
        DOCKER_IMAGE_NAME = "chetanmatadmtech/fitness-app"
        DOCKER_IMAGE_TAG = "${BUILD_NUMBER}"
        APP_NAME = "Application"
        VERSION = "v${BUILD_NUMBER}"
    }

    stages {

        stage('Checkout Code') {
            steps {
                echo "Checking out the repository..."
                git branch: 'develop',
                    url: 'https://github.com/chetanMatad-Mtech/Assignment2_ACEestFitness.git'
            }
        }

        stage('Setup Environment') {
            steps {
                echo 'Installing Python dependencies...'
                sh '''
                    pip install --upgrade pip
                    pip install -r requirements.txt
                    pip install pytest
                '''
            }
        }

        stage('Run Tests') {
            steps {
                echo "Running Automated tests..."
                sh '''
                    set -e
                    python3 -m pytest --maxfail=1 --disable-warnings -q
                '''
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    echo "Building Docker image..."
                    sh "docker build -t ${DOCKER_IMAGE_NAME}:${DOCKER_IMAGE_TAG} ."
                }
            }
        }

        stage('Push Docker Image') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'DOCKER_HUB_CREDENTIALS',
                    usernameVariable: 'DOCKER_USER',
                    passwordVariable: 'DOCKER_PASS'
                )]) {
                    sh '''
                        echo "$DOCKER_PASS" | docker login -u "$DOCKER_USER" --password-stdin
                        docker push ${DOCKER_IMAGE_NAME}:${DOCKER_IMAGE_TAG}
                        docker tag ${DOCKER_IMAGE_NAME}:${DOCKER_IMAGE_TAG} ${DOCKER_IMAGE_NAME}:latest
                        docker push ${DOCKER_IMAGE_NAME}:latest
                    '''
                }
            }
        }

        stage('Deploy Blue') {
            steps {
                script {
                    withCredentials([file(credentialsId: 'kubeconfig-minikube', variable: 'KUBECONFIG_FILE')]) {
                        sh '''
                            export KUBECONFIG=$KUBECONFIG_FILE

                            echo "Deploying 'Blue' version..."
                            sed "s|IMAGE_PLACEHOLDER|${DOCKER_IMAGE_NAME}:${DOCKER_IMAGE_TAG}|g" blue-deployment-template.yaml > blue-deployment.yaml
                            kubectl apply -f blue-deployment.yaml --validate=false
                            kubectl rollout status deployment/fitness-app-blue --timeout=120s
                        '''
                    }
                }
            }
        }

        stage('Deploy Green') {
            steps {
                script {
                    withCredentials([file(credentialsId: 'kubeconfig-minikube', variable: 'KUBECONFIG_FILE')]) {
                        sh '''
                            export KUBECONFIG=$KUBECONFIG_FILE

                            echo "Deploying 'Green' version..."
                            sed "s|IMAGE_PLACEHOLDER|${DOCKER_IMAGE_NAME}:${DOCKER_IMAGE_TAG}|g" green-deployment-template.yaml > green-deployment.yaml
                            kubectl apply -f green-deployment.yaml --validate=false
                            kubectl rollout status deployment/fitness-app-green --timeout=120s
                        '''
                    }
                }
            }
        }

        stage('Manual Approval: Go Live?') {
            steps {
                input message: "Both 'Blue' and 'Green' deployments are ready. Do you want to switch live traffic to 'Green'?"
            }
        }

        stage('Promote Green to Live') {
            steps {
                script {
                    withCredentials([file(credentialsId: 'kubeconfig-minikube', variable: 'KUBECONFIG_FILE')]) {
                        sh '''
                            export KUBECONFIG=$KUBECONFIG_FILE

                            echo "Switching service selector to 'Green'..."
                            kubectl patch service fitness-app-service -p '{"spec":{"selector":{"version":"green"}}}'
                            echo "Traffic switched to 'Green'!"
                        '''
                    }
                }
            }
        }

        stage('Build Artifact') {
            steps {
                echo "Building artifact for ${APP_NAME} version ${VERSION}..."
                sh """
                    mkdir -p build_output
                    cp Application.py build_output/${APP_NAME}_${VERSION}.py
                    cd build_output
                    zip ${APP_NAME}_${VERSION}.zip ${APP_NAME}_${VERSION}.py
                """
            }
        }

        stage('Archive Artifact') {
            steps {
                echo "Archiving artifact to Jenkins..."
                archiveArtifacts artifacts: 'build_output/*.zip', fingerprint: true
            }
        }
    }

    post {
        success {
            echo "Build, test, artifact creation, Docker push, and Blue-Green deployment completed successfully!"
        }
        failure {
            echo "Build failed. Please check the console output for details."
        }
    }
}

