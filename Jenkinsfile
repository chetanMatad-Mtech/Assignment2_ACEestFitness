pipeline {
    agent any

    environment {
        DOCKER_IMAGE = "chetanmatadmtech/fitness-app"
        VERSION = "v${BUILD_NUMBER}" // Dynamic version based on Jenkins build
        BLUE_DEPLOYMENT_NAME = "fitness-app-blue-v${BUILD_NUMBER}"
        GREEN_DEPLOYMENT_NAME = "fitness-app-green-v${BUILD_NUMBER}"
    }

    stages {

        stage('Checkout Code') {
            steps {
                checkout scm
            }
        }

        stage('Setup Python Environment') {
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
                sh '. venv/bin/activate && python3 -m pytest --maxfail=1 --disable-warnings -q'
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    docker.build("${DOCKER_IMAGE}:${VERSION}")
                }
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

        stage('Deploy Blue/Green') {
            steps {
                withCredentials([file(credentialsId: 'EKS_KUBECONFIG', variable: 'KUBECONFIG_FILE')]) {
                    sh '''
                    export KUBECONFIG=$KUBECONFIG_FILE
                    kubectl create ns fitness --dry-run=client -o yaml | kubectl apply -f -
                # Deploy Blue
                    sed "s|IMAGE_PLACEHOLDER|${DOCKER_IMAGE_NAME}:${DOCKER_IMAGE_TAG}|g; \
	                 s|VERSION_PLACEHOLDER|${VERSION}|g; \
                         s|DEPLOYMENT_NAME_PLACEHOLDER|${BLUE_DEPLOYMENT_NAME}|g" k8s-deploy/blue-deployment-template.yaml > blue-deployment.yaml
                    kubectl apply -f blue-deployment.yaml --validate=false
                    kubectl rollout status deployment/${BLUE_DEPLOYMENT_NAME} --timeout=120s
                            
                    # Deploy Green
                    sed "s|IMAGE_PLACEHOLDER|${DOCKER_IMAGE_NAME}:${DOCKER_IMAGE_TAG}|g; \
                         s|VERSION_PLACEHOLDER|${VERSION}|g; \
                         s|DEPLOYMENT_NAME_PLACEHOLDER|${GREEN_DEPLOYMENT_NAME}|g" k8s-deploy/green-deployment-template.yaml > green-deployment.yaml
                    kubectl apply -f green-deployment.yaml --validate=false
                    kubectl rollout status deployment/${GREEN_DEPLOYMENT_NAME} --timeout=120s
                    '''
                }
            }
        }

        stage('Deploy Shadow') {
            steps {
                withCredentials([file(credentialsId: 'EKS_KUBECONFIG', variable: 'KUBECONFIG_FILE')]) {
                    sh '''
                    export KUBECONFIG=$KUBECONFIG_FILE
                    sed "s|IMAGE_PLACEHOLDER|${DOCKER_IMAGE}:${VERSION}|g;
                         s|VERSION_PLACEHOLDER|${VERSION}|g;
                         s|DEPLOYMENT_NAME_PLACEHOLDER|fitness-app-shadow-${VERSION}|g" k8s-deploy/shadow-deployment-template.yaml > shadow-deployment.yaml
                    kubectl apply -f shadow-deployment.yaml --validate=false
                    kubectl rollout status deployment/fitness-app-shadow-${VERSION} --timeout=120s
                    '''
                }
            }
        }

        stage('Canary / A-B Testing') {
            steps {
                echo "Canary & A/B testing steps go here with dynamic versioning."
                // Replace placeholders like above for canary deployments
            }
        }
    }

    post {
        always {
            echo "Pipeline completed. Rollbacks or notifications can be handled here."
        }
        failure {
            echo "Pipeline failed. You can implement automatic rollback here."
        }
    }
}

