pipeline {
    agent any

    environment {
        AWS_REGION = 'eu-north-1'
        EKS_CLUSTER = 'fitness-eks'
        K8S_NAMESPACE = 'fitness'
        DOCKER_IMAGE = 'chetanmatadmtech/fitness-app:latest'
        KUBECONFIG = '/var/lib/jenkins/.kube/config'
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
                sh "docker build -t ${DOCKER_IMAGE} ."
            }
        }

        stage('Push Docker Image') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'DOCKER_HUB_CREDENTIALS', 
                                                 usernameVariable: 'DOCKER_USER', 
                                                 passwordVariable: 'DOCKER_PASS')]) {
                    sh '''
                        echo $DOCKER_PASS | docker login -u $DOCKER_USER --password-stdin
                        docker push ${DOCKER_IMAGE}
                    '''
                }
            }
        }

        stage('Deploy to EKS') {
            steps {
                withAWS(region: "${AWS_REGION}", credentials: 'aws-eks-credentials') {
                    sh '''
                        # Ensure kubeconfig exists and is accessible
                        mkdir -p $(dirname $KUBECONFIG)
                        aws eks update-kubeconfig --name ${EKS_CLUSTER} --region ${AWS_REGION} --kubeconfig $KUBECONFIG
                        chmod 600 $KUBECONFIG

                        # Ensure namespace exists
                        kubectl create ns ${K8S_NAMESPACE} --dry-run=client -o yaml | kubectl apply -f -

                        # Deploy application
                        kubectl apply -f k8s-deploy/rolling-deployment.yaml -n ${K8S_NAMESPACE} --validate=false
                    '''
                }
            }
        }
    }

    post {
        failure {
            script {
                withAWS(region: "${AWS_REGION}", credentials: 'aws-eks-credentials') {
                    sh '''
                        export KUBECONFIG=/var/lib/jenkins/.kube/config
                        # Rollback deployment if exists
                        kubectl rollout undo deployment/fitness-app -n ${K8S_NAMESPACE} || echo "No previous deployment to rollback"
                    '''
                }
            }
            echo "Pipeline failed! Rolled back if needed."
        }
    }
}

