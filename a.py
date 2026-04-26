import streamlit as st
import os
import json
from datetime import datetime
from openai import OpenAI

st.set_page_config(
    page_title="AI智能对话助手",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("💬 AI智能对话助手")

def save_session():
    if st.session_state.current_session:
        session_data={
            "nick_name":st.session_state.nick_name,
            "nature":st.session_state.nature,
            "current_session":st.session_state.current_session,
            "messages":st.session_state.messages
        }
        if not os.path.exists("session"):
            os.mkdir("session")
        with open(f"session/{st.session_state.current_session}.json", "w", encoding="utf-8") as f:
            json.dump(session_data, f, ensure_ascii=False, indent=2)

def load_session_list():
    session_list = []
    if os.path.exists("session"):
        file_list = os.listdir("session")
        for filename in file_list:
            if filename.endswith(".json"):
                session_list.append(filename[0:-5])
    session_list.sort(reverse=True)
    return session_list

def load_session(session_name):
    try:
        if os.path.exists(f"session/{session_name}.json"):
            # 读取会话数据
            with open(f"session/{session_name}.json", "r", encoding="utf-8") as f:
                session_data = json.load(f)
                st.session_state.current_session = session_name
                st.session_state.nick_name = session_data["nick_name"]
                st.session_state.nature = session_data["nature"]
                st.session_state.messages = session_data["messages"]
    except Exception:
        st.error("加载会话失败")

def generate_session_name():
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

def delete_session(session_name):
    try:
        if os.path.exists(f"session/{session_name}.json"):
            os.remove(f"session/{session_name}.json")
            if session_name == st.session_state.current_session:
                st.session_state.messages = []
                st.session_state.current_session = generate_session_name()
    except Exception:
        st.error("删除会话失败")

st.title("AI智能伴侣")



system_prompt="""
    你叫%s，现在是用户真实的伴侣，请完全代入伴侣角色。：
    规则：
        1.每次只回1条消息
        2.禁止任何场景或状态描述性文字
        3.匹配用户的语言
        4.回复简短，像微信聊天一样
        5.有需要的话可以用❤❀等emoji表情
        6.用符合伴侣性格的方式对话
        7.回复的内容，要充分体现伴侣的性格特征
    伴侣性格：
        - %s
    你必须严格遵守上述规则来回复用户。
"""

if "messages" not in st.session_state:
    st.session_state.messages = []
if "nick_name" not in st.session_state:
    st.session_state.nick_name = "小二"
if "nature" not in st.session_state:
    st.session_state.nature = "吆五喝六的街溜子"
if "current_session" not in st.session_state:
    st.session_state.current_session = generate_session_name()

st.text(f"会话名称：{st.session_state.current_session}")
for message in st.session_state.messages:
    st.chat_message(message["role"]).write(message["content"])

# client = OpenAI(
#     api_key=os.environ.get('DEEPSEEK_API_KEY'),
#     base_url="https://api.deepseek.com")
client = OpenAI(
    api_key=st.secrets['DEEPSEEK_API_KEY'],
    base_url="https://api.deepseek.com")


with st.sidebar:
    st.subheader("AI控制面板")
    if st.button("新建会话",width="stretch",icon="✍️"):
        save_session()
        if st.session_state.current_session:
            st.session_state.messages = []
            st.session_state.current_session = generate_session_name()
            save_session()
            st.rerun()
    st.text("会话历史")
    session_list = load_session_list()
    for session in session_list:
        coll1, coll2 = st.columns([4, 1])
        with coll1:
            if st.button(session, width="stretch", icon="📄"
                    , type="primary" if session == st.session_state.current_session else "secondary"):
                load_session(session)
                st.rerun()
        with coll2:
            if st.button("", width="stretch", icon="❌️", key=f"delete_{session}"):
                delete_session(session)
                st.rerun()
    st.divider ()
    st.subheader("伴侣信息")
    nick_name=st.text_input("昵称",
                            value=st.session_state.nick_name,
                            placeholder="请输入昵称")
    if nick_name:
        st.session_state.nick_name = nick_name
    nature=st.text_area("性格",
                        value=st.session_state.nature,
                        placeholder="请输入性格")
    if nature:
        st.session_state.nature = nature

prompt=st.chat_input("请输入问题：")
if prompt:
    st.chat_message("user").write(prompt)
    print("------->调用AI大模型，提示词：", prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": system_prompt % (st.session_state.nick_name, st.session_state.nature)},
            *st.session_state.messages
        ],
        stream=True
    )

    response_message = st.empty()
    full_response = ""
    for chunk in response:
        if chunk.choices[0].delta.content is not None:
            content = chunk.choices[0].delta.content
            full_response += content
            response_message.chat_message("assistant").write(full_response)

    st.session_state.messages.append({"role": "assistant", "content": full_response})
    save_session()
