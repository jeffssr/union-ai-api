---
title: UI 重设计方案 - MiniMax 风格管理后台
date: 2026-04-14
status: approved
---

# UI 重设计方案：MiniMax 风格管理后台

## 概述

参照 DESIGN.md 中的 MiniMax 设计规范，对 Streamlit 管理后台进行完整 UI 重设计。不涉及任何业务逻辑变更，仅调整视觉呈现和布局结构。

**设计决策：**
1. 布局：顶部导航栏 + 无侧边栏
2. 模型卡片：多色渐变卡片（每个模型不同颜色）
3. 登录页：品牌渐变背景 + 居中毛玻璃白色卡片

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
登录页阴影: rgba(44,30,116,0.16) 0px 0px 30px
```

## 字体

通过 Google Fonts CDN 引入：
- **DM Sans**：UI 通用字体（正文、按钮、导航、表格）
- **Outfit**：标题展示字体（页面标题、卡片标题）

字体栈：`'DM Sans', 'Helvetica Neue', Helvetica, Arial, sans-serif`

### 字号层级
| 用途 | 字号 | 字重 | 颜色 |
|------|------|------|------|
| 页面标题 | 20px | 600 | #222222 |
| 卡片标题 | 16px | 600 | #222222 / #fff |
| 副标题 | 16px | 500 | #222222 |
| 正文 | 14px | 400 | #45515e |
| 辅助文字 | 13px | 400 | #8e8e93 |
| 标签 | 12px | 500 | #45515e |
| 统计数值 | 24px | 600 | #fff / #1456f0 |

## 第 1 部分：整体架构与导航

### 页面结构变更
- 隐藏 Streamlit 默认侧边栏
- 页面顶部自定义 HTML 导航栏（通过 `st.markdown` 渲染）
- `st.session_state` 管理页面状态（逻辑不变）

### 导航栏设计
- **背景**：白色，底部 1px `#f2f3f5` 分隔线
- **左侧**：品牌名称 "Union-AI-API"（DM Sans, 16px, weight 600, #18181b）
- **中间**：药丸按钮导航项
  - 激活态：9999px 圆角，`rgba(0,0,0,0.05)` 背景，`#18181b` 文字，weight 500
  - 非激活态：`#8e8e93` 文字，无背景
- **右侧**：用户名（13px, #45515e）+ 退出按钮
- **导航项**：数据概览 | 模型配置 | API Key | 调用记录

### 技术实现
- `set_page_config` 保持 `layout="wide"`，`initial_sidebar_state="collapsed"`
- CSS：`div[data-testid="stSidebar"] { display: none; }`
- 隐藏 Streamlit 默认顶部工具栏
- 导航栏通过 `st.markdown` 输出 HTML，配合 `st.button` + session_state 切换页面

## 第 2 部分：登录/注册页面

### 登录页
- **全屏背景**：`linear-gradient(135deg, #1456f0 0%, #ea5ec1 50%, #3daeff 100%)`
- **居中卡片**：
  - `rgba(255,255,255,0.95)` 背景 + `backdrop-filter: blur(20px)`
  - 24px 圆角，`rgba(44,30,116,0.16) 0px 0px 30px` 阴影
  - 宽度 360px，内边距 40px
- **卡片内容**：
  - 标题 "Union-AI-API"（28px, weight 600, #222222）居中
  - 副标题 "统一多模型 AI 代理服务"（13px, #8e8e93）
  - 输入框：#f2f3f5 背景，8px 圆角，12px 标签 + 14px placeholder
  - 登录按钮：#181e25 背景，白色文字，8px 圆角，全宽

### 注册页
- 与登录页相同的渐变背景和毛玻璃卡片
- 增加确认密码字段
- 首次使用提示改为卡片内浅蓝色提示条

### 不变部分
- token 生成/验证逻辑
- cookie 和 query params 管理
- 表单提交和验证逻辑

## 第 3 部分：数据概览页（Dashboard）

### 页面标题
- "数据概览"（20px, weight 600, #222222），无 emoji 前缀

### 统计摘要卡片（顶部一行）
- 3 张渐变卡片横向排列：
  - 今日 Token 用量：蓝→深蓝渐变
  - 今日调用次数：粉→紫渐变
  - 活跃模型数：天蓝→蓝渐变
- 样式：20px 圆角，白色文字，品牌阴影
- 内容：标签（12px, 80% 透明度）+ 数值（24px, weight 600）

### 模型状态卡片网格
- 3 列网格布局（与现有一致）
- 每张卡片使用渐变色板中的颜色，按模型列表顺序循环分配
- **卡片结构**（20px 圆角，品牌阴影）：
  - 顶部：模型名称（16px, weight 600）+ 默认徽章（rgba(255,255,255,0.25) 背景, 9999px 圆角）或状态指示点
  - 中间：Model ID、优先级（12px, 85% 透明度）
  - 底部：Token 用量 + 调用次数（12px）
  - 进度条：rgba(255,255,255,0.2) 背景 + 白色填充，9999px 圆角
- 不可用模型：灰色渐变 + opacity 0.6

### 详细数据表格
- 分隔线后展示
- 标题 "详细数据"（16px, weight 500, #222222）
- 通过 CSS 覆盖 `st.dataframe` 样式：
  - 表头：#f8fafc 背景，#45515e 文字
  - 表格文字 13px
  - 行间 1px #f2f3f5 分隔

### 不变部分
- 所有数据查询和计算逻辑
- 展示字段和列定义

## 第 4 部分：模型配置页

### 操作栏（顶部）
- 水平排列：
  - "导出配置"：#f0f0f0 背景，#333333 文字，8px 圆角
  - "导入配置"：同上
  - "添加模型"：#1456f0 背景，白色文字，8px 圆角（主要操作突出）

### 全局设置区域
- 白色卡片容器（8px 圆角，#e5e7eb 边框，标准卡片阴影）
- 标题 "全局设置"（16px, weight 500, #222222）
- 使用 `st.toggle` 替代 `st.checkbox`
- 提示文字 13px, #8e8e93

### 模型列表
- 每个模型一张白色卡片（16px 圆角，#e5e7eb 边框，标准卡片阴影）
- **卡片头部**：模型名称（16px, weight 600）+ 优先级标签 + 默认模型标签（#e8ffea 背景, #16a34a 文字, 9999px 圆角）
- **展开后编辑表单**：
  - 输入框：白底 + #e5e7eb 边框 + 8px 圆角 + 12px 标签
  - "更新" 按钮：#1456f0 背景
  - "删除" 按钮：#f0f0f0 背景，#ef4444 文字
  - "复制配置" 按钮：文字按钮样式

### 默认模型设置
- 白色卡片，仅关闭自动切换时显示
- 标题 + `st.selectbox` 下拉选择器

### 不变部分
- 所有 CRUD 操作
- 优先级管理
- 导入导出 Excel 逻辑
- 复制配置逻辑

## 第 5 部分：API Key 管理页 & 调用记录页

### API Key 管理页

**操作栏：**
- "生成新 Key" 按钮：#1456f0 背景，白色文字，8px 圆角

**生成对话框：**
- 白色卡片（16px 圆角，#e5e7eb 边框，品牌阴影）
- 输入框统一样式：#f2f3f5 背景，8px 圆角
- 生成成功后 Key 展示：品牌蓝色代码块（#f8fafc 背景, 左侧 #1456f0 竖线, monospace 字体）

**Key 列表：**
- 每张卡片（13px 圆角，#e5e7eb 边框，标准卡片阴影）
- Key 名称（16px, weight 500）+ API Key 代码块 + 删除按钮
- 删除按钮：#ef4444 文字，hover 浅红背景

### 调用记录页

**页面标题：**
- "调用记录"（20px, weight 600, #222222）

**数据表格：**
- `st.dataframe` + CSS 覆盖样式
- 表头：#f8fafc 背景，#45515e 文字，13px weight 500
- 行：交替白色/#fafbfc 背景
- 状态列：成功绿色圆点（#10b981）、失败红色圆点（#ef4444）

### 不变部分
- 所有数据查询、分页、字段定义

## 第 6 部分：全局 CSS 变更与技术实现

### Streamlit 框架定制
- `layout="wide"`, `initial_sidebar_state="collapsed"`
- CSS 隐藏侧边栏：`div[data-testid="stSidebar"] { display: none; }`
- 隐藏 Streamlit 默认顶部工具栏
- 调整主容器 padding 与导航栏衔接

### 字体加载
- Google Fonts CDN 引入 DM Sans 和 Outfit
- CSS 全局字体栈设置

### 组件渲染方式
- 导航栏：`st.markdown` + HTML
- 渐变卡片：`st.markdown` + HTML + 内联 style
- 表格：`st.dataframe` + CSS 覆盖
- 表单：保持 `st.form` + CSS 样式覆盖

### 不影响的部分
- `db.py` 所有数据库操作
- 所有业务逻辑（CRUD、认证、导入导出等）
- `st.session_state` 状态管理
- `st.form` 表单提交机制
- `st.query_params` 参数管理
- Cookie 和 token 认证逻辑
