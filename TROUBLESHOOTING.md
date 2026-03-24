# 🔧 Docker Hub 自动构建故障排除

## ❌ 问题原因

GitHub Actions 失败的原因：
- **Docker 镜像名称不正确**
- 之前使用：`union-ai-api`
- 应该使用：`jeffssr/union-ai-api`（包含 Docker Hub 用户名）

## ✅ 已修复

**修改内容**：
```yaml
# 之前
env:
  DOCKER_IMAGE: union-ai-api

# 现在
env:
  DOCKER_IMAGE: jeffssr/union-ai-api
```

**文件位置**：`.github/workflows/docker-build.yml`

---

## 📊 验证步骤

### 1. 查看 GitHub Actions 状态

访问：https://github.com/jeffssr/union-ai-api/actions

**应该看到**：
- 最新的 commit：`fix: update Docker image name to jeffssr/union-ai-api`
- 状态：✅ 成功（绿色勾）

### 2. 查看 Docker Hub

访问：https://hub.docker.com/r/jeffssr/union-ai-api

**应该看到**：
- 镜像仓库已创建
- 标签：`latest`, `v1.0.0` 等
- 构建时间：最近

### 3. 测试拉取镜像

```bash
docker pull jeffssr/union-ai-api:latest
```

---

## 🎯 如果仍然失败

### 检查 GitHub Secrets

1. 访问：https://github.com/jeffssr/union-ai-api/settings/secrets/actions
2. 确认以下 Secrets 存在：
   - `DOCKERHUB_USERNAME` = `jeffssr`
   - `DOCKERHUB_TOKEN` = （有效的 Token）

### 重新生成 Docker Hub Token

1. 登录 Docker Hub：https://hub.docker.com/
2. 头像 → **Account Settings**
3. **Security** → **New Access Token**
4. 生成新 Token
5. 更新 GitHub Secrets

### 查看构建日志

1. GitHub Actions → 点击失败的构建
2. 查看错误信息
3. 常见错误：
   - `unauthorized: authentication required` → Secrets 配置错误
   - `denied: requested access to the resource is denied` → Token 权限不足
   - `manifest unknown: manifest unknown` → 镜像未构建成功

---

## 📝 完整的 Docker Hub 配置流程

### 步骤 1：创建 Docker Hub 仓库

**自动创建**：
- GitHub Actions 第一次推送时会自动创建

**手动创建**（可选）：
1. 登录 Docker Hub
2. 点击 **Create repository**
3. 名称：`union-ai-api`
4. 可见性：**Public**

### 步骤 2：配置 GitHub Secrets

```
Settings → Secrets and variables → Actions

添加：
- DOCKERHUB_USERNAME: jeffssr
- DOCKERHUB_TOKEN: [你的 Token]
```

### 步骤 3：触发构建

```bash
# 推送代码触发
git push origin main

# 或推送标签触发
git tag v1.0.0
git push origin v1.0.0
```

### 步骤 4：验证

```bash
# 查看 Actions 状态
https://github.com/jeffssr/union-ai-api/actions

# 查看 Docker Hub
https://hub.docker.com/r/jeffssr/union-ai-api
```

---

## 🎉 成功标志

**GitHub Actions**：
- ✅ 绿色勾
- 构建时间：~2-5 分钟
- 输出包含：`Pushed jeffssr/union-ai-api:latest`

**Docker Hub**：
- 镜像仓库存在
- 标签列表显示 `latest`, `v1.0.0` 等
- 拉取次数 > 0

**本地测试**：
```bash
docker pull jeffssr/union-ai-api:latest
# 成功拉取
```

---

## 📞 需要帮助？

**提供以下信息**：
1. GitHub Actions 构建日志链接
2. Docker Hub 仓库链接
3. 错误信息截图

**常见问题**：
- Q: Docker Hub 404？
  - A: 镜像还未构建成功，等待 Actions 完成
- Q: 认证失败？
  - A: 检查 Secrets 配置，重新生成 Token
- Q: 构建时间长？
  - A: 第一次构建需要 5-10 分钟，后续会使用缓存

---

**🎊 修复已推送，等待构建完成！**
