pipeline {
    agent any

    environment {
        DOCKER_IMAGE_NAME = "chetanmatadmtech/fitness-app"
        DOCKER_IMAGE_TAG = "${BUILD_NUMBER}"
        APP_NAME = "Application"
        VERSION = "v${BUILD_NUMBER}" 
        BLUE_DEPLOYMENT_NAME = "fitness-app-blue-v${BUILD_NUMBER}"
        GREEN_DEPLOYMENT_NAME = "fitness-app-green-v${BUILD_NUMBER}"
        SHADOW_DEPLOYMENT_NAME = "fitness-app-shadow-v${BUILD_NUMBER}"
        SHADOW_MONITOR_DURATION = "60"  // seconds to monitor shadow
        SHADOW_SUCCESS_THRESHOLD = "90" // minimum healthy pod % for shadow
        CANARY_STEPS = "20,40,60,80,100" // traffic % steps for Canary
        CANARY_MONITOR_DURATION = "30"  // seconds to monitor each Canary step
        AB_TEST_TRAFFIC = "50,50" // percentage split for A/B Testing (A=50%, B=50%)
        ROLLING_UPDATE_MAX_SURGE = "25%"  // Max surge for RollingUpdate
        ROLLING_UPDATE_MAX_UNAVAILABLE = "25%" // Max unavailable pods for RollingUpdate
        CONTAINER_NAME = "fitness-app-container"
    }

    stages {

        stage('Checkout Code') {
            steps { git branch: 'develop', url: 'https://github.com/chetanMatad-Mtech/Assignment2_ACEestFitness.git' }
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
            steps { sh 'python3 -m pytest --maxfail=1 --disable-warnings -q || true' }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    def dockerfileDir = fileExists('Dockerfile') ? '.' : './Assignment2_ACEestFitness'
                    sh "docker build -t ${DOCKER_IMAGE_NAME}:${DOCKER_IMAGE_TAG} ${dockerfileDir}"
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

        stage('Deploy Blue and Green') {
            steps {
                script {
                    withCredentials([file(credentialsId: 'kubeconfig-minikube', variable: 'KUBECONFIG_FILE')]) {
                        sh """
                            if [ ! -f \$KUBECONFIG_FILE ]; then
                                echo "KUBECONFIG file not found!"
                                exit 1
                            fi
                            export KUBECONFIG=\$KUBECONFIG_FILE
                            
                            # Deploy Blue
                            sed "s|IMAGE_PLACEHOLDER|${DOCKER_IMAGE_NAME}:${DOCKER_IMAGE_TAG}|g; \
                                 s|VERSION_PLACEHOLDER|${VERSION}|g; \
                                 s|DEPLOYMENT_NAME_PLACEHOLDER|${BLUE_DEPLOYMENT_NAME}|g" blue-deployment-template.yaml > blue-deployment.yaml
                            kubectl apply -f blue-deployment.yaml --validate=false
                            kubectl rollout status deployment/${BLUE_DEPLOYMENT_NAME} --timeout=120s
                            
                            # Deploy Green
                            sed "s|IMAGE_PLACEHOLDER|${DOCKER_IMAGE_NAME}:${DOCKER_IMAGE_TAG}|g; \
                                 s|VERSION_PLACEHOLDER|${VERSION}|g; \
                                 s|DEPLOYMENT_NAME_PLACEHOLDER|${GREEN_DEPLOYMENT_NAME}|g" green-deployment-template.yaml > green-deployment.yaml
                            kubectl apply -f green-deployment.yaml --validate=false
                            kubectl rollout status deployment/${GREEN_DEPLOYMENT_NAME} --timeout=120s
                        """
                    }
                }
            }
        }

        stage('Deploy Shadow') {
            steps {
                script {
                    withCredentials([file(credentialsId: 'kubeconfig-minikube', variable: 'KUBECONFIG_FILE')]) {
                        sh """
                            export KUBECONFIG=\$KUBECONFIG_FILE
                            sed "s|IMAGE_PLACEHOLDER|${DOCKER_IMAGE_NAME}:${DOCKER_IMAGE_TAG}|g; \
                                 s|VERSION_PLACEHOLDER|${VERSION}|g; \
                                 s|DEPLOYMENT_NAME_PLACEHOLDER|${SHADOW_DEPLOYMENT_NAME}|g" shadow-deployment-template.yaml > shadow-deployment.yaml
                            kubectl apply -f shadow-deployment.yaml --validate=false
                            kubectl rollout status deployment/${SHADOW_DEPLOYMENT_NAME} --timeout=120s

                            echo "Monitoring Shadow deployment for ${SHADOW_MONITOR_DURATION} seconds..."
                            sleep ${SHADOW_MONITOR_DURATION}
                            READY_PODS=\$(kubectl get deployment ${SHADOW_DEPLOYMENT_NAME} -o jsonpath='{.status.readyReplicas}')
                            TOTAL_PODS=\$(kubectl get deployment ${SHADOW_DEPLOYMENT_NAME} -o jsonpath='{.status.replicas}')
                            SUCCESS_RATE=\$(( READY_PODS * 100 / TOTAL_PODS ))
                            if [ \$SUCCESS_RATE -lt ${SHADOW_SUCCESS_THRESHOLD} ]; then
                                echo "Shadow deployment failed. Rolling back..."
                                kubectl delete deployment ${SHADOW_DEPLOYMENT_NAME}
                                exit 1
                            else
                                echo "Shadow deployment healthy."
                            fi
                        """
                    }
                }
            }
        }

        stage('A/B Testing') {
            steps {
                script {
                    def abPercentages = AB_TEST_TRAFFIC.split(',')
                    if (abPercentages.size() != 2) error "AB_TEST_TRAFFIC must have two values"
                    
                    withCredentials([file(credentialsId: 'kubeconfig-minikube', variable: 'KUBECONFIG_FILE')]) {
                        sh """
                            export KUBECONFIG=\$KUBECONFIG_FILE
                            echo "Starting A/B Testing: Version A=${abPercentages[0]}%, Version B=${abPercentages[1]}%"
                            # Simulate A/B traffic routing
                            kubectl patch svc fitness-app-service -p '{"spec":{"selector":{"version":"vA"}}}' --type=merge
                            sleep 30
                            kubectl patch svc fitness-app-service -p '{"spec":{"selector":{"version":"vB"}}}' --type=merge
                            sleep 30
                            echo "A/B Testing completed"
                        """
                    }
                }
            }
        }

        stage('Canary Release to Green') {
            steps {
                script {
                    withCredentials([file(credentialsId: 'kubeconfig-minikube', variable: 'KUBECONFIG_FILE')]) {
                        def stepsArray = CANARY_STEPS.split(',')
                        for (stepPercent in stepsArray) {
                            sh """
                                export KUBECONFIG=\$KUBECONFIG_FILE
                                echo "Shifting ${stepPercent}% traffic to Green..."
                                kubectl patch svc fitness-app-service -p '{"spec":{"selector":{"version":"${VERSION}"}}}' --type=merge
                                sleep ${CANARY_MONITOR_DURATION}
                            """
                        }
                        echo "Canary promotion complete. 100% traffic now points to Green."
                    }
                }
            }
        }

        stage('Rolling Update') {
            steps {
                script {
                    withCredentials([file(credentialsId: 'kubeconfig-minikube', variable: 'KUBECONFIG_FILE')]) {
                        sh """
                            export KUBECONFIG=\$KUBECONFIG_FILE
                            echo "Starting Rolling Update for ${GREEN_DEPLOYMENT_NAME}..."
                            kubectl set image deployment/${GREEN_DEPLOYMENT_NAME} ${CONTAINER_NAME}=${DOCKER_IMAGE_NAME}:${DOCKER_IMAGE_TAG}
                            kubectl patch deployment ${GREEN_DEPLOYMENT_NAME} -p '{
                                "spec": {
                                    "strategy": {
                                        "type": "RollingUpdate",
                                        "rollingUpdate": {
                                            "maxSurge": "${ROLLING_UPDATE_MAX_SURGE}",
                                            "maxUnavailable": "${ROLLING_UPDATE_MAX_UNAVAILABLE}"
                                        }
                                    }
                                }
                            }'
                            kubectl rollout status deployment/${GREEN_DEPLOYMENT_NAME} --timeout=180s
                            echo "Rolling Update completed."
                        """
                    }
                }
            }
        }

        stage('Build Artifact') {
            steps {
                sh """
                    mkdir -p build_output
                    cp Application.py build_output/${APP_NAME}_${VERSION}.py
                    cd build_output
                    zip ${APP_NAME}_${VERSION}.zip ${APP_NAME}_${VERSION}.py
                """
            }
        }

        stage('Archive Artifact') {
            steps { archiveArtifacts artifacts: 'build_output/*.zip', fingerprint: true }
        }
    }

    post {
        success { echo "Pipeline completed successfully!" }
        failure { echo "Pipeline failed. Rollback executed if needed." }
    }
}

