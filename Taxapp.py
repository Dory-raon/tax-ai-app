import streamlit as st
import pandas as pd
import numpy as np
import json
import os
from google import genai
import design 

# 딱 한 줄로 로컬 파일을 불러와서 설정합니다. (여기에 'favicon.jpg' 파일이 있어야 합니다)
st.set_page_config(page_title="라온헤리티지연구소 세무 AI", page_icon="favicon.jpg", layout="wide")

design.apply_premium_css()

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
# (사용자ID와 레포지토리명 부분만 대표님 정보로 바꿔주세요)
github_user = "Dory-raon" # 예: RaonHeritage
repo_name = "tax-ai-app" # 레포지토리 이름
logo_url = f"https://raw.githubusercontent.com/{github_user}/{repo_name}/main/favicon.jpg"

st.markdown(f"""
    <div style="display: flex; align-items: center; margin-bottom: 20px;">
        <img src="{logo_url}" width="80" style="margin-right: 20px; border-radius: 12px;">
        <h1 style="margin: 0; color: #1e3a8a; font-size: 42px; line-height: 1.2;">라온헤리티지연구소<br>상속/증여 컨설팅 AI</h1>
    </div>
""", unsafe_allow_html=True)

st.markdown("<p style='color: #475569; font-size: 20px; margin-bottom: 40px;'>사이드바에 고객님의 상황을 입력한 뒤 질문하시면, 라온헤리티지연구소의 축적된 판례를 바탕으로 최적의 솔루션을 제공합니다.</p>", unsafe_allow_html=True)
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

if prompt := st.chat_input("상담 내용을 입력하세요"):
    
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
        with st.spinner("AI가 관련 판례와 라온헤리티지 데이터베이스를 검색하고 맞춤형 절세 플랜을 작성 중입니다..."):
            
            # 검색 (임베딩)
            query_result = client.models.embed_content(model=EMBEDDING_MODEL, contents=prompt)
            query_emb = query_result.embeddings[0].values
            db['유사도'] = db['Embedding'].apply(lambda x: cosine_similarity(query_emb, x))
            retrieved = db.sort_values(by='유사도', ascending=False).head(2)
            
            # 원문 취합 (AI한테 넘겨줄 용도)
            context = ""
            for i, (_, row) in enumerate(retrieved.iterrows()):
                context += f"[판례 {i+1}]\n- 사건명: {row['사건명']}\n- 판결요지: {row['판결요지']}\n\n"
            
            # 🚀 AI에게는 쓸데없는 거 빼고 '요약'과 '답변' 글자만 짧게 뽑으라고 시킵니다!
            fast_prompt = design.get_fast_prompt(context, prompt, user_profile, len(retrieved))
            response = client.models.generate_content(model=GENERATION_MODEL, contents=fast_prompt)
            
            # AI가 빠르게 내뱉은 답변 자르기
            parts = response.text.split("===SPLIT===")
            cases_html = ""
            
            # AI가 준 요약문 + 파이썬이 들고 있던 원문 + HTML 껍데기를 0.001초만에 순식간에 조립!
            if len(parts) >= len(retrieved) + 1:
                for i, (_, row) in enumerate(retrieved.iterrows()):
                    # AI가 짧게 만들어준 요약문
                    summary_text = parts[i].strip().replace('\n', '<br>')
                    # 파이썬이 갖고 있던 진짜 원문
                    original_text = row['판결요지'].replace('\n', '<br>')
                    
                    cases_html += f"""
                    <div style="background: #ffffff; border-radius: 12px; padding: 24px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); border-top: 5px solid #1e3a8a; margin-bottom: 24px; font-family: 'Malgun Gothic', sans-serif;">
                        <h3 style="color: #1e3a8a; font-size: 18px; margin-top: 0; margin-bottom: 15px; border-bottom: 1px solid #e2e8f0; padding-bottom: 10px;">⚖️ {row['사건명']}</h3>
                        <div style="margin-bottom: 10px; background-color: #f8fafc; padding: 15px; border-radius: 8px;">
                            <p style="color: #334155; font-size: 14px; line-height: 1.6; margin: 0;"><b>[핵심 요약 및 시사점]</b><br><br>{summary_text}</p>
                        </div>
                        <details style="margin-top: 15px; border-top: 1px dashed #cbd5e1; padding-top: 15px;">
                            <summary style="cursor: pointer; color: #1e3a8a; font-weight: bold; font-size: 13px;">🔍 판례 원문 보기 (클릭하여 펼치기)</summary>
                            <div style="margin-top: 10px; background-color: #f1f5f9; padding: 15px; border-radius: 8px; border: 1px solid #e2e8f0;">
                                <p style="color: #64748b; font-size: 12px; line-height: 1.6; margin: 0;">{original_text}</p>
                            </div>
                        </details>
                    </div>
                    """
                # 마지막 파트는 메인 답변
                assistant_reply = parts[-1].strip()
            else:
                cases_html = "<div style='padding:20px; color:#991b1b;'>결과를 처리하는 중 오류가 발생했습니다.</div>"
                assistant_reply = response.text
        
        # 화면에 즉시 렌더링
        with st.container():
            col1, col2 = st.columns([5, 5])
            with col1:
                with st.chat_message("user"): st.markdown(prompt)
                with st.chat_message("assistant"): st.markdown(assistant_reply)
            with col2:
                st.markdown(cases_html, unsafe_allow_html=True)
        st.markdown("---")
        
        # 채팅 기록 저장
        st.session_state.chat_history.append({
            "user": prompt,
            "assistant": assistant_reply,
            "cases_html": cases_html
        })
