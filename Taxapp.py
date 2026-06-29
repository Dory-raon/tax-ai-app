import streamlit as st
import pandas as pd
import numpy as np
import json
from google import genai

st.set_page_config(page_title="지능형 세무 판례 검색 AI", page_icon="⚖️", layout="wide")

# API_KEY를 여기에 입력하세요
API_KEY =st.secrets[AQ.Ab8RN6JfCaGlKEdQRBS0_p5-yLkd5pcbENGBMgLWDHnVzdc5Pw]
client = genai.Client(api_key=API_KEY)

GENERATION_MODEL = 'gemini-2.5-flash'
EMBEDDING_MODEL = 'gemini-embedding-001'

def cosine_similarity(a, b):
    a, b = np.array(a), np.array(b)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

@st.cache_data
def load_pre_embedded_data():
    try:
        # 방금 공장에서 만든 완성본 엑셀을 불러옵니다.
        df = pd.read_csv('tax_knowledge_db_embedded.csv', encoding='utf-8-sig', engine='python')
        
        # 텍스트 형태(JSON)로 저장된 숫자 좌표를 다시 파이썬 배열로 변환합니다.
        df['Embedding'] = df['Embedding'].apply(lambda x: np.array(json.loads(x)))
        return df
    except Exception as e:
        st.error(f"데이터 로드 실패: 공장 스크립트(make_db.py)가 정상적으로 완료되었는지 확인해주세요. / 에러: {e}")
        st.stop()

st.title("⚖️ 지능형 세무 판례 검색 AI (광속 로딩 버전)")

# 앱이 켜질 때 단 1초 만에 완료되는 구간입니다.
with st.spinner('사전 학습된 데이터베이스를 불러오는 중입니다...'):
    db = load_pre_embedded_data()

if "messages" not in st.session_state:
    st.session_state.messages = []

col1, col2 = st.columns([6, 4])
with col1:
    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])

if prompt := st.chat_input("세무 상담 내용을 입력하세요"):
    with col1:
        with st.chat_message("user"): st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # 고객 질문 딱 하나만 임베딩 (결제를 하셨으니 이제 이 구간도 절대 막히지 않습니다)
    query_result = client.models.embed_content(model=EMBEDDING_MODEL, contents=prompt)
    query_emb = query_result.embeddings[0].values
    
    db['유사도'] = db['Embedding'].apply(lambda x: cosine_similarity(query_emb, x))
    
    # 가장 문맥이 비슷한 상위 3개 판례 추출
    retrieved = db.sort_values(by='유사도', ascending=False).head(3)
    
    with col2:
        st.subheader("📚 시스템이 참조한 유사 판례")
        for idx, row in retrieved.iterrows():
            with st.expander(f"📖 {row['사건명']} (매칭률: {round(row['유사도']*100, 1)}%)", expanded=True):
                st.write(f"판결요지: {row['판결요지']}")
    
    context = "\n\n".join([f"- 사건명: {row['사건명']}\n- 판결요지: {row['판결요지']}" for _, row in retrieved.iterrows()])
    ai_prompt = f"당신은 대한민국 최고의 세무사입니다. 다음 판례를 근거로 세무 상담을 해주세요.\n\n[판례]\n{context}\n\n[고객질문]\n{prompt}"
    
    with col1:
        with st.chat_message("assistant"):
            response = client.models.generate_content(model=GENERATION_MODEL, contents=ai_prompt)
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
