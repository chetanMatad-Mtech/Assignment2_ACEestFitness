pipeline {
    agent any
    environment {
        DOCKER_IMAGE_NAME = "chetanmatadmtech/fitness-app"
        DOCKER_IMAGE_TAG = "${BUILD_NUMBER}"
    }

    stages {
        stage('Checkout Code') {
            steps {
                echo "Checking out the repository..."
                git branch: 'develop',
                    url: 'https://github.com/chetanMatad-Mtech/Assignment2_ACEestFitness.git'
            }
        }

    stage('Setup Environment') {
        steps {
            echo 'Installing Python dependencies...'
            sh 'pip install -r requirements.txt'
            sh 'pip install pytest'
        }
    }

    stage('Run Tests') {
    steps {
        echo "Running Automated tests..."
        sh '''
            set -e
            python3 -m pytest --maxfail=1 --disable-warnings -q
        '''
    }
}

    stage('Build Docker Image') {
            steps {
                script {

                    def dockerfileDir = './Assignment2_ACEestFitness'

                    // Detect if Dockerfile is in current directory
                    if (fileExists('Dockerfile')) {
                        dockerfileDir = '.'
                    } else if (!fileExists("${dockerfileDir}/Dockerfile")) {
                        error " Dockerfile not found. Please check the folder path."
                    }

                    echo "Building Docker image from: ${dockerfileDir}"
                    sh "docker build -t ${DOCKER_IMAGE_NAME}:${DOCKER_IMAGE_TAG} ${dockerfileDir}"
                }
            }
        }

        stage('Push Docker Image') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'DOCKER_HUB_CREDENTIALS', 
                    usernameVariable: 'DOCKER_USER', 
                    passwordVariable: 'DOCKER_PASS'
                )]) {
                    sh '''
                        echo "$DOCKER_PASS" | docker login -u "$DOCKER_USER" --password-stdin
                        docker push ${DOCKER_IMAGE_NAME}:${DOCKER_IMAGE_TAG}
                    '''
                }
            }
        }
    }

    post {
        success {
            echo "Build and push completed successfully!"
        }
        failure {
            echo "Build failed. Please check the console output for details."
        }
    }
}

