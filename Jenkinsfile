pipeline {
    agent any

    environment {
        REGISTRY        = '192.168.188.18:5000'
        DOCKER_IMAGE    = "192.168.188.18:5000/etamusic"
        DOCKER_TAG      = "${BUILD_NUMBER}"
        DEPLOY_HOST     = '38.92.9.207'
        DEPLOY_USER     = 'root'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                sh 'git log --oneline -1'
            }
        }

        stage('Build Docker Image') {
            steps {
                sh "docker build -t ${DOCKER_IMAGE}:${DOCKER_TAG} -t ${DOCKER_IMAGE}:latest ."
            }
        }

        stage('Push to Registry') {
            steps {
                sh "docker push ${DOCKER_IMAGE}:${DOCKER_TAG}"
                sh "docker push ${DOCKER_IMAGE}:latest"
            }
        }

        stage('Deploy to Server') {
            steps {
                sshagent(credentials: ['deploy-ssh-key']) {
                    sh """
ssh -o StrictHostKeyChecking=no ${DEPLOY_USER}@${DEPLOY_HOST} \
  "docker pull ${DOCKER_IMAGE}:latest && \
   docker stop etamusic 2>/dev/null || true && \
   docker rm etamusic 2>/dev/null || true && \
   docker run -d \
     --name etamusic \
     --restart unless-stopped \
     -p 8000:8000 \
     -v etamusic-data:/app/backend/data \
     -e ETA_HOST=0.0.0.0 \
     -e ETA_PORT=8000 \
     -e ETA_SELF_URL=http://${DEPLOY_HOST}:8000 \
     ${DOCKER_IMAGE}:latest"
                    """
                }
            }
        }
    }

    post {
        success {
            echo "部署成功！访问地址: http://${DEPLOY_HOST}:8000"
        }
        failure {
            echo '部署失败，请检查 Jenkins 日志'
        }
        always {
            sh "docker rmi ${DOCKER_IMAGE}:${DOCKER_TAG} 2>/dev/null || true"
            cleanWs()
        }
    }
}
