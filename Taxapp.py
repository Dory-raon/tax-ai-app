import streamlit as st
import pandas as pd
import numpy as np
import json
from google import genai

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
        df = pd.read_csv('tax_knowledge_db_embedded.csv', encoding='utf-8-sig', engine='python')
        df['Embedding'] = df['Embedding'].apply(lambda x: np.array(json.loads(x)))
        return df
    except Exception as e:
        st.error(f"데이터 로드 실패: {e}")
        st.stop()

st.title("🏛️ 라온헤리티지연구소 세무 컨설팅 AI")
st.markdown("고객의 상황을 분석하여 최적의 세무 솔루션과 요약된 핵심 판례를 제공합니다.")

with st.spinner('지식 데이터베이스를 불러오는 중입니다...'):
    db = load_pre_embedded_data()

# 대화 기록과 판례를 세트로 묶어서 저장할 리스트 (새로운 구조)
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# 기존에 저장된 대화와 판례 세트를 먼저 화면에 모두 그려줍니다.
for turn in st.session_state.chat_history:
    with st.container():
        col1, col2 = st.columns([5, 5])
        with col1:
            with st.chat_message("user"): st.markdown(turn["user"])
            with st.chat_message("assistant"): st.markdown(turn["assistant"])
        with col2:
            st.markdown(turn["cases_html"], unsafe_allow_html=True)
    st.markdown("---") # 질문 세트마다 명확한 구분선 추가

if prompt := st.chat_input("상담 내용을 입력하세요 (예: 전세 낀 상가를 상속받을 경우 세금 문제는?)"):
    
    # 1. 사용자 질문을 임베딩하고 유사 판례 2개 검색
    query_result = client.models.embed_content(model=EMBEDDING_MODEL, contents=prompt)
    query_emb = query_result.embeddings[0].values
    
    db['유사도'] = db['Embedding'].apply(lambda x: cosine_similarity(query_emb, x))
    retrieved = db.sort_values(by='유사도', ascending=False).head(2)
    
    # 2. 판례 디자인 카드 생성 (우측에 들어갈 내용)
    raw_cases = ""
    for i, row in retrieved.iterrows():
        raw_cases += f"사건명: {row['사건명']}\n쟁점: {row.get('쟁점분류','')}\n법령: {row.get('관련법령','')}\n요지: {row['판결요지']}\n\n"
        
    ui_prompt = f"""
    당신은 라온헤리티지연구소의 수석 법률 요약 AI입니다.
    아래 판례 원문을 분석하여, 반드시 아래의 HTML 구조에 맞춰 요약 출력해 주세요.
    단, 텍스트에 절대 강조용 별표(애스터리스크)를 쓰지 마세요.

    [작성 규칙]
    1. 판례번호: 핵심 사건번호 위주로 추출
    2. 주요쟁점 & 판결요지: 4~5줄 이내로 결론만 요약
    3. 관련법령: 실제 법령 내용을 풀어서 3줄 이내로 요약

    [출력 HTML 구조 (이 코드를 반복해서 출력하세요)]
    <div style="background-color: #f8fafc; border-left: 5px solid #2563eb; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">
        <h4 style="color: #1e40af; margin-top: 0; margin-bottom: 15px; font-size: 18px;">📜 판례번호: [추출된 번호]</h4>
        <div style="margin-bottom: 12px;"><strong style="color: #0f172a; font-size: 15px;">📌 주요쟁점:</strong><br><span style="color: #334155; font-size: 14px; line-height: 1.6;">[요약]</span></div>
        <div style="margin-bottom: 12px;"><strong style="color: #0f172a; font-size: 15px;">⚖️ 판결요지:</strong><br><span style="color: #334155; font-size: 14px; line-height: 1.6;">[요약]</span></div>
        <div style="margin-bottom: 0;"><strong style="color: #0f172a; font-size: 15px;">📖 관련법령:</strong><br><span style="color: #334155; font-size: 14px; line-height: 1.6;">[요약]</span></div>
    </div>

    [판례 원본 데이터]
    {raw_cases}
    """
    
    ui_response = client.models.generate_content(model=GENERATION_MODEL, contents=ui_prompt)
    cases_html = ui_response.text.replace("```html", "").replace("```", "")
    
    # 3. AI 답변 생성 (좌측에 들어갈 내용)
    context = "\n\n".join([f"- 사건명: {row['사건명']}\n- 판결요지: {row['판결요지']}" for _, row in retrieved.iterrows()])
    
    ai_prompt = f"""
    당신은 '라온헤리티지연구소'에 소속된 최고 수준의 전문 회계사입니다.
    아래 [참조 판례]를 근거로 정확하고 실무적인 세무 솔루션을 제공하세요.
    
    [필수 규칙]
    1. 첫인사는 "안녕하세요, 라온헤리티지연구소 회계사입니다."로 시작하세요.
    2. 설명 중간에 반드시 제시된 [참조 판례]의 사건번호(예: 2010다18567 등)와 관련 법령을 직접 언급하여 고객이 신뢰감을 느끼도록 하세요.
    3. 문장부호에 절대 강조용 별표(애스터리스크 두 개)를 사용하지 마세요. 깔끔한 평문으로 작성하세요.
    4. 원화 금액을 표시할 때는 숫자 앞에 KRW를 붙이지 마세요.
    
    [참조 판례]
    {context}
    
    [고객질문]
    {prompt}
    """
    
    ai_response = client.models.generate_content(model=GENERATION_MODEL, contents=ai_prompt)
    assistant_reply = ai_response.text
    
    # 4. 방금 진행된 세트를 화면에 즉시 출력
    with st.container():
        col1, col2 = st.columns([5, 5])
        with col1:
            with st.chat_message("user"): st.markdown(prompt)
            with st.chat_message("assistant"): st.markdown(assistant_reply)
        with col2:
            st.markdown(cases_html, unsafe_allow_html=True)
    st.markdown("---")
    
    # 5. 세션 스테이트에 새로운 세트 저장 (다음 질문 때 지워지지 않도록)
    st.session_state.chat_history.append({{
        "user": prompt,
        "assistant": assistant_reply,
        "cases_html": cases_html
    }})
