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
- 🆕 **Responses API 支持** - 兼容 Codex v0.80.0+ 和 OpenAI SDK v1.60+
- 🔄 **自动切换模型** - 主模型失败时自动切换备用模型
- 📊 **用量统计** - 实时监控 API 调用和 Token 使用
- 🔑 **API Key 管理** - 生成和管理客户端访问密钥
- 📋 **调用日志** - 完整的请求日志和错误追踪
- 🎨 **Web 管理后台** - 图形界面配置模型和查看数据
- 👤 **用户认证** - 支持注册、登录、密码修改功能
- 📋 **配置复制** - 一键复制模型配置，快速创建新配置
- 📥📤 **导入导出** - 支持 Excel 格式导入导出模型配置
- 🐳 **Docker 部署** - 开箱即用，一键部署
- ⚡ **秒级启动** - 非首次启动只需 1-2 秒

## 🎈 应用截图

|   页面    | 截图示例                                                     |
| :-------: | ------------------------------------------------------------ |
|   注册    | ![image-20260401113749208](https://cdn.jsdelivr.net/gh/jeffssr/images/image-20260401113749208.png) |
| 数据概览  | ![](https://github.com/user-attachments/assets/a2f1dd04-96d1-475f-8f79-c2c79da3a749) |
| 模型配置  | ![](https://github.com/user-attachments/assets/46c49eab-3cb5-4726-8237-7943520ae3b0) |
| 模型配置2 | ![](https://github.com/user-attachments/assets/e1528325-0f00-4d54-a73f-02c91efe178c) |
|  apikey   | ![](https://github.com/user-attachments/assets/3795b6a0-386b-4d49-850c-7335130ed049) |
| 调用记录  | ![](https://github.com/user-attachments/assets/30a852ae-55a0-4e55-b6b2-b53ed4049425) |

## 🔗 外部调用示例

| 应用                      | 使用截图                                                     |
| ------------------------- | ------------------------------------------------------------ |
| Chatbox                   | ![](https://cdn.jsdelivr.net/gh/jeffssr/images/PixPin_2026-03-25_09-50-00.png) |
| Chatbox                   | ![PixPin_2026-03-25_09-50-54](https://cdn.jsdelivr.net/gh/jeffssr/images/PixPin_2026-03-25_09-50-54.png) |
| ClawX / openclaw 类似应用 | ![PixPin_2026-03-25_09-51-17](https://cdn.jsdelivr.net/gh/jeffssr/images/PixPin_2026-03-25_09-51-17.png) |
| Codex CLI                 | `export OPENAI_BASE_URL=http://localhost:18080 && codex` |

## 🏁 快速开始

### 方式一：一键脚本启动（推荐 ⭐）

```bash
# 1. 克隆或下载项目
git clone https://github.com/jeffssr/union-ai-api.git
cd union-ai-api

# 2. 一键启动（首次会自动构建，后续秒开）
chmod +x start.sh
./start.sh

# 3. 访问
# 管理后台：http://localhost:18501
# API 服务：http://localhost:18080
```

### 常用命令

```bash
# 启动服务（首次构建，后续秒开）
./start.sh

# 停止服务（保留容器，下次秒开）
./stop.sh

# 重启服务
./restart.sh

# 查看状态
./status.sh

# 完全清理（删除容器和镜像）
./clean.sh

# 查看日志
docker logs -f union-ai-api
```

### 方式二：使用 Docker Compose 命令

```bash
# 克隆项目
git clone https://github.com/jeffssr/union-ai-api.git
cd union-ai-api

# 启动服务（首次会自动构建镜像）
docker-compose -f docker-compose.clean.yml up -d

# 停止服务（保留容器，下次秒开）
docker-compose -f docker-compose.clean.yml stop

# 启动已停止的服务（秒开）
docker-compose -f docker-compose.clean.yml start

# 重启服务
docker-compose -f docker-compose.clean.yml restart

# 完全停止并删除容器
docker-compose -f docker-compose.clean.yml down

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

### 1. 首次使用（注册管理员账号）

首次打开管理后台时，系统会自动检测是否需要注册：

1. 打开管理后台：http://localhost:18501
2. 如果是首次使用，会显示**注册页面**
3. 输入用户名和密码（密码长度至少4位）
4. 点击注册，成功后自动跳转到登录页面
5. 使用注册的账号登录

> **注意**：注册信息存储在本地数据库中，每个部署实例只需注册一次。

### 2. 用户管理

#### 修改密码
登录后，点击右上角的用户名，展开「🔐 修改密码」选项：
1. 输入当前密码
2. 输入新密码（至少4位）
3. 确认新密码
4. 点击修改密码

#### 退出登录
点击右上角的「🚪 退出登录」按钮即可退出。

#### 重置注册数据（重新测试注册流程）

如需清除已注册的用户数据，重新测试注册流程：

**Linux/macOS：**
```bash
# 停止容器
docker stop union-ai-api

# 删除数据文件
rm -rf ./data/*

# 重新启动容器
docker start union-ai-api
```

**Windows（PowerShell）：**
```powershell
# 停止容器
docker stop union-ai-api

# 删除数据文件
Remove-Item -Path .\data\* -Recurse -Force

# 重新启动容器
docker start union-ai-api
```

> ⚠️ **警告**：此操作会删除所有数据，包括用户账号、模型配置、API Keys 和调用记录。

### 3. 配置模型

1. 进入「模型配置」页面
2. 点击「添加新模型」
3. 填写配置信息：
   - 模型名称（如：GPT-4）
   - API 地址（如：https://api.openai.com/v1/chat/completions）
   - API Key（你的 API 密钥）
   - Model ID（如：gpt-4，选填）
   - 每日 Token 限制
   - 每日调用次数限制
   - 优先级（数字越大越优先）

#### 复制配置
在已有模型配置卡片中，点击「📋 复制配置」按钮，可以复制该配置到新模型表单，方便快速创建相似配置。

#### 导入导出配置

**导出配置：**
1. 在模型配置页面，点击「📤 导出配置」按钮
2. 系统会生成包含所有模型配置的 Excel 文件
3. 下载并保存到本地

**导入配置：**
1. 点击「📥 导入配置」展开导入区域
2. 选择要导入的 Excel 文件（.xlsx 或 .xls）
3. 点击「开始导入」
4. 系统会自动识别中英文列名，导入成功后刷新页面查看

> 支持的列名（中英文均可）：
> - 模型名称 / name
> - API地址 / api_url
> - API密钥 / api_key
> - Model ID / model_id
> - 每日Token上限 / daily_token_limit
> - 每日调用上限 / daily_call_limit
> - 优先级 / priority

### 4. 生成 API Key

1. 进入「API Key」页面
2. 点击「生成新 API Key」
3. 输入 Key 名称（如：我的应用）
4. 复制生成的密钥（**注意**：密钥只显示一次，请妥善保存）

### 5. 调用 API

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

### 6. 数据概览

首页以卡片形式展示各模型的使用情况：
- 🟢 绿色圆点：模型可用
- ⚫ 灰色圆点：模型不可用（达到限额或未启用）
- 按优先级从高到低排序

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
- `proxy.db` - SQLite 数据库（包含用户、模型配置、API Keys、调用记录等）

**注意**：`data/` 目录已被 `.gitignore` 排除，不会被 Git 跟踪。

### 数据备份

```bash
# 备份数据
cp -r data data.backup.$(date +%Y%m%d)

# 恢复数据
cp -r data.backup.20260101 data
```

## 🐳 Docker 命令速查

### 快速管理（推荐）

```bash
# 启动服务（首次构建，后续秒开）
./start.sh

# 停止服务（保留容器，下次秒开）
./stop.sh

# 重启服务
./restart.sh

# 查看详细状态
./status.sh

# 完全清理（删除容器和镜像，保留数据）
./clean.sh
```

### 原生 Docker 命令

```bash
# 启动服务
docker-compose -f docker-compose.clean.yml up -d

# 停止服务（保留容器）
docker-compose -f docker-compose.clean.yml stop

# 启动已停止的服务
docker-compose -f docker-compose.clean.yml start

# 重启服务
docker-compose -f docker-compose.clean.yml restart

# 完全停止并删除容器
docker-compose -f docker-compose.clean.yml down

# 查看日志
docker logs -f union-ai-api

# 进入容器
docker exec -it union-ai-api bash

# 查看资源使用
docker stats union-ai-api
```

## 📡 API 文档

### 兼容性

本 API 兼容 OpenAI 接口格式，支持大多数 OpenAI 客户端。同时支持 **OpenAI Responses API**（Codex v0.80.0+ 使用的接口）。

### 支持的端点

| 端点 | 说明 | 适用场景 |
|------|------|----------|
| `POST /v1/chat/completions` | Chat Completions API | 通用 OpenAI 客户端 |
| `POST /v1/responses` | Responses API | Codex v0.80.0+、OpenAI SDK v1.60+ |
| `GET /health` | 健康检查 | 服务状态监控 |

### 1. Chat Completions API

适用于大多数 OpenAI 兼容客户端。

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

### 2. Responses API（Codex / OpenAI SDK 新版）

适用于 Codex v0.80.0+ 或 OpenAI SDK v1.60+。

#### 配置说明

```python
from openai import OpenAI

# 配置客户端
client = OpenAI(
    base_url="http://localhost:18080",  # 本地服务地址
    api_key="your-api-key-from-web-ui"   # 从管理后台生成的 API Key
)

# 非流式调用
response = client.responses.create(
    model="glm-4",  # 你在管理后台配置的模型名称
    input="你好，请介绍一下自己"
)
print(response.output_text)

# 流式调用
stream = client.responses.create(
    model="glm-4",
    input="你好",
    stream=True
)
for event in stream:
    if event.type == "response.output_text.delta":
        print(event.delta, end="")
```

#### 各客户端配置示例

**Codex CLI:**
```bash
# 设置环境变量
export OPENAI_BASE_URL="http://localhost:18080"
export OPENAI_API_KEY="your-api-key-from-web-ui"

# 使用 Codex
codex
```

**Cursor:**
1. 打开设置 → OpenAI API
2. Base URL: `http://localhost:18080/v1`
3. API Key: 从管理后台生成的 Key

**Claude Code / OpenAI SDK:**
```python
import os
os.environ["OPENAI_BASE_URL"] = "http://localhost:18080"
os.environ["OPENAI_API_KEY"] = "your-api-key-from-web-ui"

from openai import OpenAI
client = OpenAI()
```

**Chatbox / LobeChat 等客户端:**
- API 类型: OpenAI
- API 地址: `http://localhost:18080/v1`
- API Key: 从管理后台生成的 Key
- 模型: 填写你在管理后台配置的模型名称

### 健康检查

```bash
curl http://localhost:18080/health
```

响应：
```json
{"status":"healthy"}
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
│   ├── home.py              # 主页面
│   └── db.py                # 数据库操作
├── data/                    # 数据目录（.gitignore 排除）
├── Dockerfile.clean          # Docker 镜像配置
├── docker-compose.clean.yml # Docker Compose 配置
├── start.sh                 # 启动脚本（⭐ 推荐）
├── stop.sh                  # 停止脚本（保留容器）
├── restart.sh               # 重启脚本
├── status.sh                # 状态检查
├── clean.sh                 # 完全清理
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
