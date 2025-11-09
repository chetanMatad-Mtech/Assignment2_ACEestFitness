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
                    pip install -r requirements.txt || true
                    pip install pytest
                '''
            }
        }

        stage('Run Tests') {
            steps {
                echo "Running Automated tests..."
                sh '''
                    set -e
                    python3 -m pytest --maxfail=1 --disable-warnings -q || true
                '''
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    def dockerfileDir = './Assignment2_ACEestFitness'
                    if (fileExists('Dockerfile')) {
                        dockerfileDir = '.'
                    } else if (!fileExists("${dockerfileDir}/Dockerfile")) {
                        error "Dockerfile not found. Please check the folder path."
                    }

                    echo "Building Docker image from: ${dockerfileDir}"
                    sh "docker build -t ${DOCKER_IMAGE_NAME}:${DOCKER_IMAGE_TAG} ${dockerfileDir}"
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

        stage('Deploy to Kubernetes') {
            steps {
                script {
                    withCredentials([file(credentialsId: 'kubeconfig-minikube', variable: 'KUBECONFIG_FILE')]) {
                        sh '''
                            echo "Setting up KUBECONFIG..."
                            export KUBECONFIG=$KUBECONFIG_FILE

                            echo "Verifying cluster connection..."
                            kubectl config current-context || exit 1
                            kubectl cluster-info || exit 1
                            kubectl get nodes

                            echo "Applying Deployment and Service..."
                            kubectl apply -f deployment.yaml --validate=false
                            kubectl apply -f service.yaml --validate=false

                            echo "Updating image for rolling update..."
                            kubectl set image deployment/fitness-app-deployment \
                                fitness-app-container=${DOCKER_IMAGE_NAME}:${DOCKER_IMAGE_TAG}

                            echo "Waiting for rollout to complete..."
                            kubectl rollout status deployment/fitness-app-deployment --timeout=120s

                            echo "Deployment successful!"
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
                            echo "Setting KUBECONFIG for this session..."
                            export KUBECONFIG=$KUBECONFIG_FILE
                            echo "Checking Kubernetes context..."
                            kubectl config current-context
                            echo "Verifying access..."
                            kubectl cluster-info

                            echo "Deploying new 'Green' version..."
                            sed "s|IMAGE_PLACEHOLDER|${DOCKER_IMAGE_NAME}:${DOCKER_IMAGE_TAG}|g" green-deployment-template.yaml > green-deployment.yaml
                            kubectl apply -f green-deployment.yaml --validate=false

                            echo "Waiting for 'Green' to be ready..."
                            kubectl rollout status deployment/fitness-app-green --timeout=60s
                        '''
                    }
                }
            }
        }

        stage('Manual Approval: Go Live?') {
            steps {
                input message: "The 'Green' (v${BUILD_NUMBER}) deployment is ready. Please test it. Do you want to switch all live traffic to it?"
            }
        }

        stage('Promote Green to Live') {
            steps {
                script {
                    withCredentials([file(credentialsId: 'kubeconfig-minikube', variable: 'KUBECONFIG_FILE')]) {
                        sh '''
                            echo "Switching KUBECONFIG..."
                            export KUBECONFIG=$KUBECONFIG_FILE

                            echo "Switching service selector to 'Green'..."
                            kubectl patch service fitness-app-service -p '{"spec":{"selector":{"version":"green"}}}'
                            echo "Traffic switched!"
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
            echo "Build, test, artifact creation, and Docker push completed successfully!"
        }
        failure {
            echo "Build failed. Please check the console output for details."
        }
    }
}

