import streamlit as st
import pandas as pd
import time
from datetime import date
from streamlit_app.db import (
    get_daily_stats,
    get_all_models,
    create_model,
    update_model,
    delete_model,
    get_all_api_keys,
    create_api_key,
    delete_api_key,
    get_call_logs,
    get_auto_switch_status,
    set_auto_switch_status
)

st.set_page_config(
    page_title="AI 代理管理后台",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

pages = {
    "📊 数据概览": "dashboard",
    "🔧 模型配置": "models",
    "🔑 API Key": "apikeys",
    "📋 调用记录": "logs"
}

if "current_page" not in st.session_state:
    st.session_state.current_page = "📊 数据概览"

st.markdown("""
<style>
    .stMainBlockContainer {padding-top: 2rem;}
    div[data-testid="stSidebar"] > div:first-child {padding-top: 1rem;}
    .stButton > button {width: 100%;}
    .model-header {font-size: 1.1rem; font-weight: bold;}
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.title("🤖 union-ai-api")
    st.divider()

    for page_name in pages.keys():
        if st.button(page_name, use_container_width=True, type="primary" if st.session_state.current_page == page_name else "secondary"):
            st.session_state.current_page = page_name
            st.rerun()

    st.divider()
    st.caption("© 2024 AI Proxy")

page = pages[st.session_state.current_page]

if page == "dashboard":
    st.header("📊 数据概览 - 今日用量")

    stats = get_daily_stats()

    if not stats:
        st.info("暂无模型配置，请前往「模型配置」添加模型")
    else:
        cols = st.columns(len(stats)) if len(stats) <= 4 else st.columns(4)
        for idx, stat in enumerate(stats):
            with cols[idx % 4]:
                remaining_tokens = stat['daily_token_limit'] - stat['used_tokens']
                remaining_calls = stat['daily_call_limit'] - stat['used_calls']
                is_available = stat['used_tokens'] < stat['daily_token_limit'] and stat['used_calls'] < stat['daily_call_limit'] and stat['is_active'] == 1

                color = "#28a745" if is_available else "#6c757d"
                status_text = "🟢 可用" if is_available else "🔴 不可用"

                st.markdown(f"""
                    <div style="padding: 20px; border-radius: 10px; background-color: {color}; color: white; margin: 5px;">
                        <h3 style="color: white;">{stat['name']}</h3>
                        <p style="color: white;">Token: {stat['used_tokens']:,} / {stat['daily_token_limit']:,}</p>
                        <p style="color: white;">调用：{stat['used_calls']:,} / {stat['daily_call_limit']:,}</p>
                        <p style="color: white;"><strong>{status_text}</strong></p>
                    </div>
                """, unsafe_allow_html=True)

        st.divider()
        st.subheader("详细数据")
        df = pd.DataFrame(stats)
        df['剩余 Token'] = df['daily_token_limit'] - df['used_tokens']
        df['剩余调用次数'] = df['daily_call_limit'] - df['used_calls']
        df['Token 使用率'] = (df['used_tokens'] / df['daily_token_limit'] * 100).round(1).astype(str) + '%'
        df['调用使用率'] = (df['used_calls'] / df['daily_call_limit'] * 100).round(1).astype(str) + '%'
        df['默认模型'] = df['is_default_model'].apply(lambda x: '📌 是' if x == 1 else '')
        
        display_df = df[['name', 'model_id', 'used_calls', 'daily_call_limit', '剩余调用次数', '调用使用率', 'used_tokens', 'daily_token_limit', 'Token 使用率', '默认模型', 'is_active']].copy()
        display_df.columns = ['模型名称', 'Model ID', '已用调用', '调用限额', '剩余调用', '调用使用率', '已用 Token', 'Token 限额', 'Token 使用率', '默认模型', '状态']
        st.dataframe(display_df, hide_index=True, use_container_width=True)

elif page == "models":
    st.header("🔧 模型配置")

    models = get_all_models()

    st.subheader("⚙️ 全局设置")
    auto_switch_global = st.checkbox(
        "✅ 启用自动切换模型",
        value=get_auto_switch_status(),
        help="开启后：系统按优先级自动切换所有启用的模型 | 关闭后：所有请求固定使用下方选择的默认模型"
    )
    if auto_switch_global != get_auto_switch_status():
        set_auto_switch_status(auto_switch_global)
        st.success("✅ 设置已保存")
        time.sleep(0.5)
        st.rerun()
    st.caption("💡 提示：关闭自动切换后，请确保下方已选择默认模型，否则所有请求将失败")

    st.divider()

    st.subheader("📋 模型列表")

    with st.expander("➕ 添加新模型"):
        with st.form("add_model_form", clear_on_submit=True):
            name = st.text_input("模型名称", placeholder="例如：GPT-4", key="add_name")
            api_url = st.text_input("API 地址", placeholder="https://api.openai.com/v1/chat/completions", key="add_url")
            api_key = st.text_input("API Key", type="password", key="add_key")
            model_id = st.text_input("Model ID（选填，如 gpt-4、claude-3 等）", placeholder="如留空则使用请求中的 model 参数", key="add_model_id")
            col1, col2 = st.columns(2)
            with col1:
                daily_limit = st.number_input("每日 Token 上限", value=100000, min_value=1, key="add_limit")
            with col2:
                daily_call_limit = st.number_input("每日调用次数上限", value=1000, min_value=1, key="add_call_limit")
            priority = st.number_input("优先级 (数字越大越优先)", value=0, min_value=0, key="add_priority")

            submitted = st.form_submit_button("添加模型")
            if submitted:
                if name and api_url and api_key:
                    create_model(name, api_url, api_key, model_id, daily_limit, daily_call_limit, priority)
                    st.success(f"✅ 模型添加成功！")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("请填写所有必填字段")

    if models:
        default_model_id = None
        for m in models:
            if m.get('is_default_model', 0) == 1:
                default_model_id = m['config_id']
                break

        for model in models:
            is_default = model.get('is_default_model', 0) == 1

            status_badge = ""
            if is_default:
                status_badge = " | 📌 默认模型"

            with st.expander(f"**{model['name']}** (优先级：{model['priority']}{status_badge})"):
                with st.form(f"edit_model_{model['config_id']}", clear_on_submit=True):
                    col1, col2 = st.columns(2)
                    with col1:
                        new_name = st.text_input("模型名称", value=model['name'], key=f"name_{model['config_id']}")
                        new_api_url = st.text_input("API 地址", value=model['api_url'], key=f"url_{model['config_id']}")
                        new_api_key = st.text_input("API Key", value=model['api_key'], type="password", key=f"key_{model['config_id']}")
                        new_model_id = st.text_input("Model ID（选填）", value=model.get('model_id', ''), key=f"model_id_{model['config_id']}")
                    with col2:
                        new_limit = st.number_input("每日 Token 上限", value=model['daily_token_limit'], min_value=1, key=f"limit_{model['config_id']}")
                        new_call_limit = st.number_input("每日调用次数上限", value=model['daily_call_limit'], min_value=1, key=f"call_limit_{model['config_id']}")
                        new_priority = st.number_input("优先级", value=model['priority'], min_value=0, key=f"prio_{model['config_id']}")

                    st.divider()

                    col3, col4 = st.columns(2)
                    with col3:
                        if st.form_submit_button("💾 更新"):
                            update_model(model['config_id'], new_name, new_api_url, new_api_key, new_model_id, new_limit, new_call_limit, 1 if is_default else 0, new_priority)
                            st.success("✅ 模型已更新")
                            time.sleep(1)
                            st.rerun()
                    with col4:
                        if st.form_submit_button("🗑️ 删除"):
                            delete_model(model['config_id'])
                            st.success("✅ 模型已删除")
                            time.sleep(1)
                            st.rerun()

        st.divider()
        st.subheader("📌 默认模型设置")
        st.caption("仅在关闭自动切换时使用，所有请求将固定使用此模型")

        if not auto_switch_global:
            model_options = {}
            for m in models:
                model_options[f"{m['name']} (优先级：{m['priority']})"] = m['config_id']

            if model_options:
                current_default = default_model_id if default_model_id else next(iter(model_options.values()))
                selected = st.selectbox(
                    "选择默认模型",
                    options=list(model_options.values()),
                    format_func=lambda x: next((k for k, v in model_options.items() if v == x), ""),
                    index=list(model_options.values()).index(current_default) if current_default in model_options.values() else 0
                )

                if st.button("💾 保存默认模型"):
                    for m in models:
                        is_default = (m['config_id'] == selected)
                        update_model(m['config_id'], m['name'], m['api_url'], m['api_key'], m.get('model_id', ''), m['daily_token_limit'], m['daily_call_limit'], 1 if is_default else 0, m['priority'])
                    st.success("✅ 默认模型已保存")
                    time.sleep(1)
                    st.rerun()
            else:
                st.warning("没有模型可选")
        else:
            st.info("自动切换已开启，无需设置默认模型")

    else:
        st.info("暂无模型配置")

elif page == "apikeys":
    st.header("🔑 API Key 管理")

    with st.expander("➕ 生成新 API Key"):
        with st.form("add_api_key_form", clear_on_submit=True):
            name = st.text_input("Key 名称", placeholder="例如：我的应用", key="key_name")
            submitted = st.form_submit_button("生成")
            if submitted:
                if name:
                    result = create_api_key(name)
                    st.success("✅ API Key 生成成功！")
                    st.write(f"**Key ID:** `{result['key_id']}`")
                    st.write(f"**API Key:** `{result['api_key']}`")
                    st.warning("⚠️ 请立即复制 API Key，它不会被保存，只能生成新的。")
                else:
                    st.error("请输入名称")

    st.subheader("📋 API Key 列表")
    api_keys = get_all_api_keys()

    if api_keys:
        for key in api_keys:
            with st.expander(f"{key['name']}"):
                st.write(f"**API Key:** `{key['api_key']}`")
                if st.button(f"🗑️ 删除", key=f"del_{key['key_id']}"):
                    delete_api_key(key['key_id'])
                    st.rerun()
    else:
        st.info("暂无 API Key，请点击上方「生成新 API Key」创建一个")

elif page == "logs":
    st.header("📋 调用记录")

    logs = get_call_logs(200)

    if logs:
        df = pd.DataFrame(logs)
        df['created_at'] = pd.to_datetime(df['created_at'])
        df = df.sort_values('created_at', ascending=False)

        st.dataframe(
            df[['request_id', 'api_key_name', 'created_at', 'model_name',
                'input_tokens', 'output_tokens', 'status', 'error_message']],
            column_config={
                "request_id": "请求 ID",
                "api_key_name": "API 名称",
                "created_at": st.column_config.DatetimeColumn("调用时间"),
                "model_name": "模型",
                "input_tokens": st.column_config.NumberColumn("输入 Token"),
                "output_tokens": st.column_config.NumberColumn("输出 Token"),
                "status": "状态",
                "error_message": "错误信息"
            },
            hide_index=True,
            use_container_width=True
        )
    else:
        st.info("暂无调用记录")
