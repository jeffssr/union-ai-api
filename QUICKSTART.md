# Union AI API - 快速入门

## 🚀 立即开始使用

### 前提条件

确保已安装 **Docker Desktop**：
- [macOS 下载](https://docs.docker.com/desktop/install/mac-install/)
- [Windows 下载](https://docs.docker.com/desktop/install/windows-install/)
- [Linux 下载](https://docs.docker.com/desktop/install/linux-install/)

### 快速启动（3 步）

#### 1️⃣ 启动服务

```bash
cd /path/to/union-ai-api
./start.sh
```

#### 2️⃣ 访问管理后台

打开浏览器访问：**http://localhost:18501**

#### 3️⃣ 配置模型和 API Key

- 在「模型配置」添加你的 AI 模型
- 在「API Key」生成访问密钥
- 开始使用 API 服务

---

## 📋 常用命令

```bash
# 启动服务
./start.sh

# 查看状态
./status.sh

# 停止服务
./stop.sh

# 重启服务
./restart.sh

# 查看日志
docker logs -f union-ai-api

# 图形化启动器
python3 launcher.py
```

---

## 🌐 访问地址

- **API 服务**: http://localhost:18080
- **管理后台**: http://localhost:18501

## 🔌 客户端配置

### 通用 OpenAI 客户端
```
Base URL: http://localhost:18080/v1
API Key: 从管理后台生成的 Key
```

### Codex / OpenAI SDK v1.60+
```bash
export OPENAI_BASE_URL="http://localhost:18080"
export OPENAI_API_KEY="your-api-key-from-web-ui"
```

---

## 📂 数据存储

所有数据存储在：`./data`（项目文件夹内）

包含：
- ✅ 数据库文件
- ✅ 模型配置
- ✅ API Key
- ✅ 调用日志

**重要**: 
- `data` 目录已被 `.gitignore` 排除，不会被 Git 跟踪
- 删除项目时，请备份此目录！

---

## ❓ 遇到问题？

### Docker 未运行
```bash
# 启动 Docker Desktop 应用
```

### 端口被占用
```bash
# 检查端口占用
lsof -i :18080
lsof -i :18501

# 停止占用端口的进程
kill -9 <PID>
```

### 权限错误
```bash
# 赋予执行权限
chmod +x *.sh
```

---

## 📖 详细文档

查看 [README_DEPLOYMENT.md](README_DEPLOYMENT.md) 获取完整安装说明和故障排除指南。

---

**🎉 开始使用吧！**
