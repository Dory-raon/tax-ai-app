import streamlit as st
import pandas as pd
import numpy as np
import json
from google import genai
import design # 분리해 둔 디자인 모듈을 불러옵니다.

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
        # 파일명에 .gz를 붙이고 압축 해제 옵션을 추가합니다.
        df = pd.read_csv('tax_knowledge_db_embedded.csv.gz', encoding='utf-8-sig', engine='python', compression='gzip')
        df['Embedding'] = df['Embedding'].apply(lambda x: np.array(json.loads(x)))
        return df
    except Exception as e:
        st.error(f"데이터 로드 실패: {e}")
        st.stop()

st.title("🏛️ 라온헤리티지연구소 세무 컨설팅 AI")
st.markdown("고객의 상황을 분석하여 최적의 세무 솔루션과 요약된 핵심 판례를 제공합니다.")

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

if prompt := st.chat_input("상담 내용을 입력하세요 (예: 전세 낀 상가를 상속받을 경우 세금 문제는?)"):
    
    # 1. 벡터 엔진 검색 로직
    query_result = client.models.embed_content(model=EMBEDDING_MODEL, contents=prompt)
    query_emb = query_result.embeddings[0].values
    db['유사도'] = db['Embedding'].apply(lambda x: cosine_similarity(query_emb, x))
    retrieved = db.sort_values(by='유사도', ascending=False).head(2)
    
    # 2. 판례 디자인 생성 (design.py에서 템플릿 호출)
    raw_cases = ""
    for i, row in retrieved.iterrows():
        raw_cases += f"사건명: {row['사건명']}\n쟁점: {row.get('쟁점분류','')}\n법령: {row.get('관련법령','')}\n요지: {row['판결요지']}\n\n"
        
    ui_prompt = design.get_case_card_prompt(raw_cases) # 외부 모듈 사용
    ui_response = client.models.generate_content(model=GENERATION_MODEL, contents=ui_prompt)
    cases_html = ui_response.text.replace("```html", "").replace("```", "")
    
    # 3. AI 답변 생성 (design.py에서 템플릿 호출)
    context = "\n\n".join([f"- 사건명: {row['사건명']}\n- 판결요지: {row['판결요지']}" for _, row in retrieved.iterrows()])
    ai_prompt = design.get_assistant_prompt(context, prompt) # 외부 모듈 사용
    ai_response = client.models.generate_content(model=GENERATION_MODEL, contents=ai_prompt)
    assistant_reply = ai_response.text
    
    # 4. 화면 출력 및 저장
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
