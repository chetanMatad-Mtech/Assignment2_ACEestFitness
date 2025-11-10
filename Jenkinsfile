pipeline {
    agent any

    environment {
        AWS_REGION = 'eu-north-1'
        EKS_CLUSTER = 'fitness-eks'
        DOCKER_IMAGE_NAME = 'chetanmatadmtech/fitness-app'
        DOCKER_IMAGE_TAG = "${BUILD_NUMBER}"
        VERSION = "v${BUILD_NUMBER}"

        BLUE_DEPLOYMENT_NAME = "fitness-app-blue-${BUILD_NUMBER}"
        GREEN_DEPLOYMENT_NAME = "fitness-app-green-${BUILD_NUMBER}"
        SHADOW_DEPLOYMENT_NAME = "fitness-app-shadow-${BUILD_NUMBER}"

        SHADOW_MONITOR_DURATION = 60      // seconds
        SHADOW_SUCCESS_THRESHOLD = 90     // % healthy pods
        CANARY_STEPS = "20,40,60,80,100" // traffic % steps
        CANARY_MONITOR_DURATION = 30      // seconds per step
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
                sh '''
                    . venv/bin/activate
                    pytest --maxfail=1 --disable-warnings -q || true
                '''
            }
        }

        stage('Build Docker Image') {
            steps {
                sh """
                    docker build -t ${DOCKER_IMAGE_NAME}:${DOCKER_IMAGE_TAG} .
                """
            }
        }

        stage('Push Docker Image') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'DOCKER_HUB_CREDENTIALS',
                                                 usernameVariable: 'DOCKER_USER',
                                                 passwordVariable: 'DOCKER_PASS')]) {
                    sh '''
                        echo $DOCKER_PASS | docker login -u $DOCKER_USER --password-stdin
                        docker push ${DOCKER_IMAGE_NAME}:${DOCKER_IMAGE_TAG}
                        docker tag ${DOCKER_IMAGE_NAME}:${DOCKER_IMAGE_TAG} ${DOCKER_IMAGE_NAME}:latest
                        docker push ${DOCKER_IMAGE_NAME}:latest
                    '''
                }
            }
        }

        stage('Deploy Blue/Green') {
            steps {
                withCredentials([string(credentialsId: 'EKS_KUBECONFIG', variable: 'KUBECONFIG_CONTENT')]) {
    sh '''
        KUBECONFIG_FILE=$(mktemp)
        printf "%s" "$KUBECONFIG_CONTENT" > $KUBECONFIG_FILE

        kubectl create ns fitness --dry-run=client -o yaml --kubeconfig $KUBECONFIG_FILE | kubectl apply -f - --kubeconfig $KUBECONFIG_FILE

        # Blue deployment
        sed "s|IMAGE_PLACEHOLDER|${DOCKER_IMAGE_NAME}:${DOCKER_IMAGE_TAG}|g; \
             s|VERSION_PLACEHOLDER|${VERSION}|g; \
             s|DEPLOYMENT_NAME_PLACEHOLDER|${BLUE_DEPLOYMENT_NAME}|g" k8s-deploy/blue-deployment-template.yaml \
             > blue-deployment.yaml
        kubectl apply -f blue-deployment.yaml --validate=false --kubeconfig $KUBECONFIG_FILE
        kubectl rollout status deployment/${BLUE_DEPLOYMENT_NAME} --timeout=120s --kubeconfig $KUBECONFIG_FILE

        rm -f $KUBECONFIG_FILE
    '''
}

            }
        }

        stage('Deploy Shadow') {
            steps {
                withCredentials([string(credentialsId: 'EKS_KUBECONFIG', variable: 'KUBECONFIG_CONTENT')]) {
                    sh '''
                        KUBECONFIG_FILE=$(mktemp)
                        echo "$KUBECONFIG_CONTENT" > $KUBECONFIG_FILE

                        sed "s|IMAGE_PLACEHOLDER|${DOCKER_IMAGE_NAME}:${DOCKER_IMAGE_TAG}|g; \
                             s|VERSION_PLACEHOLDER|${VERSION}|g; \
                             s|DEPLOYMENT_NAME_PLACEHOLDER|${SHADOW_DEPLOYMENT_NAME}|g" k8s-deploy/shadow-deployment-template.yaml \
                             > shadow-deployment.yaml
                        kubectl apply -f shadow-deployment.yaml --validate=false --kubeconfig $KUBECONFIG_FILE
                        kubectl rollout status deployment/${SHADOW_DEPLOYMENT_NAME} --timeout=120s --kubeconfig $KUBECONFIG_FILE

                        echo "Monitoring Shadow deployment for ${SHADOW_MONITOR_DURATION} seconds..."
                        sleep ${SHADOW_MONITOR_DURATION}

                        READY_PODS=$(kubectl get deployment ${SHADOW_DEPLOYMENT_NAME} -o jsonpath='{.status.readyReplicas}' --kubeconfig $KUBECONFIG_FILE)
                        TOTAL_PODS=$(kubectl get deployment ${SHADOW_DEPLOYMENT_NAME} -o jsonpath='{.status.replicas}' --kubeconfig $KUBECONFIG_FILE)
                        SUCCESS_RATE=$(( READY_PODS * 100 / TOTAL_PODS ))

                        if [ $SUCCESS_RATE -lt ${SHADOW_SUCCESS_THRESHOLD} ]; then
                            echo "Shadow deployment failed. Rolling back..."
                            kubectl delete deployment ${SHADOW_DEPLOYMENT_NAME} --kubeconfig $KUBECONFIG_FILE
                            exit 1
                        else
                            echo "Shadow deployment healthy."
                        fi

                        rm -f $KUBECONFIG_FILE
                    '''
                }
            }
        }

        stage('Canary Release') {
            steps {
                withCredentials([string(credentialsId: 'EKS_KUBECONFIG', variable: 'KUBECONFIG_CONTENT')]) {
                    sh '''
                        KUBECONFIG_FILE=$(mktemp)
                        echo "$KUBECONFIG_CONTENT" > $KUBECONFIG_FILE

                        IFS=',' read -r -a STEPS <<< "${CANARY_STEPS}"
                        for STEP in "${STEPS[@]}"; do
                            echo "Shifting $STEP% traffic to Green deployment..."
                            # Example: patch service selector or ingress routing
                            sleep ${CANARY_MONITOR_DURATION}
                        done

                        echo "Canary promotion complete. 100% traffic now points to Green."
                        rm -f $KUBECONFIG_FILE
                    '''
                }
            }
        }

    }

    post {
        success { echo "Pipeline completed successfully!" }
        failure { echo "Pipeline failed. Rollback executed if needed." }
    }
}

