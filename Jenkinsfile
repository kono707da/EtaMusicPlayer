pipeline {
    agent any

    environment {
        IMAGE_NAME    = 'etamusic'
        REGISTRY      = credentials('docker-registry-url')
        IMAGE_TAG     = "${REGISTRY}/${IMAGE_NAME}:${BUILD_NUMBER}"
        IMAGE_LATEST  = "${REGISTRY}/${IMAGE_NAME}:latest"
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                sh 'git log --oneline -1'
            }
        }

        stage('Build Image') {
            steps {
                // 诊断 docker 环境（重装 Jenkins 后确认版本和 buildx 是否可用）
                sh 'docker version || true'
                sh 'docker buildx version 2>/dev/null || echo "buildx not installed"'
                // 清理旧镜像，避免 tag 指向残留的 manifest list
                sh "docker rmi ${IMAGE_NAME} ${IMAGE_TAG} ${IMAGE_LATEST} 2>/dev/null || true"
                // 内联 DOCKER_BUILDKIT=0 强制禁用 BuildKit，用经典 builder 生成普通 manifest（非 manifest list）
                // --no-cache 避免命中旧的前端构建层缓存导致部署旧版本前端代码
                sh "DOCKER_BUILDKIT=0 docker build --no-cache -t ${IMAGE_NAME} -t ${IMAGE_TAG} -t ${IMAGE_LATEST} ."
            }
        }

        stage('Push to Registry') {
            steps {
                sh "docker push ${IMAGE_TAG}"
                sh "docker push ${IMAGE_LATEST}"
            }
        }

        stage('Deploy to Server') {
            steps {
                sshPublisher(publishers: [
                    sshPublisherDesc(
                        configName: 'hongkong',
                        transfers: [
                            sshTransfer(
                                execCommand: "docker pull ${IMAGE_LATEST} && (docker stop etamusic 2>/dev/null || true) && (docker rm etamusic 2>/dev/null || true) && docker run -d --name etamusic --restart unless-stopped -p 8000:8000 -v etamusic-web-data:/app/web/backend/data -v etamusic-node:/app/node -v etamusic-plugins:/app/plugins -v etamusic-data:/app/data -v etamusic-deps:/app/deps -e TZ=Asia/Shanghai ${IMAGE_LATEST}"
                            )
                        ]
                    )
                ])
            }
        }
    }

    post {
        success {
            echo '部署成功！'
        }
        failure {
            echo '部署失败，请检查 Jenkins 日志'
        }
        always {
            sh "docker rmi ${IMAGE_TAG} ${IMAGE_LATEST} ${IMAGE_NAME} 2>/dev/null || true"
            cleanWs()
        }
    }
}
