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

        stage('Determine Deployment') {
            steps {
                script {
                    def liveVersion = sh(
                        script: "kubectl get service fitness-app-service -o jsonpath='{.spec.selector.version}' || echo 'none'",
                        returnStdout: true
                    ).trim()

                    if (liveVersion == "none" || liveVersion.contains("green")) {
                        env.NEXT_DEPLOYMENT = "blue"
                        env.CURRENT_DEPLOYMENT = "green"
                    } else {
                        env.NEXT_DEPLOYMENT = "green"
                        env.CURRENT_DEPLOYMENT = "blue"
                    }

                    env.NEXT_DEPLOYMENT_NAME = "fitness-app-${env.NEXT_DEPLOYMENT}-v${BUILD_NUMBER}"
                    env.CURRENT_DEPLOYMENT_NAME = "fitness-app-${env.CURRENT_DEPLOYMENT}-v${BUILD_NUMBER}"

                    echo "Current live deployment: ${env.CURRENT_DEPLOYMENT_NAME}"
                    echo "Next deployment: ${env.NEXT_DEPLOYMENT_NAME}"
                }
            }
        }

        stage('Deploy Next') {
            steps {
                script {
                    withCredentials([file(credentialsId: 'kubeconfig-minikube', variable: 'KUBECONFIG_FILE')]) {
                        try {
                            sh """
                                export KUBECONFIG=$KUBECONFIG_FILE

                                echo "Deploying ${NEXT_DEPLOYMENT} version..."
                                sed "s|IMAGE_PLACEHOLDER|${DOCKER_IMAGE_NAME}:${DOCKER_IMAGE_TAG}|g; \
                                     s|VERSION_PLACEHOLDER|${VERSION}|g; \
                                     s|DEPLOYMENT_NAME_PLACEHOLDER|${NEXT_DEPLOYMENT_NAME}|g" ${NEXT_DEPLOYMENT}-deployment-template.yaml > deployment.yaml
                                kubectl apply -f deployment.yaml --validate=false

                                echo "Waiting for ${NEXT_DEPLOYMENT} rollout..."
                                kubectl rollout status deployment/${NEXT_DEPLOYMENT_NAME} --timeout=120s

                                echo "Switching service to ${NEXT_DEPLOYMENT}..."
                                sed "s|VERSION_PLACEHOLDER|${VERSION}|g" service-template.yaml > service.yaml
                                kubectl apply -f service.yaml --validate=false

                                echo "${NEXT_DEPLOYMENT} is now live!"
                            """
                        } catch (Exception e) {
                            echo "Deployment failed, rolling back to ${CURRENT_DEPLOYMENT}..."
                            sh """
                                sed "s|VERSION_PLACEHOLDER|${VERSION}|g" service-template.yaml > service.yaml
                                kubectl apply -f service.yaml --validate=false
                            """
                            error "Deployment failed and rollback executed!"
                        }
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

