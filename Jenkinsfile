pipeline {
    agent any
    environment {
        DOCKER_IMAGE = "chetanmatadmtech/fitness-app"
        DOCKER_TAG = "latest"
        K8S_NAMESPACE = "fitness"
        DEPLOY_STRATEGY = "rolling" // Options: rolling, blue-green, canary, shadow, ab
        AWS_REGION = "eu-north-1"
        EKS_CLUSTER = "fitness-eks"
    }

    stages {
        stage('Checkout SCM') {
            steps {
                git branch: 'develop',
                    url: 'https://github.com/chetanMatad-Mtech/Assignment2_ACEestFitness.git',
                    credentialsId: 'DOCKER_HUB_CREDENTIALS'
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
                sh '''
                    . venv/bin/activate
                    pytest
                '''
            }
        }

        stage('Build Docker Image') {
            steps {
                sh "docker build -t ${DOCKER_IMAGE}:${DOCKER_TAG} ."
            }
        }

        stage('Push Docker Image') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'DOCKER_HUB_CREDENTIALS', usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
                    sh '''
                        echo $DOCKER_PASS | docker login -u $DOCKER_USER --password-stdin
                        docker push ${DOCKER_IMAGE}:${DOCKER_TAG}
                    '''
                }
            }
        }

        stage('Deploy to EKS') {
            steps {
                withAWS(region: "${AWS_REGION}", credentials: 'aws-eks-credentials') {
                    sh "aws eks update-kubeconfig --name ${EKS_CLUSTER} --region ${AWS_REGION}"

                    script {
                        switch(env.DEPLOY_STRATEGY) {
                            case "rolling":
                                sh "kubectl apply -f k8s-deploy/rolling-deployment.yaml -n ${K8S_NAMESPACE}"
                                sh "kubectl rollout status deployment/fitness-app -n ${K8S_NAMESPACE}"
                                break

                            case "blue-green":
                                sh "kubectl apply -f k8s-deploy/blue-deployment.yaml -n ${K8S_NAMESPACE}"
                                sh "kubectl apply -f k8s-deploy/green-deployment.yaml -n ${K8S_NAMESPACE}"
                                sh "kubectl apply -f k8s-deploy/service-blue-green.yaml -n ${K8S_NAMESPACE}"
                                break

                            case "canary":
                                sh "kubectl apply -f k8s-deploy/canary-deployment.yaml -n ${K8S_NAMESPACE}"
                                echo "Canary deployment applied. Gradually scale canary pods to test new version."
                                break

                            case "shadow":
                                sh "kubectl apply -f k8s-deploy/shadow-deployment.yaml -n ${K8S_NAMESPACE}"
                                echo "Shadow deployment applied. Traffic is mirrored only for testing."
                                break

                            case "ab":
                                sh "kubectl apply -f k8s-deploy/ab-deployment.yaml -n ${K8S_NAMESPACE}"
                                sh "kubectl apply -f k8s-deploy/service-ab.yaml -n ${K8S_NAMESPACE}"
                                echo "A/B testing deployment applied. Use Ingress or ALB for traffic splitting."
                                break

                            default:
                                error "Unknown DEPLOY_STRATEGY: ${DEPLOY_STRATEGY}"
                        }
                    }
                }
            }
        }
    }

    post {
        success {
            echo "Pipeline completed successfully and deployed using ${DEPLOY_STRATEGY} strategy!"
        }
        failure {
            echo "Pipeline failed! Rolling back..."
            script {
                switch(env.DEPLOY_STRATEGY) {
                    case "rolling":
                        sh "kubectl rollout undo deployment/fitness-app -n ${K8S_NAMESPACE}"
                        break
                    case "blue-green":
                        sh "kubectl apply -f k8s-deploy/service-blue.yaml -n ${K8S_NAMESPACE}" // rollback to blue
                        break
                    case "canary":
                        sh "kubectl delete deployment fitness-app-canary -n ${K8S_NAMESPACE}"
                        break
                    case "shadow":
                        sh "kubectl delete deployment fitness-app-shadow -n ${K8S_NAMESPACE}"
                        break
                    case "ab":
                        sh "kubectl apply -f k8s-deploy/service-a.yaml -n ${K8S_NAMESPACE}" // rollback to stable
                        break
                }
            }
        }
    }
}

