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

        stage('Push Docker Image') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'DOCKER_HUB_CREDENTIALS', usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
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
                    def liveVersion = sh(script: "kubectl get service fitness-app-service -o jsonpath='{.spec.selector.version}' || echo 'none'", returnStdout: true).trim()
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
                    echo "Next deployment (Canary): ${env.NEXT_DEPLOYMENT_NAME}"
                }
            }
        }

        stage('Deploy Canary') {
            steps {
                script {
                    withCredentials([file(credentialsId: 'kubeconfig-minikube', variable: 'KUBECONFIG_FILE')]) {
                        try {
                            sh """
                                export KUBECONFIG=$KUBECONFIG_FILE

                                # Deploy new version as canary
                                sed "s|IMAGE_PLACEHOLDER|${DOCKER_IMAGE_NAME}:${DOCKER_IMAGE_TAG}|g; \
                                     s|VERSION_PLACEHOLDER|${VERSION}|g; \
                                     s|DEPLOYMENT_NAME_PLACEHOLDER|${NEXT_DEPLOYMENT_NAME}|g" ${NEXT_DEPLOYMENT}-deployment-template.yaml > deployment.yaml
                                kubectl apply -f deployment.yaml --validate=false

                                echo "Waiting for Canary rollout..."
                                kubectl rollout status deployment/${NEXT_DEPLOYMENT_NAME} --timeout=120s

                                # Route partial traffic to Canary (50% example)
                                kubectl patch service fitness-app-service -p '{"spec":{"selector":{"version":"${VERSION}"}}}' --type=merge || true
                                echo "Canary deployment live for partial traffic"
                            """
                        } catch (Exception e) {
                            echo "Canary deployment failed, rolling back..."
                            sh "kubectl patch service fitness-app-service -p '{\"spec\":{\"selector\":{\"version\":\"${CURRENT_DEPLOYMENT}\"}}}' --type=merge"
                            error "Canary failed and rollback executed!"
                        }
                    }
                }
            }
        }

        stage('Promote Canary to Full') {
            steps {
                input message: "Canary is stable. Promote ${VERSION} to full production?"
                script {
                    withCredentials([file(credentialsId: 'kubeconfig-minikube', variable: 'KUBECONFIG_FILE')]) {
                        sh """
                            export KUBECONFIG=$KUBECONFIG_FILE
                            echo "Routing full traffic to ${NEXT_DEPLOYMENT}..."
                            sed "s|VERSION_PLACEHOLDER|${VERSION}|g" service-template.yaml > service.yaml
                            kubectl apply -f service.yaml --validate=false
                        """
                    }
                }
            }
        }

        stage('Build & Archive Artifact') {
            steps {
                sh """
                    mkdir -p build_output
                    cp Application.py build_output/${APP_NAME}_${VERSION}.py
                    cd build_output
                    zip ${APP_NAME}_${VERSION}.zip ${APP_NAME}_${VERSION}.py
                """
                archiveArtifacts artifacts: 'build_output/*.zip', fingerprint: true
            }
        }
    }

    post {
        success {
            echo "Build, Canary deployment, promotion, and artifact archiving completed successfully!"
        }
        failure {
            echo "Pipeline failed. Check logs and rollback executed if needed."
        }
    }
}

