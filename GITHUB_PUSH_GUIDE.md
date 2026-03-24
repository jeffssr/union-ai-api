# 🚀 推送到 GitHub 完整指南

## 📋 已完成的工作

✅ 初始化 Git 仓库
✅ 创建 `.gitignore`（排除 data 目录）
✅ 创建 MIT 许可证
✅ 创建免责声明
✅ 创建 README.md
✅ 创建 GitHub Actions 工作流
✅ 提交所有代码

## 🎯 推送到 GitHub 的步骤

### 步骤 1：在 GitHub 上创建仓库

1. 访问 [GitHub](https://github.com)
2. 点击右上角 "+" → "New repository"
3. 填写信息：
   - **Repository name**: `union-ai-api`
   - **Description**: "统一的多模型 AI 代理 API 服务"
   - **Public**: ✅ (公开仓库)
   - **Initialize this repository with a README**: ❌ (不要勾选)
4. 点击 "Create repository"

### 步骤 2：推送代码到 GitHub

```bash
# 添加远程仓库（替换为你的 GitHub 用户名）
git remote add origin https://github.com/YOUR_USERNAME/union-ai-api.git

# 推送到 GitHub
git branch -M main
git push -u origin main
```

### 步骤 3：验证推送

```bash
# 查看远程仓库
git remote -v

# 查看提交历史
git log --oneline
```

## 🐳 配置 Docker Hub 自动构建

### 1. 创建 Docker Hub 账号

访问：[Docker Hub](https://hub.docker.com/)

### 2. 在 GitHub 添加 Secrets

1. 进入 GitHub 仓库
2. 点击 "Settings" → "Secrets and variables" → "Actions"
3. 点击 "New repository secret"
4. 添加以下 Secrets：

```
Name: DOCKERHUB_USERNAME
Value: 你的 Docker Hub 用户名

Name: DOCKERHUB_TOKEN
Value: 你的 Docker Hub 访问令牌
```

**获取 Docker Hub Token**：
- 登录 Docker Hub
- Account Settings → Security → New Access Token
- 权限：Read, Write, Delete

### 3. 触发自动构建

```bash
# 打标签触发构建
git tag v1.0.0
git push origin v1.0.0

# 或推送到 main 分支
git push origin main
```

## 📦 用户如何使用

### 方式一：从 GitHub 克隆

```bash
# 克隆仓库
git clone https://github.com/YOUR_USERNAME/union-ai-api.git
cd union-ai-api

# 启动服务
chmod +x start.sh
./start.sh

# 访问管理后台
# http://localhost:18501
```

### 方式二：使用 Docker 镜像

```bash
# 拉取镜像
docker pull YOUR_DOCKERHUB_USERNAME/union-ai-api:latest

# 运行容器
docker run -d \
  -p 18080:8000 \
  -p 18501:8501 \
  -v $(pwd)/data:/app/data \
  --name union-ai-api \
  YOUR_DOCKERHUB_USERNAME/union-ai-api:latest
```

### 方式三：使用 Docker Compose

```bash
# 克隆仓库
git clone https://github.com/YOUR_USERNAME/union-ai-api.git
cd union-ai-api

# 启动服务
docker-compose -f docker-compose.clean.yml up -d
```

## 🔄 更新代码

### 推送更新

```bash
# 提交更改
git add .
git commit -m "描述你的更新"
git push origin main

# 发布新版本
git tag v1.1.0
git push origin v1.1.0
```

### 自动构建新版本

推送标签后，GitHub Actions 会自动：
1. 构建新的 Docker 镜像
2. 推送到 Docker Hub（标签：v1.1.0）
3. 更新 latest 标签

## 📊 查看构建状态

### GitHub Actions

访问：`https://github.com/YOUR_USERNAME/union-ai-api/actions`

### Docker Hub

访问：`https://hub.docker.com/r/YOUR_USERNAME/union-ai-api`

## 🛡️ 安全建议

### 1. 保护 main 分支

在 GitHub 仓库设置中：
- Settings → Branches → Add branch protection rule
- Branch name pattern: `main`
- 勾选：
  - ✅ Require a pull request before merging
  - ✅ Require status checks to pass before merging

### 2. 定期更新依赖

```bash
# 检查依赖更新
pip list --outdated

# 更新 requirements.txt
pipreqs . --force
```

### 3. 监控 Docker 镜像漏洞

使用 Docker Hub 的自动漏洞扫描功能

## 📝 检查清单

推送前请确认：

- [ ] 已创建 GitHub 账号
- [ ] 已创建 Docker Hub 账号
- [ ] 已创建 GitHub 仓库
- [ ] 已添加远程仓库
- [ ] 代码已成功推送
- [ ] 已配置 GitHub Secrets
- [ ] Docker 镜像已自动构建
- [ ] README 中的链接已更新

## 🎉 完成！

现在你的项目已经：
- ✅ 开源在 GitHub
- ✅ 自动构建 Docker 镜像
- ✅ 用户可以直接克隆使用
- ✅ 用户可以使用 Docker 镜像

## 📞 常见问题

### Q: 推送失败怎么办？

```bash
# 检查远程仓库配置
git remote -v

# 重新添加远程仓库
git remote remove origin
git remote add origin https://github.com/YOUR_USERNAME/union-ai-api.git

# 再次推送
git push -u origin main
```

### Q: Docker 构建失败？

1. 检查 GitHub Secrets 是否正确配置
2. 查看 Actions 标签页的错误日志
3. 确保 Dockerfile.clean 没有语法错误

### Q: 如何删除敏感数据？

```bash
# 如果不小心提交了敏感文件
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch PATH_TO_FILE" \
  --prune-empty --tag-name-filter cat -- --all

git push origin --force --all
```

---

**🎊 恭喜！你的项目已成功开源！**
