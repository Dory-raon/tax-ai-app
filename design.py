import streamlit as st

def apply_premium_css():
    """스트림릿 기본 UI를 덮어쓰는 프리미엄 CSS 강제 주입"""
      custom_css = """
    <style>
    #MainMenu {visibility: hidden;}
    /* header 전체를 숨기지 말고, 스트림릿 메뉴만 숨기기 */
    header[data-testid="stHeader"] {visibility: hidden;} 
    
    footer {visibility: hidden;}
    .stAppDeployButton {display: none;}
    .stApp {background-color: #f4f6f9;}
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e2e8f0;
        box-shadow: 2px 0 10px rgba(0,0,0,0.03);
    }
    .stChatInputContainer {
        border-radius: 15px !important;
        border: 1px solid #cbd5e1 !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05) !important;
    }
    h1, h2, h3 {color: #1e3a8a !important;}
    
    /* details(아코디언) 태그 클릭 시 외곽선 없애기 */
    details summary {
        outline: none;
    }
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)

def get_fast_prompt(context, user_query, user_profile, num_cases):
    """극강의 속도를 위해 AI에게는 딱 필요한 내용만 짧게 생성하도록 강제하는 프롬프트"""
    split_format = ""
    for i in range(1, num_cases + 1):
        split_format += f"[판례 {i} 간단 요약]\n(비전문가가 이해하기 쉽게 3줄 요약)\n\n[핵심 시사점]\n(고객 상황에 맞는 절세 시사점 1~2줄)\n===SPLIT===\n"
    
    return f"""
    당신은 '라온헤리티지연구소'의 AI 세무 컨설턴트입니다.
    아래 제공된 [판례 원문]을 바탕으로 맞춤형 세무 컨설팅을 제공하세요.

    [고객 프로필]
    {user_profile}

    [고객 질문]
    {user_query}

    [판례 원문]
    {context}

    ======================================
    [🔥 출력 규칙 - ⚠️ 속도를 위해 반드시 지킬 것 ⚠️]
    1. 당신은 절대로 HTML 코드, CSS 디자인, 사건명, 판례 원문을 다시 타이핑하지 마세요! (출력 속도를 심각하게 늦춥니다)
    2. 오직 당신이 창작한 '요약문', '시사점', '최종 답변'만 아래 양식에 맞춰 짧고 굵게 출력하세요.
    3. 각 파트를 나누는 "===SPLIT===" 기호를 정확히 기입하세요.

    {split_format}라온헤리티지연구소 수석 컨설턴트입니다.
    (이하 메인 컨설팅 답변 및 라온헤리티지연구소가 제안 드리는 플랜 2~3가지 작성)
    """
