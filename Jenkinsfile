pipeline {
    agent any

    environment {
        DOCKER_IMAGE = "chetanmatadmtech/fitness-app"
        VERSION = "v${BUILD_NUMBER}"
        BLUE_DEPLOYMENT = "fitness-app-blue-${VERSION}"
        GREEN_DEPLOYMENT = "fitness-app-green-${VERSION}"
        SHADOW_DEPLOYMENT = "fitness-app-shadow-${VERSION}"
        SHADOW_MONITOR_DURATION = "60"  // seconds
        SHADOW_SUCCESS_THRESHOLD = "90" // % healthy pods required
        CANARY_STEPS = "20,40,60,80,100" // traffic % steps
        CANARY_MONITOR_DURATION = "30"  // seconds
        AB_TEST_TRAFFIC = "50,50"       // A/B split %
    }

    stages {
        stage('Checkout Code') {
            steps { checkout scm }
        }

        stage('Setup Python') {
            steps {
                sh '''
                python3 -m venv venv
                . venv/bin/activate
                pip install --upgrade pip
                pip install -r requirements.txt
                pip install pytest
                '''
            }
        }

        stage('Run Tests') {
            steps {
                sh '. venv/bin/activate && python3 -m pytest --maxfail=1 --disable-warnings -q'
            }
        }

        stage('Build Docker Image') {
            steps {
                script { docker.build("${DOCKER_IMAGE}:${VERSION}") }
            }
        }

        stage('Push Docker Image') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'DOCKER_HUB_CREDENTIALS', usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
                    sh '''
                    echo $DOCKER_PASS | docker login -u $DOCKER_USER --password-stdin
                    docker push ${DOCKER_IMAGE}:${VERSION}
                    docker tag ${DOCKER_IMAGE}:${VERSION} ${DOCKER_IMAGE}:latest
                    docker push ${DOCKER_IMAGE}:latest
                    '''
                }
            }
        }

        stage('Deploy Blue/Green/Shadow') {
            steps {
                withCredentials([file(credentialsId: 'EKS_KUBECONFIG', variable: 'KUBECONFIG_FILE')]) {
                    sh '''
                    export KUBECONFIG=$KUBECONFIG_FILE
                    kubectl create ns fitness --dry-run=client -o yaml | kubectl apply -f -

                    # BLUE
                    sed -e "s|IMAGE_PLACEHOLDER|${DOCKER_IMAGE}:${VERSION}|g" \
                        -e "s|VERSION_PLACEHOLDER|${VERSION}|g" \
                        -e "s|DEPLOYMENT_NAME_PLACEHOLDER|${BLUE_DEPLOYMENT}|g" \
                        k8s-deploy/deployment-template.yaml > blue-deployment.yaml
                    kubectl apply -f blue-deployment.yaml --validate=false
                    kubectl rollout status deployment/${BLUE_DEPLOYMENT} --timeout=120s

                    # GREEN
                    sed -e "s|IMAGE_PLACEHOLDER|${DOCKER_IMAGE}:${VERSION}|g" \
                        -e "s|VERSION_PLACEHOLDER|${VERSION}|g" \
                        -e "s|DEPLOYMENT_NAME_PLACEHOLDER|${GREEN_DEPLOYMENT}|g" \
                        k8s-deploy/deployment-template.yaml > green-deployment.yaml
                    kubectl apply -f green-deployment.yaml --validate=false
                    kubectl rollout status deployment/${GREEN_DEPLOYMENT} --timeout=120s

                    # SHADOW
                    sed -e "s|IMAGE_PLACEHOLDER|${DOCKER_IMAGE}:${VERSION}|g" \
                        -e "s|VERSION_PLACEHOLDER|${VERSION}|g" \
                        -e "s|DEPLOYMENT_NAME_PLACEHOLDER|${SHADOW_DEPLOYMENT}|g" \
                        k8s-deploy/deployment-template.yaml > shadow-deployment.yaml
                    kubectl apply -f shadow-deployment.yaml --validate=false
                    kubectl rollout status deployment/${SHADOW_DEPLOYMENT} --timeout=120s

                    # Shadow Health Check
                    echo "Monitoring Shadow deployment for ${SHADOW_MONITOR_DURATION}s..."
                    sleep ${SHADOW_MONITOR_DURATION}
                    READY_PODS=$(kubectl get deployment ${SHADOW_DEPLOYMENT} -o jsonpath='{.status.readyReplicas}')
                    TOTAL_PODS=$(kubectl get deployment ${SHADOW_DEPLOYMENT} -o jsonpath='{.status.replicas}')
                    SUCCESS_RATE=$(( READY_PODS * 100 / TOTAL_PODS ))
                    if [ $SUCCESS_RATE -lt ${SHADOW_SUCCESS_THRESHOLD} ]; then
                        echo "Shadow deployment failed. Rolling back..."
                        kubectl delete deployment ${SHADOW_DEPLOYMENT}
                        exit 1
                    else
                        echo "Shadow deployment healthy."
                    fi
                    '''
                }
            }
        }

        stage('Canary Release') {
            steps {
                withCredentials([file(credentialsId: 'EKS_KUBECONFIG', variable: 'KUBECONFIG_FILE')]) {
                    script {
                        def stepsArray = CANARY_STEPS.split(',')
                        for (stepPercent in stepsArray) {
                            sh """
                            export KUBECONFIG=\$KUBECONFIG_FILE
                            echo "Shifting ${stepPercent}% traffic to Green..."
                            # In real scenario, use ingress/istio weighted routing
                            sleep ${CANARY_MONITOR_DURATION}
                            """
                        }
                        echo "Canary promotion complete: 100% traffic to Green."
                    }
                }
            }
        }

        stage('A/B Testing') {
            steps {
                withCredentials([file(credentialsId: 'EKS_KUBECONFIG', variable: 'KUBECONFIG_FILE')]) {
                    sh '''
                    export KUBECONFIG=$KUBECONFIG_FILE
                    IFS=',' read -r A B <<< "$AB_TEST_TRAFFIC"
                    echo "Starting A/B Testing: A=${A}%, B=${B}%"
                    # Simulate service patching (replace with weighted routing)
                    sleep 30
                    echo "A/B Testing completed"
                    '''
                }
            }
        }

        stage('Build & Archive Artifact') {
            steps {
                sh """
                mkdir -p build_output
                cp Application.py build_output/Application_${VERSION}.py
                cd build_output
                zip Application_${VERSION}.zip Application_${VERSION}.py
                """
                archiveArtifacts artifacts: 'build_output/*.zip', fingerprint: true
            }
        }
    }

    post {
        success { echo "Pipeline completed successfully!" }
        failure { echo "Pipeline failed. Rollback executed if needed." }
    }
}

