import streamlit as st
import pandas as pd
import numpy as np
import json
import re
from google import genai

# 라온헤리티지연구소 브랜딩 적용
st.set_page_config(page_title="라온헤리티지연구소 세무 AI", page_icon="🏛️", layout="wide")

API_KEY = st.secrets["GEMINI_API_KEY"] # (로컬 테스트 시에는 진짜 키를 문자열로 넣으세요)
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

# 메인 타이틀
st.title("🏛️ 라온헤리티지연구소 세무 컨설팅 AI")
st.markdown("고객의 상황을 분석하여 최적의 세무 솔루션과 요약된 핵심 판례를 제공합니다.")

with st.spinner('지식 데이터베이스를 불러오는 중입니다...'):
    db = load_pre_embedded_data()

if "messages" not in st.session_state:
    st.session_state.messages = []

col1, col2 = st.columns([5, 5]) # 화면 비율을 5:5로 맞춰 우측 판례가 예쁘게 보이도록 조정
with col1:
    st.subheader("💬 실시간 세무 상담")
    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])

if prompt := st.chat_input("상담 내용을 입력하세요 (예: 전세 낀 상가를 상속받을 경우 세금 문제는?)"):
    with col1:
        with st.chat_message("user"): st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # 1. 질문 임베딩 및 유사 판례 2개 검색 (가독성을 위해 2개만 추출)
    query_result = client.models.embed_content(model=EMBEDDING_MODEL, contents=prompt)
    query_emb = query_result.embeddings[0].values
    
    db['유사도'] = db['Embedding'].apply(lambda x: cosine_similarity(query_emb, x))
    retrieved = db.sort_values(by='유사도', ascending=False).head(2)
    
    # 2. 우측 화면(판례) 요약 및 디자인 생성
    with col2:
        st.subheader("📚 관련 핵심 판례 브리핑")
        ui_placeholder = st.empty()
        ui_placeholder.info("원문 판례를 실무진이 보기 편하게 요약하고 있습니다...")
        
        # 날것의 데이터를 텍스트로 모음
        raw_cases = ""
        for i, row in retrieved.iterrows():
            raw_cases += f"사건명: {row['사건명']}\n쟁점: {row.get('쟁점분류','')}\n법령: {row.get('관련법령','')}\n요지: {row['판결요지']}\n\n"
            
        # 제미나이에게 예쁜 디자인 카드(HTML)로 요약해달라고 지시
        ui_prompt = f"""
        당신은 라온헤리티지연구소의 수석 법률 요약 AI입니다.
        아래 판례 원문을 분석하여, 반드시 아래의 HTML 구조에 맞춰 '예쁘고 간결하게' 요약 출력해 주세요.

        [작성 규칙]
        1. 판례번호: '대법원 2010.2.11 선고 2009다71578' 등에서 '2009다71578' 처럼 핵심 사건번호 위주로 추출할 것.
        2. 주요쟁점 & 판결요지: 복잡한 사실관계는 쳐내고, 결론 위주로 '최대 4~5줄'을 절대 넘지 않게 요약할 것.
        3. 관련법령: 단순히 조문 번호만 쓰지 말고, 해당 조문이 어떤 내용인지 실제 법령 내용을 풀어서 3줄 이내로 적어줄 것.

        [출력 HTML 구조 (이 코드를 반복해서 출력하세요)]
        <div style="background-color: #f8fafc; border-left: 5px solid #2563eb; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">
            <h4 style="color: #1e40af; margin-top: 0; margin-bottom: 15px; font-size: 18px;">📜 판례번호: [추출된 번호]</h4>
            <div style="margin-bottom: 12px;"><strong style="color: #0f172a; font-size: 15px;">📌 주요쟁점:</strong><br><span style="color: #334155; font-size: 14px; line-height: 1.6;">[2~3줄 요약]</span></div>
            <div style="margin-bottom: 12px;"><strong style="color: #0f172a; font-size: 15px;">⚖️ 판결요지:</strong><br><span style="color: #334155; font-size: 14px; line-height: 1.6;">[5줄 이내 결론 요약]</span></div>
            <div style="margin-bottom: 0;"><strong style="color: #0f172a; font-size: 15px;">📖 관련법령:</strong><br><span style="color: #334155; font-size: 14px; line-height: 1.6;">[조문 번호 및 실제 내용 요약]</span></div>
        </div>

        [판례 원본 데이터]
        {raw_cases}
        """
        
        # 요약된 HTML 결과물을 우측 화면에 렌더링
        ui_response = client.models.generate_content(model=GENERATION_MODEL, contents=ui_prompt)
        clean_html = ui_response.text.replace("```html", "").replace("```", "")
        ui_placeholder.markdown(clean_html, unsafe_allow_html=True)
        
    # 3. 좌측 화면(채팅) 라온헤리티지 소속 AI 답변 생성
    context = "\n\n".join([f"- 사건명: {row['사건명']}\n- 판결요지: {row['판결요지']}" for _, row in retrieved.iterrows()])
    
    ai_prompt = f"""
    당신은 '라온헤리티지연구소'에 소속된 최고 수준의 전문 회계사입니다.
    고객의 상황에 깊이 공감하면서도, 아래 [참조 판례]를 근거로 정확하고 실무적인 세무 솔루션을 제공하세요.
    답변은 언제나 "안녕하세요, 라온헤리티지연구소 회계사입니다."와 같은 소속감 있는 인사로 시작해야 합니다.
    
    [참조 판례]
    {context}
    
    [고객질문]
    {prompt}
    """
    
    with col1:
        with st.chat_message("assistant"):
            response = client.models.generate_content(model=GENERATION_MODEL, contents=ai_prompt)
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
