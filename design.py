import streamlit as st

def apply_premium_css():
    """스트림릿 기본 UI를 덮어쓰는 프리미엄 CSS 강제 주입"""
    custom_css = """
    <style>
    /* 1. 스트림릿 기본 꼬리표(메뉴, 헤더, 푸터) 완벽 숨김 */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stAppDeployButton {display: none;}
    
    /* 2. 전체 배경색 (아주 옅은 회파란색으로 신뢰감 부여) */
    .stApp {
        background-color: #f4f6f9;
    }

    /* 3. 사이드바 디자인 다듬기 */
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e2e8f0;
        box-shadow: 2px 0 10px rgba(0,0,0,0.03);
    }

    /* 4. 채팅 입력창 라운딩 및 그림자 처리 */
    .stChatInputContainer {
        border-radius: 15px !important;
        border: 1px solid #cbd5e1 !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05) !important;
    }
    
    /* 5. 텍스트 강조 컬러 (라온헤리티지 네이비) */
    h1, h2, h3 {
        color: #1e3a8a !important;
    }
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)

def get_case_card_prompt(raw_cases):
    """판례 데이터를 고급스러운 UI 카드로 변환하는 프롬프트"""
    return f"""
    당신은 수석 UI/UX 웹 퍼블리셔입니다.
    아래 제공된 판례 텍스트를 분석하여, 대형 로펌의 프리미엄 인트라넷에서 볼 법한 세련되고 고급스러운 HTML 카드 UI로 변환해주세요.

    [디자인 가이드 - 반드시 지킬 것]
    1. 전체 래퍼: `<div style="background: #ffffff; border-radius: 12px; padding: 24px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); border-top: 5px solid #1e3a8a; margin-bottom: 24px; font-family: 'Malgun Gothic', sans-serif;">`
    2. 제목(사건명): `<h3 style="color: #1e3a8a; font-size: 18px; margin-top: 0; margin-bottom: 15px; border-bottom: 1px solid #e2e8f0; padding-bottom: 10px;">⚖️ [사건명]</h3>`
    3. 내용 영역: 쟁점, 관련법령, 판결요지를 각각 소제목과 함께 깔끔하게 배치.
    4. 소제목 뱃지: `<span style="background-color: #f1f5f9; padding: 4px 8px; border-radius: 4px; font-weight: bold; color: #475569; font-size: 13px; margin-right: 8px;">쟁점</span>` 형태로 강조.
    5. 본문 텍스트: 글씨 크기 14px, 줄간격 1.6, 색상 `#334155`로 가독성 극대화.
    6. 판례가 2개 이상일 경우 위 div 래퍼를 반복해서 작성.
    7. 마크다운(` ```html ` 등) 기호 없이 순수 HTML 코드만 텍스트로 출력할 것.

    [판례 로데이터]
    {raw_cases}
    """

def get_assistant_prompt(context, user_query, user_profile):
    """메인 AI 컨설턴트의 페르소나 및 지침 프롬프트"""
    return f"""
    당신은 '라온헤리티지연구소'의 수석 세무 AI 컨설턴트입니다.
    아래 제공된 고객의 프로필과 대법원/조세심판원 판례를 바탕으로 논리적이고 전문적인 맞춤형 절세 플랜을 브리핑하세요.

    [고객 프로필]
    {user_profile}

    [참조 판례]
    {context}

    [고객 질문]
    {user_query}

    [답변 작성 가이드]
    1. 도입부: "라온헤리티지연구소 AI 컨설턴트입니다."로 시작하며, 고객의 자산/가족 상황을 깊이 이해하고 있음을 짚어주세요.
    2. 전문성: 참조된 판례의 핵심 논리를 인용하여 국세청의 과세 논리와 우리의 방어 논리를 브리핑하세요.
    3. 가독성: 긴 글을 나열하지 말고, 글머리 기호와 소제목을 활용해 깔끔한 보고서 형태로 작성하세요.
    4. 어조: 대형 회계법인의 파트너 회계사가 VIP 고객에게 브리핑하는 듯한 정중하고 단호한 어조를 유지하세요.
    5. 결론: 고객이 당장 실행해야 할 실질적인 '액션 플랜(Action Plan)'을 2~3가지로 요약하여 제시하세요.
    """
