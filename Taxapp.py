import streamlit as st
import pandas as pd
import numpy as np
import json
import os
from google import genai
import design 

st.set_page_config(page_title="라온헤리티지연구소 세무 AI", page_icon="🏛️", layout="wide")

API_KEY = st.secrets["GEMINI_API_KEY"]
client = genai.Client(api_key=API_KEY)

GENERATION_MODEL = 'gemini-2.5-flash'
EMBEDDING_MODEL = 'gemini-embedding-001'

def cosine_similarity(a, b):
    a, b = np.array(a), np.array(b)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

@st.cache_data
def load_pre_embedded_data():
    try:
        df = pd.read_csv('tax_knowledge_db_embedded.csv.gz', encoding='utf-8-sig', engine='python', compression='gzip')
        df['Embedding'] = df['Embedding'].apply(lambda x: np.array(json.loads(x)))
        return df
    except Exception as e:
        st.error(f"데이터 로드 실패: {e}")
        st.stop()

# ==========================================
# 사이드바 (고객 사전 문진표)
# ==========================================
with st.sidebar:
    if os.path.exists("logo.png"):
        st.image("logo.png", use_container_width=True)
    else:
        st.markdown("<h2 style='text-align: center; color: #1e3a8a;'>라온헤리티지연구소</h2>", unsafe_allow_html=True)
    
    st.markdown("---")
    st.subheader("📋 고객 상황 체크리스트")
    st.caption("배경지식을 입력하시면 맞춤형 절세 플랜이 제공됩니다.")
    
    family_spouse = st.radio("배우자 생존 여부", ["있음 (배우자공제 가능)", "없음 (일괄공제 5억 적용)"], index=0)
    family_kids = st.number_input("자녀 수 (명)", min_value=0, max_value=10, value=2)
    asset_size = st.selectbox("예상 총 자산 규모", ["10억 미만 (상속세 면제 가능성 높음)", "10억 ~ 30억 (전략적 분배 필요)", "30억 ~ 50억 (사전증여 필수)", "50억 이상 (가업승계/신탁 고려)"])
    asset_types = st.multiselect("주요 보유 자산 (다중 선택)", ["거주용 주택/아파트", "상가/빌딩 (수익형 부동산)", "현금 및 예적금", "비상장 주식 (가업/법인)"])
    primary_goal = st.selectbox("컨설팅 주요 목적", ["상속세/증여세 최소화", "상속세 납부 재원 마련", "자녀 간 분쟁 없는 원활한 분배", "가업 승계 및 경영권 방어"])

user_profile = f"배우자: {family_spouse}, 자녀 수: {family_kids}명, 자산규모: {asset_size}, 주요자산: {', '.join(asset_types)}, 주요목적: {primary_goal}"

# ==========================================
# 메인 화면
# ==========================================
st.title("🏛️ 맞춤형 상속/증여 컨설팅 AI")
st.markdown("사이드바에 고객님의 상황을 입력한 뒤 질문하시면, 라온헤리티지연구소의 축적된 판례를 바탕으로 최적의 솔루션을 제공합니다.")

with st.spinner('지식 데이터베이스를 불러오는 중입니다...'):
    db = load_pre_embedded_data()

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

for turn in st.session_state.chat_history:
    with st.container():
        col1, col2 = st.columns([5, 5])
        with col1:
            with st.chat_message("user"): st.markdown(turn["user"])
            with st.chat_message("assistant"): st.markdown(turn["assistant"])
        with col2:
            st.markdown(turn["cases_html"], unsafe_allow_html=True)
    st.markdown("---")

if prompt := st.chat_input("상담 내용을 입력하세요 (예: 상가를 먼저 증여하는게 나을까요, 상속이 나을까요?)"):
    
    # [새로운 기능 1] AI 문지기를 통한 토큰 낭비 방지 (비용 방어)
    gate_prompt = f"다음 질문이 세무, 회계, 상속, 증여, 절세 플랜, 재무 컨설팅과 관련된 질문인지 판별하세요. 맞으면 'O', 전혀 엉뚱한 질문이면 'X'만 출력하세요.\n질문: {prompt}"
    gate_res = client.models.generate_content(model=GENERATION_MODEL, contents=gate_prompt)
    
    if "X" in gate_res.text.upper():
        # 엉뚱한 질문일 경우 정중하게 거절하고 아래의 복잡한 로직을 전부 패스합니다.
        reject_msg = "안녕하세요, 라온헤리티지연구소입니다. 죄송하지만 저는 상속, 증여, 양도 등 세무 및 절세 플랜 컨설팅에 특화된 AI입니다. 세무와 관련된 질문을 남겨주시면 전문적인 판례와 함께 최선을 다해 답변해 드리겠습니다."
        cases_html = "<div style='padding:20px; color:#64748b; font-size:14px; background-color:#f8fafc; border-radius:8px;'>해당 질문은 세무 컨설팅과 관련이 없어 판례 검색이 생략되었습니다.</div>"
        
        with st.container():
            col1, col2 = st.columns([5, 5])
            with col1:
                with st.chat_message("user"): st.markdown(prompt)
                with st.chat_message("assistant"): st.markdown(reject_msg)
            with col2:
                st.markdown(cases_html, unsafe_allow_html=True)
        st.markdown("---")
        
        st.session_state.chat_history.append({
            "user": prompt,
            "assistant": reject_msg,
            "cases_html": cases_html
        })
        
    else:
        # [새로운 기능 2] 답변 생성 중 로딩 문구 표시
        with st.spinner("AI가 관련 판례와 최적의 맞춤형 절세 플랜을 분석 중입니다. 잠시만 기다려주세요..."):
            
            # 검색 및 판례 요약 (무거운 작업)
            query_result = client.models.embed_content(model=EMBEDDING_MODEL, contents=prompt)
            query_emb = query_result.embeddings[0].values
            db['유사도'] = db['Embedding'].apply(lambda x: cosine_similarity(query_emb, x))
            retrieved = db.sort_values(by='유사도', ascending=False).head(2)
            
            raw_cases = ""
            for i, row in retrieved.iterrows():
                raw_cases += f"사건명: {row['사건명']}\n쟁점: {row.get('쟁점분류','')}\n법령: {row.get('관련법령','')}\n요지: {row['판결요지']}\n\n"
                
            ui_prompt = design.get_case_card_prompt(raw_cases) 
            ui_response = client.models.generate_content(model=GENERATION_MODEL, contents=ui_prompt)
            cases_html = ui_response.text.replace("```html", "").replace("```", "")
            
            context = "\n\n".join([f"- 사건명: {row['사건명']}\n- 판결요지: {row['판결요지']}" for _, row in retrieved.iterrows()])
            
            # 최종 답변 생성
            ai_prompt = design.get_assistant_prompt(context, prompt, user_profile) 
            ai_response = client.models.generate_content(model=GENERATION_MODEL, contents=ai_prompt)
            assistant_reply = ai_response.text
        
        # 스피너(로딩)가 끝나면 화면에 결과를 그려줍니다.
        with st.container():
            col1, col2 = st.columns([5, 5])
            with col1:
                with st.chat_message("user"): st.markdown(prompt)
                with st.chat_message("assistant"): st.markdown(assistant_reply)
            with col2:
                st.markdown(cases_html, unsafe_allow_html=True)
        st.markdown("---")
        
        st.session_state.chat_history.append({
            "user": prompt,
            "assistant": assistant_reply,
            "cases_html": cases_html
        })
