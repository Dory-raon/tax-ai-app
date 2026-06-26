import streamlit as st
import time

# --- [1. 우리만의 내부 지식 데이터베이스 구축 (RAG 모의 테스트용)] ---
# 실제 서비스에서는 법제처 API와 크롤링으로 수집한 수만 건의 데이터가 이곳을 대체합니다.
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

# --- [2. 검색 엔진 로직 (AI가 조건에 맞는 데이터를 찾는 과정)] ---
def search_strategy(asset_value, conflict_risk):
    results = []
    
    # 세무 리스크 분석 (최고세율 50% 구간 확인)
    if asset_value >= 30:
        results.append("⚠️ [세무 리스크 경고] 예상 상속재산이 30억을 초과하여 최고 누진세율 50% 구간에 진입했습니다. 강력한 사전증여 플랜이 필요합니다.")
        
    # 법률 리스크 분석 (분쟁 위험도에 따른 DB 검색)
    if conflict_risk == "높음 (유류분 청구 예상)":
        results.append("🔍 [분쟁 방어 전략 검색 완료]")
        for item in KNOWLEDGE_DB:
            if item["분류"] in ["분쟁방어", "분쟁방어 및 재원마련"]:
                results.append(f"- {item['쟁점']}: {item['내용']}")
    else:
        results.append("🔍 [일반 절세 전략 검색 완료]")
        for item in KNOWLEDGE_DB:
            if item["분류"] == "절세극대화":
                results.append(f"- {item['쟁점']}: {item['내용']}")
                
    return results

# --- [3. 웹사이트 화면 UI 설정] ---
st.set_page_config(page_title="AI 상속/증여 세무 컨설턴트", page_icon="⚖️")
st.title("AI 상속/증여 세무 컨설턴트 💼")
st.markdown("고객 상황을 좌측에 입력하고 엔터를 치시면, 내부 DB를 검색하여 맞춤형 전략을 도출합니다.")

# 사이드바 입력창
with st.sidebar:
    st.header("고객 상황 조건부 입력창")
    asset_value = st.number_input("예상 상속/증여 재산 (억원)", min_value=0, value=50)
    conflict_risk = st.selectbox("유산 분쟁 예상 여부", ["높음 (유류분 청구 예상)", "보통", "낮음"])
    st.divider()
    st.info("💡 지금 선택하시는 값에 따라 AI가 내부 DB에서 꺼내오는 전략이 실시간으로 바뀝니다.")

# 채팅 UI 로직
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 사용자가 입력창에 글을 남겼을 때 실행되는 행동
if prompt := st.chat_input("상담을 시작하려면 '분석 시작' 이라고 입력해 보세요."):
    
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        # 입력된 사이드바 조건(자산규모, 분쟁위험)을 바탕으로 자체 DB 검색 함수 실행
        strategy_list = search_strategy(asset_value, conflict_risk)
        
        # 검색된 결과를 문장으로 조립하여 화면에 타이핑 효과로 출력
        simulated_response = "\n\n".join(strategy_list)
        
        for chunk in simulated_response.split():
            full_response += chunk + " "
            time.sleep(0.05)
            message_placeholder.markdown(full_response + "▌")
        message_placeholder.markdown(full_response)
        
    st.session_state.messages.append({"role": "assistant", "content": full_response})