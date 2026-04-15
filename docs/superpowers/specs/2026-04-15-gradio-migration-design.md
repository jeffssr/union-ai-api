---
title: Streamlit → Gradio 前端迁移设计规格
date: 2026-04-15
status: approved
---

# Streamlit → Gradio 前端迁移设计规格

## 概述

将 `streamlit_app/` 前端从 Streamlit 迁移到 Gradio 5.x，**仅重构 UI 层**。`db.py` 直接复制，业务逻辑零修改。新前端放在 `gradio_app/` 目录，旧 `streamlit_app/` 保留。

**设计决策：**

1. 范围：仅 UI 层重构，db.py 复制不修改，后端不碰
2. 框架：Gradio 5.x 稳定版（>=5.0,<6.0）
3. 架构：`gr.Blocks()` + `gr.Tabs()` 单页应用，页面模块化
4. 认证：Gradio 内置 `auth=` 参数 + 主界面内注册/改密码
5. 风格：MiniMax 核心风格（渐变卡片 + 品牌色 + 圆角卡片），不定制字体和精确阴影
6. 列表渲染：混合方案（`gr.HTML` 展示 + 独立表单操作）
7. 端口：保持 18501

## 项目结构

```
union-ai-api/
├── app/                          # 后端 FastAPI（不改动）
├── gradio_app/                   # 新前端
│   ├── __init__.py               # 空
│   ├── app.py                    # 主入口：Blocks + Tabs + auth + launch
│   ├── db.py                     # 直接复制自 streamlit_app/db.py，零修改
│   ├── theme.py                  # MiniMax 主题 + 自定义 CSS
│   └── pages/
│       ├── __init__.py           # 空
│       ├── dashboard.py          # 数据概览页
│       ├── model_config.py       # 模型配置页
│       ├── api_keys.py           # API Key 管理页
│       └── call_logs.py          # 调用记录页
├── streamlit_app/                # 旧前端（保留）
├── tests/                        # 测试
│   ├── __init__.py
│   ├── conftest.py               # 临时数据库 fixture
│   ├── test_db.py                # db.py 验证
│   ├── test_auth.py              # 认证逻辑
│   ├── test_dashboard.py         # Dashboard 纯函数
│   ├── test_model_config.py      # Excel 导入导出
│   └── test_call_logs.py         # 调用记录纯函数
├── supervisord.conf              # 改为启动 gradio_app
├── Dockerfile.clean              # 改为复制 gradio_app
├── requirements.txt              # streamlit → gradio
└── docker-compose.clean.yml      # 不变
```

## 颜色常量

### 品牌色

```
品牌蓝: #1456f0    天蓝: #3daeff    品牌粉: #ea5ec1
深蓝: #17437d      主蓝: #3b82f6    浅蓝: #60a5fa
```

### 功能色

```
深色背景: #181e25  主文字: #222222   副文字: #45515e
弱文字: #8e8e93    边框: #e5e7eb    分割线: #f2f3f5
输入框背景: #f2f3f5  成功绿: #e8ffea
成功文字: #16a34a   危险红: #ef4444
```

### 卡片渐变色板（按顺序循环分配）

```
1. 蓝→深蓝:  linear-gradient(135deg, #1456f0, #3b82f6)
2. 粉→紫:    linear-gradient(135deg, #ea5ec1, #9333ea)
3. 天蓝→蓝:  linear-gradient(135deg, #3daeff, #1456f0)
4. 橙→粉:    linear-gradient(135deg, #f97316, #ea5ec1)
5. 绿→蓝:    linear-gradient(135deg, #10b981, #3b82f6)
不可用:      linear-gradient(135deg, #8e8e93, #45515e) + opacity: 0.6
```

### 阴影

```
标准卡片:   rgba(0,0,0,0.08) 0px 4px 6px
品牌阴影:   rgba(44,30,116,0.16) 0px 0px 15px
提升阴影:   rgba(36,36,36,0.08) 0px 12px 16px -4px
```

## UI 组件样式规格（Mockup 锁定）

> 以下为 brainstorming 阶段确认的 Mockup 效果，实现时严格按照此规格执行，不得变形。

### Dashboard — 统计摘要卡片

```
容器:  display: flex; gap: 16px; margin-bottom: 24px;
卡片:  flex: 1; 渐变背景; border-radius: 16px; padding: 20px; color: white;
       box-shadow: rgba(44,30,116,0.16) 0px 0px 15px;
标签:  font-size: 12px; opacity: 0.8; margin-bottom: 8px;
数值:  font-size: 24px; font-weight: 600;
```

- 第 1 张：蓝→深蓝渐变（#1456f0 → #3b82f6），标签"今日 Token 用量"
- 第 2 张：粉→紫渐变（#ea5ec1 → #9333ea），标签"今日调用次数"
- 第 3 张：天蓝→蓝渐变（#3daeff → #1456f0），标签"活跃模型数"

### Dashboard — 模型状态卡片

```
容器:  display: flex; gap: 16px; flex-wrap: wrap;
卡片:  flex: 1; min-width: 200px; 渐变背景; border-radius: 16px;
       padding: 16px; color: white; position: relative;
头部:  display: flex; justify-content: space-between; align-items: center;
       margin-bottom: 8px;
名称:  font-size: 16px; font-weight: 600;
默认徽章: background: rgba(255,255,255,0.25); border-radius: 9999px;
          padding: 2px 10px; font-size: 12px;
元信息: font-size: 12px; opacity: 0.85; margin-bottom: 8px; （Model ID · 优先级）
用量:   font-size: 12px; opacity: 0.8; （Token: x / y · 调用: x / y）
进度条: margin-top: 8px;
  轨道: background: rgba(255,255,255,0.2); border-radius: 9999px; height: 4px;
  填充: background: white; border-radius: 9999px; height: 4px; width: {使用率%};
不可用: 灰色渐变（#8e8e93 → #45515e）+ opacity: 0.6;
```

### Dashboard — 详细数据表格

```
容器:   border: 1px solid #e5e7eb; border-radius: 8px; overflow: hidden;
表头:   background: #f8fafc; color: #45515e; text-align: left;
表头文字: font-weight: 500; padding: 10px 12px;
行分隔: border-top: 1px solid #f2f3f5;
交替行: 奇数行 #fafbfc 背景;
文字:   13px;
模型名称: color: #222222;
其他列:  color: #45515e;
状态列:  成功 → <span style="color: #10b981;">●</span> 可用
         失败 → <span style="color: #ef4444;">●</span> 不可用
```

### 模型配置 — 操作栏按钮

```
次级按钮: background: #f0f0f0; color: #333333; border: none;
           border-radius: 8px; padding: 8px 16px; font-size: 13px;
主按钮:   background: #1456f0; color: white; border: none;
           border-radius: 8px; padding: 8px 16px; font-size: 13px;
```

### 模型配置 — 全局设置卡片

```
卡片:  background: white; border: 1px solid #e5e7eb; border-radius: 8px;
       padding: 16px; box-shadow: rgba(0,0,0,0.08) 0px 4px 6px;
标题:  font-size: 16px; font-weight: 500; color: #222222; margin-bottom: 12px;
提示:  font-size: 13px; color: #8e8e93; margin-top: 8px;
```

### 模型配置 — 模型列表卡片

```
卡片:  background: white; border: 1px solid #e5e7eb; border-radius: 16px;
       padding: 16px; box-shadow: rgba(0,0,0,0.08) 0px 4px 6px;
布局:  display: flex; justify-content: space-between; align-items: center;
名称:  font-size: 16px; font-weight: 600; color: #222222;
优先级标签: font-size: 12px; color: #8e8e93; background: #f2f3f5;
            padding: 2px 8px; border-radius: 9999px; margin-left: 8px;
默认标签:  font-size: 12px; color: #16a34a; background: #e8ffea;
            padding: 2px 8px; border-radius: 9999px; margin-left: 8px;
右侧摘要: font-size: 12px; color: #8e8e93;
```

### 模型配置 — 编辑表单

```
表单容器: background: white; border: 1px solid #e5e7eb; border-radius: 8px;
          padding: 16px; box-shadow: rgba(0,0,0,0.08) 0px 4px 6px;
字段布局: display: grid; grid-template-columns: 1fr 1fr; gap: 12px;
标签:   font-size: 12px; color: #45515e; margin-bottom: 4px;
输入框: width: 100%; background: #f2f3f5; border: 1px solid #e5e7eb;
         border-radius: 8px; padding: 8px 12px; font-size: 14px; box-sizing: border-box;
更新按钮: background: #1456f0; color: white; border: none; border-radius: 8px;
           padding: 8px 20px; font-size: 13px;
删除按钮: background: #f0f0f0; color: #ef4444; border: none; border-radius: 8px;
           padding: 8px 20px; font-size: 13px;
复制配置: background: none; color: #1456f0; border: none;
           font-size: 13px; text-decoration: underline;
```

### API Key — 生成结果展示

```
容器:  background: #f8fafc; border-left: 3px solid #1456f0;
       border-radius: 4px; padding: 12px; font-family: monospace; font-size: 13px;
Key ID: color: #8e8e93; font-size: 12px;
API Key: color: #222222;
警告:  color: #ef4444; font-size: 13px; margin-top: 8px;
       文字："请立即复制保存，此 Key 仅显示一次"
```

### API Key — Key 列表卡片

```
卡片:  background: white; border: 1px solid #e5e7eb; border-radius: 13px;
       padding: 16px; box-shadow: rgba(0,0,0,0.08) 0px 4px 6px;
布局:  display: flex; justify-content: space-between; align-items: center;
名称:  font-size: 16px; font-weight: 500; color: #222222;
Key值: font-family: monospace; font-size: 13px; color: #45515e; margin-top: 4px;
删除按钮: background: none; color: #ef4444; border: 1px solid #fecaca;
           border-radius: 8px; padding: 6px 14px; font-size: 13px;
```

### 调用记录 — 表格

与 Dashboard 详细数据表格样式一致，额外：
```
页脚提示: font-size: 13px; color: #8e8e93; margin-top: 12px;
          文字："显示最近 200 条记录"
刷新按钮: background: #f0f0f0; color: #333; border: none; border-radius: 8px;
           padding: 6px 16px; font-size: 13px;
状态列:  成功 → <span style="color: #10b981;">●</span> 成功
         失败 → <span style="color: #ef4444;">●</span> 失败
错误信息: 失败时 color: #ef4444; 成功时 color: #8e8e93; 显示 "-"
```

## 第 1 部分：认证系统

### 登录

Gradio 内置 `auth=` 参数，自动生成登录页（无法自定义样式）：

```python
def auth_fn(username, password):
    if not db.has_users():
        return True  # 无用户时放行，允许首次注册
    user = db.get_user(username)
    if user and db.verify_password(password, user['password_hash'], user['salt']):
        return True
    return False

demo = gr.Blocks(theme=theme, css=CUSTOM_CSS, auth=auth_fn)
demo.launch(server_port=18501)
```

### 注册

主界面顶部检测 `db.has_users()`：
- 无用户 → 显示 `gr.Column` 注册表单（用户名 + 密码 + 确认密码 + 注册按钮）
- 有用户 → 隐藏

### 修改密码

最后一个 Tab（设置）内的 Accordion：
- `gr.Textbox`(旧密码) + `gr.Textbox`(新密码) + `gr.Textbox`(确认) + `gr.Button`
- 调用 `db.update_user_password()`

### 退出登录

Gradio 内置右上角登出按钮，无需额外实现。

### 不变部分

- `db.py` 的 `create_user`、`get_user`、`verify_password`、`hash_password`、`has_users`、`update_user_password` 全部原样调用

## 第 2 部分：Dashboard（数据概览页）

### 组件映射

| 功能 | Gradio 组件 | 说明 |
|------|-------------|------|
| 统计摘要卡片 | `gr.HTML` | 3 张渐变卡片，纯函数 `build_stats_html()` |
| 模型状态卡片 | `gr.HTML` | 渐变卡片网格，纯函数 `build_model_cards_html()` |
| 详细数据 | `gr.Dataframe` | 纯函数 `build_detail_dataframe()` 返回 pd.DataFrame |
| 刷新 | `gr.Button` + `demo.load` | 点击刷新 / 页面加载自动刷新 |

### 布局

```
┌─────────────────────────────────────────────┐
│ 数据概览（20px, weight 600, #222222）         │
├──────────┬──────────┬──────────────────────┤
│ 今日Token │ 今日调用  │ 活跃模型数              │  ← gr.HTML 渐变卡片
├──────────┴──────────┴──────────────────────┤
│ 模型状态                                      │
│ [渐变卡片 1] [渐变卡片 2] [渐变卡片 3]          │  ← gr.HTML
├─────────────────────────────────────────────┤
│ 详细数据                                      │
│ [gr.Dataframe]                               │
└─────────────────────────────────────────────┘
```

### 统计摘要卡片

3 张渐变卡片横向排列（`gr.HTML` 渲染）：
- 今日 Token 用量：蓝→深蓝渐变
- 今日调用次数：粉→紫渐变
- 活跃模型数：天蓝→蓝渐变

样式：16px 圆角，白色文字，品牌阴影。

### 模型状态卡片

使用渐变色板按模型顺序循环分配颜色：
- 卡片内容：模型名称 + 默认徽章 + Model ID + 优先级 + Token/调用用量 + 进度条
- 不可用模型：灰色渐变 + opacity 0.6

### 详细数据表格

`gr.Dataframe` 展示，列：
模型名称、Model ID、是否可用、已用调用、调用限额、剩余调用、调用使用率、已用 Token、Token 限额、剩余 Token、Token 使用率、默认模型、优先级

### 数据流

`db.get_daily_stats()` → 纯函数构建 HTML/DataFrame → 渲染

### 不变部分

- `get_daily_stats()` 数据查询逻辑
- 展示字段和列定义

## 第 3 部分：模型配置页

### 操作栏

```
[导出配置]  [导入配置]  [+ 添加模型]
```

- 导出：`gr.DownloadButton`，调用 `export_models_to_excel()`
- 导入：`gr.File` 上传 + `gr.Button` 确认，调用 `import_models_from_excel()`
- 添加模型：`gr.Accordion` 展开/收起表单

### 全局设置

- 自动切换模型：`gr.Checkbox`，`value=get_auto_switch_status()`
- 变更时调用 `set_auto_switch_status()`
- 提示文字 13px，#8e8e93

### 模型列表展示

`gr.HTML` 渲染模型卡片列表，纯函数 `build_model_list_html()`：
- 每个模型一张白色卡片（16px 圆角，#e5e7eb 边框，标准卡片阴影）
- 卡片内容：模型名称 + 优先级标签 + 默认模型标签 + Model ID + Token 用量摘要

### 编辑/删除/复制操作区

独立表单区域（不嵌套在列表内）：
- `gr.Dropdown` 选择要操作的模型
- 选择后自动填充表单字段：模型名称、API 地址、API Key（password）、Model ID、Token 上限、调用上限、优先级
- 操作按钮：[更新]（#1456f0 背景）、[删除]（#ef4444 文字）、[复制配置]（文字按钮）
- 每次操作后刷新模型列表 HTML + 重新加载 Dropdown 选项

### 添加模型

`gr.Accordion` 包裹表单：
- 字段：模型名称、API 地址、API Key、Model ID、Token 上限、调用上限、优先级
- 提交后刷新列表

### 默认模型设置

- 仅关闭自动切换时显示（`gr.Column(visible=not auto_switch)`）
- `gr.Dropdown` 选择模型 + `gr.Button` 保存

### 不变部分

- 所有 CRUD 操作（`create_model`、`update_model`、`delete_model`）
- 优先级管理逻辑
- Excel 导入导出逻辑（`export_models_to_excel`、`import_models_from_excel`）
- 复制配置逻辑

## 第 4 部分：API Key 管理页

### 生成新 Key

`gr.Accordion` 包裹表单：
- Key 名称：`gr.Textbox`
- 生成按钮：`gr.Button`（#1456f0 背景）
- 结果展示：`gr.Textbox`(readonly) 显示 Key ID + API Key + 警告提示

### Key 列表

`gr.HTML` 渲染卡片，纯函数 `build_key_list_html()`：
- 每个 Key 一张卡片（13px 圆角，#e5e7eb 边框）
- Key 名称 + API Key（monospace） + 删除按钮

### 删除 Key

`gr.Dropdown` 选择 Key + `gr.Button` 删除

### 不变部分

- `create_api_key()`、`delete_api_key()`、`get_all_api_keys()` 函数
- Key 生成逻辑（`sk-` 前缀 + token_urlsafe）

## 第 5 部分：调用记录页

### 数据表格

- `gr.Dataframe` 展示最近 200 条记录
- 列：请求 ID、API 名称、调用时间、模型、输入 Token、输出 Token、状态、错误信息
- `gr.Button` 刷新 + `demo.load` 自动加载

### 不变部分

- `get_call_logs()` 数据查询逻辑

## 第 6 部分：主题与 CSS

### Gradio 主题

基于 `gr.themes.Soft` 定制：
- `primary_hue`: blue（品牌蓝 #1456f0）
- `font`: DM Sans（Google Fonts CDN）
- 按钮主色：#1456f0 背景，白色文字
- 输入框：#f2f3f5 背景，#e5e7eb 边框，8px 圆角
- 卡片圆角：16px，阴影 rgba(0,0,0,0.08) 0px 4px 6px

### CSS 覆盖（核心定制，不过度）

通过 `css=` 参数传入：

1. **Tab 导航样式**：药丸按钮（9999px 圆角），激活态 rgba(0,0,0,0.05) 背景
2. **卡片圆角**：16px 统一
3. **表格样式**：#f8fafc 表头背景，行间 #f2f3f5 分隔
4. **字体加载**：Google Fonts CDN 引入 DM Sans
5. **隐藏默认 footer**：`.footer { display: none; }`

### 不定制

- 精确阴影值匹配（用 Gradio 默认阴影）
- Outfit/Poppins 字体（统一用 DM Sans）
- 登录页样式（Gradio 内置登录页无法自定义）

## 第 7 部分：部署变更

### 修改文件清单

**requirements.txt：**
```
# streamlit==1.31.1  （注释/移除）
gradio>=5.0,<6.0     （新增）
```

**supervisord.conf：**
```ini
[program:gradio]
command=python -u gradio_app/app.py
autostart=true
autorestart=true
stdout_logfile=/dev/stdout
stdout_logfile_maxbytes=0
stderr_logfile=/dev/stderr
stderr_logfile_maxbytes=0
```

**Dockerfile.clean：**
```dockerfile
COPY gradio_app ./gradio_app
```

### 不修改的文件

- `app/` 目录所有文件
- `streamlit_app/` 保留原样
- `launcher.py`
- `docker-compose.clean.yml`（端口保持 18501:8501）
- 所有 shell 脚本
