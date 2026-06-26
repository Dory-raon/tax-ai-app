import streamlit as st
import time
import google.generativeai as genai

# API 키 불러오기 및 제미나이 모델 설정
api_key = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-2.5-flash')

# 1. 우리만의 내부 지식 데이터베이스 (RAG 모의 테스트용)
KNOWLEDGE_DB = [
    {
        "쟁점": "유언대용신탁", 
        "분류": "분쟁방어", 
        "내용": "신탁계약 1년 전 맡긴 자산은 유류분 반환 대상이 아니라는 하급심 판례(수원지법)가 존재하여, 특정 자녀에게 자산을 집중 승계할 때 유리합니다."
    },
    {
        "쟁점": "종신보험 가입", 
        "분류": "분쟁방어 및 재원마련", 
        "내용": "계약자와 수익자를 자녀로 지정한 사망보험금은 상속재산이 아닌 수익자의 고유재산(대법원 2000다64502)이므로 유류분을 방어하고 상속세 재원을 마련할 수 있습니다."
    },
    {
        "쟁점": "부담부증여", 
        "분류": "절세극대화", 
        "내용": "전세 보증금이나 대출을 포함하여 증여하는 방식으로, 자산 가치 상승이 예상되는 경우 순수 증여 대비 과세표준을 낮춰 누진세율 구간을 회피할 수 있습니다."
    }
]

# 2. 검색 엔진 로직
def search_strategy(asset_value, conflict_risk):
    results = []
    if asset_value >= 30:
        results.append("[세무 리스크] 30억 초과로 최고 누진세율 50% 구간 진입. 강력한 사전증여 플랜 필요.")
        
    if conflict_risk == "높음 (유류분 청구 예상)":
        for item in KNOWLEDGE_DB:
            if item["분류"] in ["분쟁방어", "분쟁방어 및 재원마련"]:
                results.append(f"[{item['쟁점']}] {item['내용']}")
    else:
        for item in KNOWLEDGE_DB:
            if item["분류"] == "절세극대화":
                results.append(f"[{item['쟁점']}] {item['내용']}")
    return "\n".join(results)

# 3. 웹사이트 화면 UI 설정
st.set_page_config(page_title="AI 상속/증여 세무 컨설턴트", page_icon="⚖️")
st.title("AI 상속/증여 세무 컨설턴트 💼")
st.markdown("고객 상황을 분석하여 AI가 자연스러운 문장으로 절세 전략을 제안합니다.")

with st.sidebar:
    st.header("고객 상황 조건부 입력창")
    asset_value = st.number_input("예상 상속/증여 재산 (억원)", min_value=0, value=50)
    conflict_risk = st.selectbox("유산 분쟁 예상 여부", ["높음 (유류분 청구 예상)", "보통", "낮음"])
    st.divider()
    st.info("실제 제미나이 AI가 이 조건들과 내부 DB를 종합하여 답변을 생성합니다.")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("상담을 시작하려면 문의 내용을 입력하세요."):
    
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        # 자체 DB에서 조건에 맞는 데이터 검색
        db_context = search_strategy(asset_value, conflict_risk)
        
        # AI에게 지시할 프롬프트 조립 (RAG 핵심 로직)
        ai_prompt = f"""
        당신은 상속/증여 전문 세무 컨설턴트입니다.
        아래 제공된 [검색된 지식 DB] 내용만을 바탕으로 사용자의 질문에 답변하세요.
        전문적이고 신뢰감 있는 말투를 사용하며, 고객의 상황에 맞는 전략을 자연스러운 문장으로 풀어서 설명해 주세요.
        
        [고객 상황]
        - 재산 규모: {asset_value}억원
        - 분쟁 위험도: {conflict_risk}
        
        [검색된 지식 DB]
        {db_context}
        
        사용자 질문: {prompt}
        """
        
        try:
            # 제미나이 AI에게 답변 생성 요청
            response = model.generate_content(ai_prompt)
            full_response = response.text
            message_placeholder.markdown(full_response)
        except Exception as e:
            full_response = f"AI 연동 중 오류가 발생했습니다: {e}"
            message_placeholder.markdown(full_response)
        
    st.session_state.messages.append({"role": "assistant", "content": full_response})
