pipeline {
    agent any
    environment {
        DOCKER_IMAGE = "chetanmatadmtech/fitness-app"
        DOCKER_TAG = "latest"
        K8S_NAMESPACE = "fitness"
        DEPLOY_STRATEGY = "rolling" // Options: rolling, blue-green, canary, shadow, ab
        AWS_REGION = "eu-north-1"
        EKS_CLUSTER = "fitness-eks"
        KUBECONFIG = "${env.HOME}/.kube/config"
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
                    sh '''
                        mkdir -p $HOME/.kube
                        aws eks update-kubeconfig --name ${EKS_CLUSTER} --region ${AWS_REGION} --kubeconfig $KUBECONFIG
                        kubectl config use-context arn:aws:eks:${AWS_REGION}:${AWS_ACCOUNT_ID}:cluster/${EKS_CLUSTER}
                    '''
                    script {
                        switch(env.DEPLOY_STRATEGY) {
                            case "rolling":
                                sh "kubectl apply -f k8s-deploy/rolling-deployment.yaml -n ${K8S_NAMESPACE}"
                                sh "kubectl rollout status deployment/fitness-app -n ${K8S_NAMESPACE}"
                                break

                            case "blue-green":
                                sh "kubectl apply -f k8s-deploy/blue.yaml -n ${K8S_NAMESPACE}"
                                sh "kubectl apply -f k8s-deploy/green.yaml -n ${K8S_NAMESPACE}"
                                sh "kubectl apply -f k8s-deploy/service-blue-green.yaml -n ${K8S_NAMESPACE}"
                                break

                            case "canary":
                                sh "kubectl apply -f k8s-deploy/canary.yaml -n ${K8S_NAMESPACE}"
                                echo "Canary deployment applied, monitor traffic gradually."
                                break

                            case "shadow":
                                sh "kubectl apply -f k8s-deploy/shadow.yaml -n ${K8S_NAMESPACE}"
                                echo "Shadow deployment applied, mirrored traffic only."
                                break

                            case "ab":
                                sh "kubectl apply -f k8s-deploy/service-ab.yaml -n ${K8S_NAMESPACE}"
                                echo "A/B testing enabled via Ingress routing."
                                break
                        }
                    }
                }
            }
        }
    }

    post {
        success {
            echo "Pipeline completed successfully using ${DEPLOY_STRATEGY} strategy!"
        }
        failure {
            echo "Pipeline failed! Rolling back..."
            script {
                switch(env.DEPLOY_STRATEGY) {
                    case "rolling":
                        sh "kubectl rollout undo deployment/fitness-app -n ${K8S_NAMESPACE}"
                        break
                    case "blue-green":
                        sh "kubectl apply -f k8s-deploy/service-blue.yaml -n ${K8S_NAMESPACE}"
                        break
                    case "canary":
                        sh "kubectl delete deployment fitness-app-canary -n ${K8S_NAMESPACE}"
                        break
                    case "shadow":
                        sh "kubectl delete deployment fitness-app-shadow -n ${K8S_NAMESPACE}"
                        break
                    case "ab":
                        sh "kubectl apply -f k8s-deploy/service-ab-stable.yaml -n ${K8S_NAMESPACE}"
                        break
                }
            }
        }
    }
}

