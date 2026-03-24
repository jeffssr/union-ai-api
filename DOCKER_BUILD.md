# Union AI API - Docker 镜像构建和发布指南

## 🐳 构建 Docker 镜像

### 本地构建

```bash
# 构建镜像
docker build -f Dockerfile.clean -t union-ai-api:latest .

# 或带标签构建
docker build -f Dockerfile.clean -t yourusername/union-ai-api:latest .
```

### 测试镜像

```bash
# 运行容器
docker run -d -p 18080:8000 -p 18501:8501 \
  -v $(pwd)/data:/app/data \
  --name union-ai-api-test \
  union-ai-api:latest

# 查看日志
docker logs -f union-ai-api-test

# 停止并删除
docker stop union-ai-api-test
docker rm union-ai-api-test
```

## 📤 推送到 Docker Hub

### 1. 登录 Docker Hub

```bash
docker login
# 输入你的 Docker Hub 用户名和密码
```

### 2. 标记镜像

```bash
# 替换为你的 Docker Hub 用户名
docker tag union-ai-api:latest yourusername/union-ai-api:latest
```

### 3. 推送镜像

```bash
docker push yourusername/union-ai-api:latest
```

## 🔄 使用 GitHub Actions 自动构建

### 工作流程

1. 推送到 GitHub 后自动构建
2. 自动推送到 Docker Hub
3. 自动生成版本标签

### 配置步骤

1. 在 GitHub 仓库创建 Secrets：
   - `DOCKERHUB_USERNAME`: Docker Hub 用户名
   - `DOCKERHUB_TOKEN`: Docker Hub 访问令牌

2. 创建 `.github/workflows/docker-build.yml`

3. 推送代码触发自动构建

## 📋 使用 Docker 镜像

### 方式一：Docker 命令

```bash
docker run -d \
  -p 18080:8000 \
  -p 18501:8501 \
  -v $(pwd)/data:/app/data \
  --name union-ai-api \
  yourusername/union-ai-api:latest
```

### 方式二：Docker Compose

```yaml
version: '3'
services:
  union-ai-api:
    image: yourusername/union-ai-api:latest
    container_name: union-ai-api
    ports:
      - "18080:8000"
      - "18501:8501"
    volumes:
      - ./data:/app/data
    restart: unless-stopped
```

## 🏷️ 版本管理

```bash
# 构建特定版本
docker build -f Dockerfile.clean -t yourusername/union-ai-api:v1.0.0 .

# 推送多个标签
docker tag yourusername/union-ai-api:v1.0.0 yourusername/union-ai-api:latest
docker push yourusername/union-ai-api:v1.0.0
docker push yourusername/union-ai-api:latest
```

## 🔍 验证镜像

```bash
# 拉取镜像
docker pull yourusername/union-ai-api:latest

# 查看镜像信息
docker inspect yourusername/union-ai-api:latest

# 运行健康检查
docker run --rm yourusername/union-ai-api:latest curl http://localhost:8000/health
```
