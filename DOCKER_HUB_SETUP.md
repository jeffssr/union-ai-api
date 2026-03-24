# 🐳 Docker Hub 自动构建配置完成

## ✅ 已完成的配置

### 1. GitHub Secrets
- ✅ `DOCKERHUB_USERNAME` - Docker Hub 用户名
- ✅ `DOCKERHUB_TOKEN` - Docker Hub 访问令牌

### 2. GitHub Actions 工作流
- ✅ `.github/workflows/docker-build.yml` - 自动构建配置
- ✅ 支持分支推送自动构建
- ✅ 支持标签推送自动构建
- ✅ 自动语义化版本标签

### 3. 版本标签
- ✅ `v1.0.0` - 第一个正式版本

---

## 🚀 触发自动构建

### 方式一：推送标签（推荐）

```bash
# 推送标签触发构建
git tag v1.0.0
git push origin v1.0.0
```

### 方式二：推送到 main 分支

```bash
# 推送代码到 main 分支也会触发构建
git push origin main
```

---

## 📊 查看构建状态

### GitHub Actions

访问：https://github.com/jeffssr/union-ai-api/actions

**查看内容**：
- 构建状态（运行中/成功/失败）
- 构建日志
- 构建时间

### Docker Hub

访问：https://hub.docker.com/r/jeffssr/union-ai-api

**查看内容**：
- 镜像标签
- 构建历史
- 镜像大小
- 拉取次数

---

## 🏷️ 自动生成的标签

GitHub Actions 会自动生成以下标签：

| 标签 | 说明 | 示例 |
|------|------|------|
| `latest` | 最新版本 | `jeffssr/union-ai-api:latest` |
| `v{version}` | 语义化版本 | `jeffssr/union-ai-api:v1.0.0` |
| `v{major}.{minor}` | 主版本。次版本 | `jeffssr/union-ai-api:v1.0` |
| `sha-{short}` | Git commit SHA | `jeffssr/union-ai-api:sha-e27f288` |

---

## 📦 使用 Docker 镜像

### 拉取镜像

```bash
# 拉取最新版本
docker pull jeffssr/union-ai-api:latest

# 或拉取特定版本
docker pull jeffssr/union-ai-api:v1.0.0
```

### 运行容器

```bash
docker run -d \
  -p 18080:8000 \
  -p 18501:8501 \
  -v $(pwd)/data:/app/data \
  --name union-ai-api \
  jeffssr/union-ai-api:latest
```

### Docker Compose

```yaml
version: '3'
services:
  union-ai-api:
    image: jeffssr/union-ai-api:latest
    container_name: union-ai-api
    ports:
      - "18080:8000"
      - "18501:8501"
    volumes:
      - ./data:/app/data
    restart: unless-stopped
```

---

## 🔄 更新镜像

### 发布新版本

```bash
# 1. 修改代码
# 2. 提交更改
git add .
git commit -m "feat: 添加新功能"

# 3. 推送代码
git push origin main

# 4. 打上新标签
git tag v1.1.0
git push origin v1.1.0
```

### 用户更新

```bash
# 拉取最新镜像
docker pull jeffssr/union-ai-api:latest

# 停止旧容器
docker stop union-ai-api
docker rm union-ai-api

# 启动新容器
docker run -d \
  -p 18080:8000 \
  -p 18501:8501 \
  -v $(pwd)/data:/app/data \
  --name union-ai-api \
  jeffssr/union-ai-api:latest
```

---

## 🔍 故障排除

### 构建失败

**检查 GitHub Secrets**：
```
Settings → Secrets and variables → Actions
```

确认：
- ✅ `DOCKERHUB_USERNAME` 正确
- ✅ `DOCKERHUB_TOKEN` 有效

**查看构建日志**：
```
Actions → Docker Build and Push → 查看日志
```

### 镜像拉取失败

```bash
# 检查镜像是否存在
docker pull jeffssr/union-ai-api:latest

# 如果失败，检查：
# 1. Docker Hub 用户名是否正确
# 2. 镜像是否已推送成功
# 3. 网络连接是否正常
```

### 容器启动失败

```bash
# 查看容器日志
docker logs union-ai-api

# 检查端口占用
lsof -i :18080
lsof -i :18501

# 检查数据目录权限
ls -la data/
```

---

## 📝 添加 Docker badge 到 README

现在可以添加 Docker badge 到 README.md：

```markdown
[![Docker Build](https://img.shields.io/docker/build/jeffssr/union-ai-api?style=flat-square)](https://hub.docker.com/r/jeffssr/union-ai-api)
```

位置：`README.md` 第 5-7 行

完整示例：
```markdown
<p align="center">

[![Docker Build](https://img.shields.io/docker/build/jeffssr/union-ai-api?style=flat-square)](https://hub.docker.com/r/jeffssr/union-ai-api)
[![Python Version](https://img.shields.io/badge/python-3.11+-blue?style=flat-square)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)](LICENSE)
[![GitHub Stars](https://img.shields.io/github/stars/jeffssr/union-ai-api?style=flat-square)](https://github.com/jeffssr/union-ai-api/stargazers)

</p>
```

---

## 🎉 完成！

现在你的项目已经：
- ✅ 自动构建 Docker 镜像
- ✅ 自动推送到 Docker Hub
- ✅ 支持语义化版本管理
- ✅ 用户可以轻松拉取使用

**下一步**：
1. 查看 GitHub Actions 构建状态
2. 确认 Docker Hub 镜像已生成
3. 添加 Docker badge 到 README
4. 分享给用户使用！

---

**🎊 恭喜！Docker Hub 自动构建已配置完成！**
