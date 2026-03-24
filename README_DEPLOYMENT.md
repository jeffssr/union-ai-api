# Union AI API - 开箱即用部署指南

🚀 **Union AI API** 是一个统一的多模型 AI 代理服务，支持 FastAPI 后端和 Streamlit 管理后台。

---

## 📋 目录

- [快速开始](#快速开始)
- [系统要求](#系统要求)
- [安装步骤](#安装步骤)
- [使用方法](#使用方法)
- [常见问题](#常见问题)
- [文件说明](#文件说明)

---

## 🎯 快速开始

### 方式一：命令行启动（推荐）

```bash
# 1. 赋予执行权限
chmod +x start.sh

# 2. 一键启动
./start.sh
```

### 方式二：图形界面启动

```bash
# 启动图形化启动器
python3 launcher.py
```

---

## 💻 系统要求

### 必需软件

1. **Docker Desktop**（必须）
   - macOS: [下载链接](https://docs.docker.com/desktop/install/mac-install/)
   - Windows: [下载链接](https://docs.docker.com/desktop/install/windows-install/)
   - Linux: [下载链接](https://docs.docker.com/desktop/install/linux-install/)

2. **Python 3.8+**（仅用于图形化启动器，可选）
   - macOS: `brew install python@3.11`
   - Windows: [下载链接](https://www.python.org/downloads/)
   - Linux: `sudo apt install python3`

### 硬件要求

- CPU: 双核以上
- 内存：2GB 可用内存
- 磁盘：1GB 可用空间

---

## 📥 安装步骤

### 步骤 1：检查 Docker 安装

打开终端，输入：

```bash
docker --version
```

如果显示版本号，说明 Docker 已安装。否则请先安装 Docker Desktop。

### 步骤 2：启动服务

#### macOS / Linux

```bash
# 进入项目目录
cd /path/to/union-ai-api

# 赋予脚本执行权限
chmod +x start.sh stop.sh restart.sh status.sh

# 一键启动
./start.sh
```

#### Windows (PowerShell)

```powershell
# 进入项目目录
cd C:\path\to\union-ai-api

# 启动服务
docker-compose -f docker-compose.clean.yml up -d
```

### 步骤 3：访问服务

启动成功后，打开浏览器访问：

- **管理后台**: http://localhost:18501
- **API 服务**: http://localhost:18080

---

## 🎮 使用方法

### 1. 首次使用

1. 访问 http://localhost:18501 打开管理后台
2. 在「模型配置」页面添加你的 AI 模型
3. 在「API Key」页面生成 API 密钥
4. 开始使用 API 服务

### 2. 管理命令

#### 查看服务状态

```bash
./status.sh
```

#### 查看实时日志

```bash
docker logs -f union-ai-api
```

#### 重启服务

```bash
./restart.sh
```

#### 停止服务

```bash
./stop.sh
```

#### 完全清理（保留数据）

```bash
./clean.sh
```

### 3. 图形化启动器

```bash
# 启动图形界面
python3 launcher.py
```

功能：
- ✅ 一键启动/停止/重启
- ✅ 实时状态监控
- ✅ 日志查看
- ✅ 快速打开浏览器

---

## ❓ 常见问题

### Q1: Docker 未运行

**错误信息**: `Cannot connect to the Docker daemon`

**解决方案**:
1. 启动 Docker Desktop 应用
2. 等待 Docker 完全启动（状态栏图标变绿）
3. 重新运行 `./start.sh`

### Q2: 端口被占用

**错误信息**: `Bind for 0.0.0.0:18080 failed: port is already allocated`

**解决方案**:
1. 检查是否有其他服务占用端口：
   ```bash
   lsof -i :18080
   lsof -i :18501
   ```
2. 停止占用端口的服务，或修改 `docker-compose.clean.yml` 中的端口映射

### Q3: 权限错误

**错误信息**: `Permission denied`

**解决方案**:
```bash
# 赋予脚本执行权限
chmod +x *.sh

# 修复数据目录权限
mkdir -p ../union-ai-data
chmod 755 ../union-ai-data
```

### Q4: 服务启动慢

**原因**: 首次启动需要下载 Docker 镜像

**解决方案**:
- 耐心等待首次下载完成（约 5-10 分钟）
- 后续启动会非常快（秒开）

### Q5: 数据在哪里？

所有数据存储在 `./data` 目录（项目文件夹内），包括：
- 数据库文件
- 模型配置
- API Key
- 调用日志

**重要**: 
- `data` 目录已被 `.gitignore` 排除，不会被 Git 跟踪
- 删除项目时，请手动备份 `data` 目录以保留数据
- 打包分发时，`data` 目录不会被包含（除非你手动添加）

---

## 📁 文件说明

### 核心文件

```
union-ai-api/
├── docker-compose.clean.yml    # Docker Compose 配置
├── Dockerfile.clean            # Docker 镜像构建文件
├── start.sh                    # 一键启动脚本
├── stop.sh                     # 停止服务脚本
├── restart.sh                  # 重启服务脚本
├── status.sh                   # 状态检查脚本
├── clean.sh                    # 清理脚本
├── launcher.py                 # 图形化启动器
└── README_DEPLOYMENT.md        # 本文件
```

### 数据目录

```
data/                           # 数据存储目录（自动生成，已被 .gitignore 排除）
└── proxy.db                    # SQLite 数据库
```

---

## 🔧 高级配置

### 修改端口

编辑 `docker-compose.clean.yml`：

```yaml
ports:
  - "自定义端口：18080"  # API 服务
  - "自定义端口：18501"  # 管理后台
```

### 数据备份

```bash
# 备份数据
cp -r data data.backup

# 恢复数据
cp -r data.backup data
```

### 查看容器信息

```bash
# 查看容器详情
docker inspect union-ai-api

# 进入容器
docker exec -it union-ai-api bash
```

---

## 📞 技术支持

如遇到问题，请提供以下信息：

1. 操作系统版本
2. Docker 版本
3. 错误日志：`docker logs union-ai-api`
4. 服务状态：`./status.sh`

---

## 📝 更新日志

### v1.0.0 (2026)
- ✅ 初始版本
- ✅ Docker 容器化部署
- ✅ 一键启动脚本
- ✅ 图形化启动器
- ✅ 数据与代码分离

---

**🎉 享受你的 Union AI API！**
