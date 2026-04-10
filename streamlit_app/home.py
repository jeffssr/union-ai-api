import streamlit as st
import pandas as pd
import time
import io
from datetime import date, datetime, timedelta
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
    set_auto_switch_status,
    create_user,
    get_user,
    update_user_password,
    has_users,
    verify_password
)
import hashlib
import base64

st.set_page_config(
    page_title="Union-AI-API",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS样式
st.markdown("""
<style>
    .stMainBlockContainer {padding-top: 2rem;}
    div[data-testid="stSidebar"] > div:first-child {padding-top: 1rem;}
    .stButton > button {width: 100%;}
    .model-header {font-size: 1.1rem; font-weight: bold;}
    
    /* 卡片样式 */
    .model-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 15px;
        padding: 20px;
        margin: 10px 0;
        color: white;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        transition: transform 0.2s;
    }
    .model-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0,0,0,0.15);
    }
    .model-card.available {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
    }
    .model-card.unavailable {
        background: linear-gradient(135deg, #bdc3c7 0%, #2c3e50 100%);
    }
    .status-dot {
        display: inline-block;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        margin-right: 8px;
    }
    .status-dot.available {
        background-color: #00ff88;
        box-shadow: 0 0 10px #00ff88;
    }
    .status-dot.unavailable {
        background-color: #888;
    }
    .model-name {
        font-size: 1.3rem;
        font-weight: bold;
        margin-bottom: 10px;
    }
    .model-info {
        font-size: 0.9rem;
        opacity: 0.95;
        margin: 5px 0;
    }
    .default-badge {
        background: rgba(255,255,255,0.2);
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 0.8rem;
        margin-left: 10px;
    }
</style>
""", unsafe_allow_html=True)

# 初始化session state
if "current_page" not in st.session_state:
    st.session_state.current_page = "📊 数据概览"
if "is_logged_in" not in st.session_state:
    st.session_state.is_logged_in = False
if "username" not in st.session_state:
    st.session_state.username = None
if "show_register" not in st.session_state:
    st.session_state.show_register = False
if "copy_model_data" not in st.session_state:
    st.session_state.copy_model_data = None
if "show_add_model" not in st.session_state:
    st.session_state.show_add_model = False

def generate_auth_token(username):
    """生成认证 token"""
    timestamp = str(int(datetime.now().timestamp()))
    token_data = f"{username}:{timestamp}"
    token_hash = hashlib.sha256(f"{token_data}:union_ai_secret".encode()).hexdigest()[:16]
    auth_token = f"{token_data}:{token_hash}"
    return base64.b64encode(auth_token.encode()).decode()

def verify_auth_token(token_b64):
    """验证认证 token"""
    if not token_b64:
        return None
    try:
        auth_token = base64.b64decode(token_b64.encode()).decode()
        parts = auth_token.split(":")
        if len(parts) != 3:
            return None
        username, timestamp, token_hash = parts
        # 验证token是否过期（7天）
        token_time = datetime.fromtimestamp(int(timestamp))
        if datetime.now() - token_time > timedelta(days=7):
            return None
        # 验证hash
        expected_hash = hashlib.sha256(f"{username}:{timestamp}:union_ai_secret".encode()).hexdigest()[:16]
        if token_hash != expected_hash:
            return None
        # 验证用户是否存在
        user = get_user(username)
        if user:
            return username
        return None
    except:
        return None

def login_user(username, password):
    """用户登录验证"""
    user = get_user(username)
    if user and verify_password(password, user['password_hash'], user['salt']):
        return True
    return False

def logout():
    """退出登录"""
    st.session_state.is_logged_in = False
    st.session_state.username = None
    # 清除所有认证相关的 query params 和 cookie
    st.query_params.clear()
    st.markdown("""
    <script>
    document.cookie = "union_ai_auth=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/; SameSite=Lax";
    sessionStorage.removeItem('union_ai_auth');
    </script>
    """, unsafe_allow_html=True)
    st.rerun()

def show_login_page():
    """显示登录页面"""
    # 居中显示标题
    st.markdown("""
        <h1 style='text-align: center;'>🤖 Union-AI-API</h1>
    """, unsafe_allow_html=True)
    
    # 检查是否已有用户
    if not has_users():
        st.session_state.show_register = True
        st.rerun()
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            username = st.text_input("用户名", placeholder="请输入用户名")
            password = st.text_input("密码", type="password", placeholder="请输入密码")
            submitted = st.form_submit_button("登录", use_container_width=True)
            
            if submitted:
                if not username or not password:
                    st.error("请输入用户名和密码")
                elif login_user(username, password):
                    st.session_state.is_logged_in = True
                    st.session_state.username = username
                    # 设置 cookie 和 query param
                    auth_token = generate_auth_token(username)
                    expires_date = (datetime.now() + timedelta(days=7)).strftime("%a, %d %b %Y %H:%M:%S GMT")
                    st.markdown(f"""
                    <script>
                    document.cookie = "union_ai_auth={auth_token}; expires={expires_date}; path=/; SameSite=Lax";
                    sessionStorage.setItem('union_ai_auth', '{auth_token}');
                    </script>
                    """, unsafe_allow_html=True)
                    # 同时设置 query param 作为备份
                    st.query_params["auth"] = auth_token
                    st.success("登录成功！")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("用户名或密码错误")

def show_register_page():
    """显示注册页面"""
    # 居中显示标题
    st.markdown("""
        <h1 style='text-align: center;'>🤖 Union-AI-API</h1>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.info("这是首次使用，请创建一个管理员账号")
        
        with st.form("register_form"):
            username = st.text_input("用户名", placeholder="请输入用户名")
            password = st.text_input("密码", type="password", placeholder="请输入密码")
            confirm_password = st.text_input("确认密码", type="password", placeholder="请再次输入密码")
            submitted = st.form_submit_button("注册", use_container_width=True)
            
            if submitted:
                if not username or not password:
                    st.error("请输入用户名和密码")
                elif password != confirm_password:
                    st.error("两次输入的密码不一致")
                elif len(password) < 4:
                    st.error("密码长度至少为4位")
                else:
                    if create_user(username, password):
                        st.success("注册成功！请登录")
                        st.session_state.show_register = False
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("用户名已存在")

def show_change_password():
    """显示修改密码对话框"""
    with st.expander("🔐 修改密码"):
        with st.form("change_password_form"):
            old_password = st.text_input("当前密码", type="password")
            new_password = st.text_input("新密码", type="password")
            confirm_new_password = st.text_input("确认新密码", type="password")
            submitted = st.form_submit_button("修改密码")
            
            if submitted:
                if not old_password or not new_password:
                    st.error("请填写所有字段")
                elif new_password != confirm_new_password:
                    st.error("两次输入的新密码不一致")
                elif len(new_password) < 4:
                    st.error("新密码长度至少为4位")
                elif not login_user(st.session_state.username, old_password):
                    st.error("当前密码错误")
                else:
                    update_user_password(st.session_state.username, new_password)
                    st.success("密码修改成功！")
                    time.sleep(1)

def export_models_to_excel():
    """导出模型配置到Excel"""
    models = get_all_models()
    if not models:
        return None
    
    df = pd.DataFrame(models)
    export_columns = ['name', 'api_url', 'api_key', 'model_id', 'daily_token_limit', 
                      'daily_call_limit', 'priority', 'is_active', 'is_default_model']
    df_export = df[export_columns].copy()
    df_export.columns = ['模型名称', 'API地址', 'API密钥', 'Model ID', '每日Token上限', 
                         '每日调用上限', '优先级', '是否启用', '是否默认']
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_export.to_excel(writer, index=False, sheet_name='模型配置')
    output.seek(0)
    return output

def import_models_from_excel(uploaded_file):
    """从Excel导入模型配置"""
    try:
        df = pd.read_excel(uploaded_file)
        column_mapping = {}
        expected_columns = {
            'name': ['模型名称', 'name', 'Name'],
            'api_url': ['API地址', 'api_url', 'API URL', 'api url'],
            'api_key': ['API密钥', 'api_key', 'API Key', 'api key'],
            'model_id': ['Model ID', 'model_id', 'model id', 'ModelId'],
            'daily_token_limit': ['每日Token上限', 'daily_token_limit', 'Token Limit'],
            'daily_call_limit': ['每日调用上限', 'daily_call_limit', 'Call Limit'],
            'priority': ['优先级', 'priority', 'Priority']
        }
        
        for key, possible_names in expected_columns.items():
            for col in df.columns:
                if col in possible_names:
                    column_mapping[key] = col
                    break
        
        if 'name' not in column_mapping or 'api_url' not in column_mapping or 'api_key' not in column_mapping:
            return False, "Excel文件缺少必要的列（模型名称、API地址、API密钥）"
        
        success_count = 0
        for _, row in df.iterrows():
            try:
                name = str(row[column_mapping.get('name', 'name')])
                api_url = str(row[column_mapping.get('api_url', 'api_url')])
                api_key = str(row[column_mapping.get('api_key', 'api_key')])
                
                if not name or not api_url or not api_key:
                    continue
                
                model_id = str(row.get(column_mapping.get('model_id', 'model_id'), ''))
                daily_token_limit = int(row.get(column_mapping.get('daily_token_limit', 'daily_token_limit'), 100000))
                daily_call_limit = int(row.get(column_mapping.get('daily_call_limit', 'daily_call_limit'), 1000))
                priority = int(row.get(column_mapping.get('priority', 'priority'), 0))
                
                create_model(name, api_url, api_key, model_id, daily_token_limit, daily_call_limit, priority)
                success_count += 1
            except Exception as e:
                continue
        
        return True, f"成功导入 {success_count} 个模型配置"
    except Exception as e:
        return False, f"导入失败：{str(e)}"

def render_model_cards(stats):
    """渲染模型卡片列表"""
    sorted_stats = sorted(stats, key=lambda x: x['priority'], reverse=True)
    cols_per_row = 3
    for i in range(0, len(sorted_stats), cols_per_row):
        cols = st.columns(cols_per_row)
        for j, col in enumerate(cols):
            idx = i + j
            if idx < len(sorted_stats):
                stat = sorted_stats[idx]
                with col:
                    remaining_tokens = stat['daily_token_limit'] - stat['used_tokens']
                    remaining_calls = stat['daily_call_limit'] - stat['used_calls']
                    is_available = (stat['used_tokens'] < stat['daily_token_limit'] and 
                                   stat['used_calls'] < stat['daily_call_limit'] and 
                                   stat['is_active'] == 1)
                    
                    card_class = "available" if is_available else "unavailable"
                    dot_class = "available" if is_available else "unavailable"
                    status_text = "可用" if is_available else "不可用"
                    default_badge = "<span class='default-badge'>默认</span>" if stat['is_default_model'] == 1 else ""
                    
                    st.markdown(f"""
                        <div class="model-card {card_class}">
                            <div class="model-name">
                                <span class="status-dot {dot_class}"></span>
                                {stat['name']}{default_badge}
                            </div>
                            <div class="model-info">Model ID: {stat.get('model_id', 'N/A')}</div>
                            <div class="model-info">Token: {stat['used_tokens']:,} / {stat['daily_token_limit']:,}</div>
                            <div class="model-info">调用: {stat['used_calls']:,} / {stat['daily_call_limit']:,}</div>
                            <div class="model-info">优先级: {stat['priority']}</div>
                            <div class="model-info">状态: {status_text}</div>
                        </div>
                    """, unsafe_allow_html=True)

# 页面加载时检查认证状态（通过 query params）
if not st.session_state.is_logged_in:
    auth_param = st.query_params.get("auth")
    if auth_param:
        verified_user = verify_auth_token(auth_param)
        if verified_user:
            st.session_state.is_logged_in = True
            st.session_state.username = verified_user

# 主程序
if not st.session_state.is_logged_in:
    if st.session_state.show_register or not has_users():
        show_register_page()
    else:
        show_login_page()
else:
    # 已登录，显示主界面
    pages = {
        "📊 数据概览": "dashboard",
        "🔧 模型配置": "models",
        "🔑 API Key": "apikeys",
        "📋 调用记录": "logs"
    }
    
    with st.sidebar:
        st.title("🤖 union-ai-api")
        st.divider()
        
        st.markdown(f"**👤 {st.session_state.username}**")
        
        show_change_password()
        
        if st.button("🚪 退出登录", use_container_width=True):
            logout()
        
        st.divider()
        
        for page_name in pages.keys():
            if st.button(page_name, use_container_width=True, 
                        type="primary" if st.session_state.current_page == page_name else "secondary"):
                st.session_state.current_page = page_name
                st.rerun()
        
        st.divider()
        st.caption("© 2026 AI Proxy")
    
    page = pages[st.session_state.current_page]
    
    if page == "dashboard":
        st.header("📊 数据概览 - 今日用量")
        
        stats = get_daily_stats()
        
        if not stats:
            st.info("暂无模型配置，请前往「模型配置」添加模型")
        else:
            render_model_cards(stats)
            
            st.divider()
            st.subheader("详细数据")
            df = pd.DataFrame(stats)
            df['剩余 Token'] = df['daily_token_limit'] - df['used_tokens']
            df['剩余调用次数'] = df['daily_call_limit'] - df['used_calls']
            df['Token 使用率'] = (df['used_tokens'] / df['daily_token_limit'] * 100).round(1).astype(str) + '%'
            df['调用使用率'] = (df['used_calls'] / df['daily_call_limit'] * 100).round(1).astype(str) + '%'
            df['是否可用'] = df.apply(lambda x: '✅ 可用' if (x['used_tokens'] < x['daily_token_limit'] and 
                                                              x['used_calls'] < x['daily_call_limit'] and 
                                                              x['is_active'] == 1) else '❌ 不可用', axis=1)
            df['默认模型'] = df['is_default_model'].apply(lambda x: '📌 是' if x == 1 else '')
            
            display_df = df[['name', 'model_id', '是否可用', 'used_calls', 'daily_call_limit', '剩余调用次数', 
                            '调用使用率', 'used_tokens', 'daily_token_limit', '剩余 Token', 'Token 使用率', 
                            '默认模型', 'priority']].copy()
            display_df.columns = ['模型名称', 'Model ID', '是否可用', '已用调用', '调用限额', '剩余调用', 
                                 '调用使用率', '已用 Token', 'Token 限额', '剩余 Token', 'Token 使用率', 
                                 '默认模型', '优先级']
            st.dataframe(display_df, hide_index=True, use_container_width=True)
    
    elif page == "models":
        st.header("🔧 模型配置")
        
        models = get_all_models()
        
        col1, col2, col3 = st.columns([1, 1, 3])
        with col1:
            excel_data = export_models_to_excel()
            if excel_data:
                st.download_button(
                    label="📤 导出配置",
                    data=excel_data,
                    file_name=f"models_export_{date.today().isoformat()}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            else:
                st.button("📤 导出配置", disabled=True, use_container_width=True)

        with col2:
            with st.expander("📥 导入配置"):
                st.markdown("### 导入模型配置")
                uploaded_file = st.file_uploader("选择Excel文件", type=['xlsx', 'xls'], key="import_file")
                if uploaded_file is not None:
                    if st.button("开始导入", key="btn_import"):
                        success, message = import_models_from_excel(uploaded_file)
                        if success:
                            st.success(message)
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(message)
        
        with col3:
            pass
        
        st.divider()
        
        st.subheader("⚙️ 全局设置")
        auto_switch_global = st.checkbox(
            "✅ 启用自动切换模型",
            value=get_auto_switch_status()
        )
        if auto_switch_global != get_auto_switch_status():
            set_auto_switch_status(auto_switch_global)
            st.success("✅ 设置已保存")
            time.sleep(0.5)
            st.rerun()
        st.caption("💡 提示：开启后：系统按优先级自动切换所有启用的模型 | 关闭后：所有请求固定使用下方选择的默认模型，请确保下方已选择默认模型，否则所有请求将失败")
        
        st.divider()
        
        st.subheader("📋 模型列表")
        
        with st.expander("➕ 添加新模型", expanded=st.session_state.show_add_model):
            copy_data = st.session_state.copy_model_data
            
            with st.form("add_model_form", clear_on_submit=True):
                name = st.text_input("模型名称", 
                                    value=copy_data['name'] if copy_data else "", 
                                    placeholder="例如：GPT-4")
                api_url = st.text_input("API 地址", 
                                       value=copy_data['api_url'] if copy_data else "", 
                                       placeholder="https://api.openai.com/v1/chat/completions")
                api_key = st.text_input("API Key", 
                                       value=copy_data['api_key'] if copy_data else "", 
                                       type="password")
                model_id = st.text_input("Model ID（选填，如 gpt-4、claude-3 等）", 
                                        value=copy_data['model_id'] if copy_data else "", 
                                        placeholder="如留空则使用请求中的 model 参数")
                col1, col2 = st.columns(2)
                with col1:
                    daily_limit = st.number_input("每日 Token 上限", 
                                                  value=copy_data['daily_token_limit'] if copy_data else 100000, 
                                                  min_value=1)
                with col2:
                    daily_call_limit = st.number_input("每日调用次数上限", 
                                                       value=copy_data['daily_call_limit'] if copy_data else 1000, 
                                                       min_value=1)
                priority = st.number_input("优先级 (数字越大越优先)", 
                                          value=copy_data['priority'] if copy_data else 0, 
                                          min_value=0)
                
                submitted = st.form_submit_button("添加模型")
                if submitted:
                    if name and api_url and api_key:
                        create_model(name, api_url, api_key, model_id, daily_limit, daily_call_limit, priority)
                        st.success(f"✅ 模型添加成功！")
                        st.session_state.copy_model_data = None
                        st.session_state.show_add_model = False
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
                    col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 4])
                    with col_btn1:
                        if st.button("📋 复制配置", key=f"copy_{model['config_id']}"):
                            st.session_state.copy_model_data = {
                                'name': model['name'] + ' (复制)',
                                'api_url': model['api_url'],
                                'api_key': model['api_key'],
                                'model_id': model.get('model_id', ''),
                                'daily_token_limit': model['daily_token_limit'],
                                'daily_call_limit': model['daily_call_limit'],
                                'priority': model['priority']
                            }
                            st.session_state.show_add_model = True
                            st.rerun()
                    
                    with col_btn2:
                        pass
                    
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
