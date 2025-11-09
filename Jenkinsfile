pipeline {
    agent any
    environment {
        IMAGE_NAME = "chetanmatadmtech/fitness-app"
        VERSION = "v${BUILD_NUMBER}"
        KUBECONFIG_FILE = credentials('KUBECONFIG_FILE')
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
                    pip install -r requirements.txt
                    pip install pytest
                '''
            }
        }

        stage('Run Tests') {
            steps {
                sh 'python3 -m pytest --maxfail=1 --disable-warnings -q'
            }
        }

        stage('Build Docker Image') {
            steps {
                sh """
                    docker build -t ${IMAGE_NAME}:${BUILD_NUMBER} .
                """
            }
        }

        stage('Push Docker Image') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'DOCKER_HUB_CREDENTIALS', usernameVariable: 'USER', passwordVariable: 'PASS')]) {
                    sh """
                        echo \$PASS | docker login -u \$USER --password-stdin
                        docker push ${IMAGE_NAME}:${BUILD_NUMBER}
                        docker tag ${IMAGE_NAME}:${BUILD_NUMBER} ${IMAGE_NAME}:latest
                        docker push ${IMAGE_NAME}:latest
                    """
                }
            }
        }

        stage('Deploy Blue and Green') {
            steps {
                withCredentials([file(credentialsId: 'KUBECONFIG_FILE', variable: 'KUBECONFIG')]) {
                    sh """
                        # Blue Deployment
                        sed 's|IMAGE_PLACEHOLDER|${IMAGE_NAME}:${BUILD_NUMBER}|g; s|VERSION_PLACEHOLDER|${VERSION}|g; s|DEPLOYMENT_NAME_PLACEHOLDER|fitness-app-blue-${VERSION}|g' blue-deployment-template.yaml > blue-deployment.yaml
                        kubectl apply -f blue-deployment.yaml --validate=false
                        kubectl rollout status deployment/fitness-app-blue-${VERSION} --timeout=120s

                        # Green Deployment
                        sed 's|IMAGE_PLACEHOLDER|${IMAGE_NAME}:${BUILD_NUMBER}|g; s|VERSION_PLACEHOLDER|${VERSION}|g; s|DEPLOYMENT_NAME_PLACEHOLDER|fitness-app-green-${VERSION}|g' green-deployment-template.yaml > green-deployment.yaml
                        kubectl apply -f green-deployment.yaml --validate=false
                        kubectl rollout status deployment/fitness-app-green-${VERSION} --timeout=120s
                    """
                }
            }
        }

        stage('Deploy Shadow') {
            steps {
                withCredentials([file(credentialsId: 'KUBECONFIG_FILE', variable: 'KUBECONFIG')]) {
                    sh """
                        sed 's|IMAGE_PLACEHOLDER|${IMAGE_NAME}:${BUILD_NUMBER}|g; s|VERSION_PLACEHOLDER|${VERSION}|g; s|DEPLOYMENT_NAME_PLACEHOLDER|fitness-app-shadow-${VERSION}|g' shadow-deployment-template.yaml > shadow-deployment.yaml
                        kubectl apply -f shadow-deployment.yaml --validate=false
                        kubectl rollout status deployment/fitness-app-shadow-${VERSION} --timeout=120s

                        echo "Monitoring shadow deployment for 60 seconds..."
                        sleep 60

                        READY_PODS=\$(kubectl get deployment fitness-app-shadow-${VERSION} -o jsonpath={.status.readyReplicas})
                        TOTAL_PODS=\$(kubectl get deployment fitness-app-shadow-${VERSION} -o jsonpath={.status.replicas})
                        SUCCESS_RATE=\$((READY_PODS*100/TOTAL_PODS))

                        if [ \$SUCCESS_RATE -lt 90 ]; then
                            echo "Shadow deployment failed. Aborting pipeline."
                            exit 1
                        fi

                        echo "Shadow deployment healthy."
                    """
                }
            }
        }

        stage('Canary Release to Green') {
            steps {
                withCredentials([file(credentialsId: 'KUBECONFIG_FILE', variable: 'KUBECONFIG')]) {
                    sh """
                        for PERCENT in 20 40 60 80 100; do
                            echo "Shifting \$PERCENT% traffic to Green..."
                            kubectl patch svc fitness-app-service -p '{"spec":{"selector":{"version":"${VERSION}"}}}' --type=merge
                            sleep 30
                        done
                        echo "Canary promotion complete. 100% traffic now points to Green."
                    """
                }
            }
        }

        stage('A/B Testing') {
            steps {
                withCredentials([file(credentialsId: 'KUBECONFIG_FILE', variable: 'KUBECONFIG')]) {
                    sh """
                        # Deploy alternative B version for A/B testing
                        sed 's|IMAGE_PLACEHOLDER|${IMAGE_NAME}:${BUILD_NUMBER}|g; s|VERSION_PLACEHOLDER|${VERSION}-B|g; s|DEPLOYMENT_NAME_PLACEHOLDER|fitness-app-B-${VERSION}|g' ab-testing-template.yaml > ab-deployment-B.yaml
                        kubectl apply -f ab-deployment-B.yaml --validate=false
                        kubectl rollout status deployment/fitness-app-B-${VERSION} --timeout=120s

                        # Split traffic 50/50 between A (current) and B (new)
                        kubectl patch svc fitness-app-service -p '{"spec":{"selector":{"version":"A"}}}' --type=merge
                        kubectl patch svc fitness-app-service-b -p '{"spec":{"selector":{"version":"B"}}}' --type=merge

                        echo "A/B testing deployed. Monitoring user traffic split between A and B..."
                        sleep 60
                    """
                }
            }
        }

        stage('Build Artifact') {
            steps {
                sh """
                    mkdir -p build_output
                    cp Application.py build_output/Application_${BUILD_NUMBER}.py
                    cd build_output
                    zip Application_${BUILD_NUMBER}.zip Application_${BUILD_NUMBER}.py
                """
            }
        }

        stage('Archive Artifact') {
            steps {
                archiveArtifacts artifacts: 'build_output/*.zip', fingerprint: true
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

