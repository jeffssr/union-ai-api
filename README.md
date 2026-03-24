# 🚀 Union AI API

<p align="center">

[![Docker Build](https://img.shields.io/docker/build/jeffssr1/union-ai-api?style=flat-square)](https://hub.docker.com/r/jeffssr1/union-ai-api)
[![Python Version](https://img.shields.io/badge/python-3.11+-blue?style=flat-square)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)](LICENSE)
[![GitHub Stars](https://img.shields.io/github/stars/jeffssr/union-ai-api?style=flat-square)](https://github.com/jeffssr/union-ai-api/stargazers)

</p>

统一的多模型 AI 代理 API 服务，支持快速切换多个 LLM 提供商，提供 Web 管理界面。

## ✨ 特性

- 🌐 **统一 API 接口** - 一个接口调用多个 AI 模型
- 🔄 **自动切换模型** - 主模型失败时自动切换备用模型
- 📊 **用量统计** - 实时监控 API 调用和 Token 使用
- 🔑 **API Key 管理** - 生成和管理客户端访问密钥
- 📋 **调用日志** - 完整的请求日志和错误追踪
- 🎨 **Web 管理后台** - 图形界面配置模型和查看数据
- 🐳 **Docker 部署** - 开箱即用，一键部署

## 🎈 应用截图

| 页面 | 截图示例 |
|------|------|
| 数据概览 | <img width="1565" height="918" alt="image" src="https://github.com/user-attachments/assets/a2f1dd04-96d1-475f-8f79-c2c79da3a749" /> |
| 模型配置 | <img width="1565" height="918" alt="image" src="https://github.com/user-attachments/assets/46c49eab-3cb5-4726-8237-7943520ae3b0" /> |
| 模型配置2 | <img width="1565" height="918" alt="image" src="https://github.com/user-attachments/assets/e1528325-0f00-4d54-a73f-02c91efe178c" /> |
| apikey | <img width="1565" height="918" alt="image" src="https://github.com/user-attachments/assets/3795b6a0-386b-4d49-850c-7335130ed049" /> |
| 调用记录 | <img width="1565" height="918" alt="image" src="https://github.com/user-attachments/assets/30a852ae-55a0-4e55-b6b2-b53ed4049425" /> |

## 🏁 快速开始

### 方式一：Docker 部署（推荐）

```bash
# 1. 克隆或下载项目
git clone https://github.com/jeffssr/union-ai-api.git
cd union-ai-api

# 2. 启动服务
chmod +x start.sh
./start.sh

# 3. 访问
# 管理后台：http://localhost:18501
# API 服务：http://localhost:18080
```

### 方式二：使用 Docker Compose

```bash
# 克隆项目
git clone https://github.com/jeffssr/union-ai-api.git
cd union-ai-api

# 启动服务
docker-compose -f docker-compose.clean.yml up -d

# 查看日志
docker logs -f union-ai-api
```

### 方式三：从源码运行

```bash
# 克隆项目
git clone https://github.com/jeffssr/union-ai-api.git
cd union-ai-api

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 启动服务
# 终端 1：启动 API 服务
uvicorn app.main:app --host 0.0.0.0 --port 18080

# 终端 2：启动管理后台
streamlit run streamlit_app/home.py --server.port 18501
```

## 📖 使用指南

### 1. 配置模型

1. 打开管理后台：http://localhost:18501
2. 进入「模型配置」页面
3. 点击「添加新模型」
4. 填写配置信息：
   - 模型名称（如：GPT-4）
   - API 地址（如：https://api.openai.com/v1/chat/completions）
   - API Key（你的 API 密钥）
   - Model ID（如：gpt-4）
   - 每日 Token 限制
   - 每日调用次数限制
   - 优先级（数字越大越优先）

### 2. 生成 API Key

1. 进入「API Key」页面
2. 点击「生成新 API Key」
3. 复制生成的密钥

### 3. 调用 API

```bash
# 使用生成的 API Key 调用
curl -X POST http://localhost:18080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "model": "gpt-4",
    "messages": [{"role": "user", "content": "你好"}]
  }'
```

## 🔧 配置说明

### 端口配置

| 服务 | 端口 | 说明 |
|------|------|------|
| API 服务 | 18080 | OpenAI 兼容接口 |
| 管理后台 | 18501 | Web 界面 |

### 环境变量

如果需要自定义配置，可以修改 `docker-compose.clean.yml`：

```yaml
environment:
  - PYTHONUNBUFFERED=1
  - PYTHONPATH=/app
```

### 数据存储

所有数据存储在 `./data` 目录：
- `proxy.db` - SQLite 数据库

**注意**：`data/` 目录已被 `.gitignore` 排除，不会被 Git 跟踪。

## 📡 API 文档

### 兼容性

本 API 兼容 OpenAI 接口格式，支持大多数 OpenAI 客户端。

### 端点

```
POST /v1/chat/completions
```

### 请求示例

```python
import requests

url = "http://localhost:18080/v1/chat/completions"
headers = {
    "Authorization": "Bearer YOUR_API_KEY",
    "Content-Type": "application/json"
}
data = {
    "model": "gpt-4",
    "messages": [
        {"role": "system", "content": "你是一个助手"},
        {"role": "user", "content": "你好"}
    ]
}

response = requests.post(url, headers=headers, json=data)
print(response.json())
```

### 健康检查

```bash
curl http://localhost:18080/health
```

响应：
```json
{"status":"healthy"}
```

## 🐳 Docker 命令

```bash
# 启动服务
docker-compose -f docker-compose.clean.yml up -d

# 停止服务
docker-compose -f docker-compose.clean.yml down

# 重启服务
docker-compose -f docker-compose.clean.yml restart

# 查看状态
./status.sh

# 查看日志
docker logs -f union-ai-api

# 进入容器
docker exec -it union-ai-api bash
```

## 📁 项目结构

```
union-ai-api/
├── app/                     # 应用代码
│   ├── router/              # API 路由
│   ├── services/            # 服务层
│   ├── database.py          # 数据库配置
│   └── main.py              # 应用入口
├── streamlit_app/           # 管理后台
├── data/                    # 数据目录（.gitignore 排除）
├── Dockerfile.clean          # Docker 镜像配置
├── docker-compose.clean.yml # Docker Compose 配置
├── start.sh                 # 启动脚本
├── stop.sh                  # 停止脚本
├── restart.sh               # 重启脚本
├── status.sh                # 状态检查
├── launcher.py              # 图形化启动器
├── LICENSE                  # MIT 许可证
├── DISCLAIMER.md            # 免责声明
└── README.md                # 本文件
```

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

本项目基于 MIT 许可证开源 - 查看 [LICENSE](LICENSE) 文件了解详情。

## ⚠️ 免责声明

使用本软件即表示您同意以下条款：
- 本软件仅供学习和研究使用
- 使用本软件的风险由您自行承担
- 详情请查看 [DISCLAIMER.md](DISCLAIMER.md)

---

**⭐ 如果这个项目对你有帮助，请给我们一个 Star！**
