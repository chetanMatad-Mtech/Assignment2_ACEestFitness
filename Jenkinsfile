pipeline {
    agent any
    environment {
        DOCKER_HUB_CREDENTIALS = credentials('DOCKER_HUB_CREDENTIALS')
        KUBECONFIG_FILE = credentials('KUBECONFIG_FILE')
        IMAGE_NAME = "chetanmatadmtech/fitness-app"
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
                script {
                    sh """
                        docker build -t $IMAGE_NAME:${BUILD_NUMBER} .
                    """
                }
            }
        }

        stage('Push Docker Image') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'DOCKER_HUB_CREDENTIALS', passwordVariable: 'DOCKER_PASS', usernameVariable: 'DOCKER_USER')]) {
                    sh """
                        echo $DOCKER_PASS | docker login -u $DOCKER_USER --password-stdin
                        docker push $IMAGE_NAME:${BUILD_NUMBER}
                        docker tag $IMAGE_NAME:${BUILD_NUMBER} $IMAGE_NAME:latest
                        docker push $IMAGE_NAME:latest
                    """
                }
            }
        }

        stage('Blue/Green Deployment') {
            steps {
                withCredentials([file(credentialsId: 'KUBECONFIG_FILE', variable: 'KUBECONFIG')]) {
                    sh """
                        export KUBECONFIG=$KUBECONFIG_FILE
                        
                        # Blue Deployment
                        sed 's|IMAGE_PLACEHOLDER|$IMAGE_NAME:${BUILD_NUMBER}|g; s|VERSION_PLACEHOLDER|${VERSION}|g; s|DEPLOYMENT_NAME_PLACEHOLDER|fitness-app-blue-${VERSION}|g' blue-deployment-template.yaml > blue-deployment.yaml
                        kubectl apply -f blue-deployment.yaml --validate=false
                        kubectl rollout status deployment/fitness-app-blue-${VERSION} --timeout=120s

                        # Green Deployment
                        sed 's|IMAGE_PLACEHOLDER|$IMAGE_NAME:${BUILD_NUMBER}|g; s|VERSION_PLACEHOLDER|${VERSION}|g; s|DEPLOYMENT_NAME_PLACEHOLDER|fitness-app-green-${VERSION}|g' green-deployment-template.yaml > green-deployment.yaml
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
                        export KUBECONFIG=$KUBECONFIG_FILE
                        sed 's|IMAGE_PLACEHOLDER|$IMAGE_NAME:${BUILD_NUMBER}|g; s|VERSION_PLACEHOLDER|${VERSION}|g; s|DEPLOYMENT_NAME_PLACEHOLDER|fitness-app-shadow-${VERSION}|g' shadow-deployment-template.yaml > shadow-deployment.yaml
                        kubectl apply -f shadow-deployment.yaml --validate=false
                        kubectl rollout status deployment/fitness-app-shadow-${VERSION} --timeout=120s
                        
                        echo "Monitoring shadow deployment for 60 seconds..."
                        sleep 60
                        
                        READY_PODS=$(kubectl get deployment fitness-app-shadow-${VERSION} -o jsonpath={.status.readyReplicas})
                        TOTAL_PODS=$(kubectl get deployment fitness-app-shadow-${VERSION} -o jsonpath={.status.replicas})
                        SUCCESS_RATE=$((READY_PODS*100/TOTAL_PODS))
                        
                        if [ $SUCCESS_RATE -lt 90 ]; then
                            echo "Shadow deployment failed. Aborting pipeline."
                            exit 1
                        fi
                        
                        echo "Shadow deployment healthy."
                    """
                }
            }
        }

        stage('A/B Testing') {
            steps {
                withCredentials([file(credentialsId: 'KUBECONFIG_FILE', variable: 'KUBECONFIG')]) {
                    sh """
                        export KUBECONFIG=$KUBECONFIG_FILE

                        # Deploy version A
                        sed 's|IMAGE_PLACEHOLDER|$IMAGE_NAME:${BUILD_NUMBER}|g; s|DEPLOYMENT_NAME_PLACEHOLDER|fitness-app-A|g' deployment-A-template.yaml | kubectl apply -f -
                        kubectl rollout status deployment/fitness-app-A --timeout=120s

                        # Deploy version B
                        sed 's|IMAGE_PLACEHOLDER|$IMAGE_NAME:${BUILD_NUMBER}|g; s|DEPLOYMENT_NAME_PLACEHOLDER|fitness-app-B|g' deployment-B-template.yaml | kubectl apply -f -
                        kubectl rollout status deployment/fitness-app-B --timeout=120s

                        # Apply Istio VirtualService for 50/50 split
                        kubectl apply -f virtualservice-ab.yaml
                    """
                }
            }
        }

        stage('Canary Promotion') {
            steps {
                withCredentials([file(credentialsId: 'KUBECONFIG_FILE', variable: 'KUBECONFIG')]) {
                    sh """
                        export KUBECONFIG=$KUBECONFIG_FILE
                        echo "Starting gradual traffic shift to Version B..."
                        
                        for PERCENT in 20 40 60 80 100; do
                            echo "Shifting \$PERCENT% traffic to Version B..."
                            kubectl patch svc fitness-app-service -p '{"spec":{"selector":{"version":"vB"}}}' --type=merge
                            sleep 30
                        done
                        
                        echo "Canary promotion complete. 100% traffic now points to Version B."
                    """
                }
            }
        }

        stage('Build Artifact') {
            steps {
                sh """
                    mkdir -p build_output
                    cp Application.py build_output/Application_${VERSION}.py
                    cd build_output
                    zip Application_${VERSION}.zip Application_${VERSION}.py
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

