import streamlit as st
import pandas as pd
import numpy as np
import json
import os
from google import genai
import design

st.set_page_config(
    page_title="라온헤리티지연구소 세무 AI",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

design.apply_premium_css()

st.markdown("""
    <style>
        [data-testid="stSidebar"] {
            display: flex !important;
            min-width: 300px !important;
        }
    </style>
""", unsafe_allow_html=True)

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
# 사이드바 (단계별 고객 사전 문진표 - 심층 컨설팅용)
# ==========================================

# 1. 화면이동 및 데이터 저장을 위한 초기화
if 'step' not in st.session_state:
    st.session_state.step = 1

# 사용자가 입력한 값을 단계가 넘어가도 기억하도록 기본값 세팅 (양도/취득세/메모 항목 추가)
default_states = {
    "family_spouse": "예 (생존)", "family_kids": 2, "has_heir_issues": False,
    "asset_size": "10억~30억", "asset_types": [], 
    "is_multi_home": "해당 없음 (무주택/상가만 보유)", "sell_plan": False,
    "has_pre_gift": False, "transfer_timing": "아직 구체적 계획 없음", 
    "acq_tax_issue": False, "business_succession": False, 
    "primary_goal": "상속/증여 종합 절세 플랜 수립", "special_memo": ""
}

for key, val in default_states.items():
    if key not in st.session_state:
        st.session_state[key] = val

# 단계 이동 함수 (4단계로 확장)
def next_step(): 
    if st.session_state.step < 4: st.session_state.step += 1
def prev_step(): 
    if st.session_state.step > 1: st.session_state.step -= 1

with st.sidebar:
    st.markdown("## 📋 맞춤형 세무전략 플래너")
    st.markdown("<p style='font-size: 13px; color: #64748b;'>고객님의 상황을 고려한 완벽한 플랜을 위해 4단계 문진을 진행합니다.</p>", unsafe_allow_html=True)
    
    # 상단 진행률 표시 (4단계 기준)
    progress_val = int((st.session_state.step / 4) * 100)
    st.progress(st.session_state.step / 4, text=f"진행률 {progress_val}%")
    st.markdown("---")

    # [1단계] 가족 관계
    if st.session_state.step == 1:
        st.subheader("1단계: 가족 관계 👨‍👩‍👧‍👦")
        st.radio("배우자님이 계신가요?", ["예 (생존)", "아니오 (사망/미혼)"], key="family_spouse", help="배우자 상속공제(최소 5억~최대 30억) 적용 여부를 판단합니다.")
        st.number_input("슬하의 자녀분은 몇 분이신가요?", min_value=0, max_value=10, key="family_kids")
        st.checkbox("가족 간 재산 분배 관련 갈등 소지가 있나요?", key="has_heir_issues")
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.button("다음 단계로 ➡️", use_container_width=True, on_click=next_step)

    # [2단계] 자산 및 양도세 이슈
    elif st.session_state.step == 2:
        st.subheader("2단계: 보유 자산 및 양도 계획 💰")
        st.select_slider("예상 총 자산 규모", options=["10억 미만", "10억~30억", "30억~50억", "50억~100억", "100억 이상"], key="asset_size")
        st.multiselect("보유 중인 자산 유형을 모두 골라주세요", ["거주용 아파트/주택", "수익형 부동산(상가/빌딩)", "토지/임야", "예적금/금융자산", "비상장 주식(법인)"], key="asset_types")
        
        st.markdown("**주택 보유 현황 (양도세 중과 판별)**")
        st.radio("현재 세대 기준 주택 보유 수는 어떻게 되시나요?", ["1주택자", "2주택자", "3주택 이상 다주택자", "해당 없음 (무주택/상가만 보유)"], key="is_multi_home")
        st.checkbox("가까운 시일 내에 부동산을 매각(양도)할 계획이 있으신가요?", key="sell_plan", help="양도소득세와 증여세 중 어떤 것이 유리할지 비교하기 위해 필요합니다.")
        
        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1: st.button("⬅️ 이전", use_container_width=True, on_click=prev_step)
        with col2: st.button("다음 ➡️", use_container_width=True, on_click=next_step)

    # [3단계] 상속/증여 및 취득세 이슈
    elif st.session_state.step == 3:
        st.subheader("3단계: 재산 이전 및 취득 계획 🎁")
        st.checkbox("최근 10년 내 가족에게 증여하신 적이 있나요?", key="has_pre_gift", help="10년 이내 증여재산은 상속세 과세가액에 합산됩니다.")
        st.radio("재산 이전(증여 등) 예상 시기는 언제인가요?", ["당장 진행을 고려 중 (1년 이내)", "단기 계획 (1년~3년)", "장기 계획 (3년 이후)", "아직 구체적 계획 없음"], key="transfer_timing")
        st.checkbox("부동산을 상속/증여받을 때 발생하는 **취득세** 부담이 걱정되시나요?", key="acq_tax_issue", help="상속/증여 시 무상취득에 따른 취득세(최대 12%) 재원 마련 전략이 필요합니다.")
        st.checkbox("가업 승계(법인 지분/경영권 이전)가 포함되나요?", key="business_succession")
        
        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1: st.button("⬅️ 이전", use_container_width=True, on_click=prev_step)
        with col2: st.button("다음 ➡️", use_container_width=True, on_click=next_step)

   # [4단계] 절세 목표 및 자유 메모
    elif st.session_state.step == 4:
        st.subheader("4단계: 목표 및 특이사항 🎯")
        st.selectbox("이번 컨설팅의 가장 핵심 목표는 무엇인가요?", 
                    ["상속/증여 종합 절세 플랜 수립", "다주택자 양도 vs 증여 유불리 비교", "취득세 등 세금 납부 재원 마련 전략", "가업상속공제 특례 적용 검토", "세무조사 리스크 사전 진단"], key="primary_goal")
        
        st.markdown("**기타 메모 및 특이사항**")
        st.text_area("AI에게 미리 알리고 싶은 특수한 상황이나 질문을 자유롭게 적어주세요.", 
                     placeholder="예: 5년 전에 장남에게 아파트를 하나 증여한 적이 있습니다. / 비상장 법인에 가수금이 많습니다.", 
                     height=100, key="special_memo")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # 버튼을 2개로 나누어 배치
        col1, col2 = st.columns(2)
        with col1: 
            st.button("⬅️ 이전", use_container_width=True, on_click=prev_step)
        with col2: 
            # 클릭 여부를 submit_btn 변수에 저장
            submit_btn = st.button("✅ 입력 완료", use_container_width=True)
            
        # 버튼들(col1, col2) 아래로 빠져나와서, 클릭 시 전체 너비로 예쁜 알림창 띄우기
        if submit_btn:
            st.markdown("""
                <div style="margin-top: 15px; padding: 15px; background-color: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; text-align: center; color: #166534; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                    <span style="font-size: 16px; font-weight: bold;">🎉 준비가 완료되었습니다!</span><br>
                    <span style="font-size: 14px; margin-top: 5px; display: inline-block;">우측 하단 채팅창에 질문을 남겨주세요.</span>
                </div>
            """, unsafe_allow_html=True)

# AI가 참조할 프로필 문자열 (양도/취득세/메모 내용 포함)
user_profile = f"""
[고객 프로필]
- 가족관계: 배우자 {st.session_state.family_spouse}, 자녀 {st.session_state.family_kids}명
- 가족갈등 소지: {'있음' if st.session_state.has_heir_issues else '없음'}
- 자산규모: {st.session_state.asset_size}
- 자산유형: {', '.join(st.session_state.asset_types) if st.session_state.asset_types else '미입력'}
- 주택보유수: {st.session_state.is_multi_home} (양도세 중과 검토용)
- 부동산 매각계획: {'있음' if st.session_state.sell_plan else '없음'}
- 10년내 사전증여: {'있음' if st.session_state.has_pre_gift else '없음'}
- 증여/상속 예상시기: {st.session_state.transfer_timing}
- 취득세 이슈 고려: {'예 (재원 마련 방안 필요)' if st.session_state.acq_tax_issue else '아니오'}
- 가업승계 포함: {'예' if st.session_state.business_succession else '아니오'}
- 핵심목표: {st.session_state.primary_goal}
- 기타 특이사항(메모): {st.session_state.special_memo if st.session_state.special_memo else '없음'}
"""
# ==========================================
# 메인 화면
# ==========================================
github_user = "Dory-raon"
repo_name = "tax-ai-app"
icon_url = f"https://raw.githubusercontent.com/{github_user}/{repo_name}/main/favicon.jpg"
logo_horizontal_url = f"https://raw.githubusercontent.com/{github_user}/{repo_name}/main/logo_horizontal.png"

# 들여쓰기(띄어쓰기)로 인한 텍스트 노출 오류를 막기 위해 왼쪽 여백을 완전히 없앴습니다!
html_code = f"""
<style>
.block-container {{ padding-top: 2rem !important; }}
.stMainBlockContainer {{ padding-top: 2rem !important; }}

.fixed-header {{
    position: sticky;
    top: 0px; 
    background: rgba(255, 255, 255, 0.95); 
    backdrop-filter: blur(8px); 
    z-index: 9999; 
    display: flex;
    justify-content: space-between; 
    align-items: center;
    padding: 15px 30px;
    margin-top: -2rem; 
    margin-bottom: 30px;
    border-bottom: 1px solid #e2e8f0;
    box-shadow: 0 4px 10px -2px rgba(0, 0, 0, 0.05); 
    border-radius: 0 0 15px 15px;
}}

.header-left {{
    display: flex;
    align-items: center;
}}

header[data-testid="stHeader"] {{
    display: none;
}}
</style>

<div class="fixed-header">
    <div class="header-left">
        <!-- 아이콘 크기를 100px로 엄청 키웠습니다 -->
        <img src="{icon_url}" style="width: 100px; height: 100px; border-radius: 15px; margin-right: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
        <h1 style="margin: 0; color: #1e3a8a; font-size: 30px; font-weight: 800; letter-spacing: -1px; white-space: nowrap;">라온헤리티지연구소 컨설팅 AI</h1>
    </div>
    
    <div>
        <!-- 에러가 나던 회사 로고 영역도 띄어쓰기를 없애 완벽히 해결 -->
        <img src="{logo_horizontal_url}" style="height: 55px;">
    </div>
</div>
"""

st.markdown(html_code, unsafe_allow_html=True)

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
