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

with st.spinner('지식 데이터베이스를 불러오는 중입니다...'):
    db = load_pre_embedded_data()

if "messages" not in st.session_state:
    st.session_state.messages = []

col1, col2 = st.columns([6, 4])
with col1:
    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])

if prompt := st.chat_input("상담 내용을 입력하세요 (예: 상속세 공제 한도 등)"):
    with col1:
        with st.chat_message("user"): st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    query_result = client.models.embed_content(model=EMBEDDING_MODEL, contents=prompt)
    query_emb = query_result.embeddings[0].values
    
    db['유사도'] = db['Embedding'].apply(lambda x: cosine_similarity(query_emb, x))
    retrieved = db.sort_values(by='유사도', ascending=False).head(3)
    
    with col2:
        st.subheader("참조 유사 판례")
        for idx, row in retrieved.iterrows():
            
            # 제목 표시줄에 쟁점과 매칭률을 직관적으로 표기
            with st.expander(f"[{row.get('쟁점분류', '미분류')}] 유사도: {round(row['유사도']*100, 1)}%", expanded=True):
                
                # 가독성을 높인 메타데이터 배치
                st.markdown("판례번호: " + str(row['사건명']))
                st.markdown("주요주제: " + str(row.get('쟁점분류', '미분류')))
                st.markdown("관련법령: " + str(row.get('관련법령', '관련 법령 없음')))
                
                st.markdown("---")
                
                # 판시사항을 색상 박스로 묶어서 시각적 피로도 감소
                st.markdown("판시사항:")
                st.info(row['판결요지'])
    
    context = "\n\n".join([f"- 사건명: {row['사건명']}\n- 판결요지: {row['판결요지']}" for _, row in retrieved.iterrows()])
    
    # 페르소나 주입: 라온헤리티지연구소 회계사로 정체성 고정
    ai_prompt = f"당신은 라온헤리티지연구소에 소속된 전문 회계사입니다. 다음 제공된 판례를 근거로 논리적이고 전문적인 세무 상담을 제공해주세요.\n\n[판례]\n{context}\n\n[고객질문]\n{prompt}"
    
    with col1:
        with st.chat_message("assistant"):
            response = client.models.generate_content(model=GENERATION_MODEL, contents=ai_prompt)
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
