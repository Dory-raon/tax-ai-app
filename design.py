import streamlit as st

def apply_premium_css():
    """스트림릿 기본 UI를 덮어쓰는 프리미엄 CSS 강제 주입"""
    custom_css = """
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
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

def get_unified_prompt(context, user_query, user_profile):
    return f"""
    당신은 '라온헤리티지연구소'의 수석 세무 컨설턴트이자 UI 웹 퍼블리셔입니다.
    아래 제공된 [판례 원문]을 바탕으로 고객에게 맞춤형 세무 컨설팅을 제공해야 합니다.

    [고객 프로필]
    {user_profile}

    [고객 질문]
    {user_query}

    [판례 원문]
    {context}

    ======================================
    [🔥 출력 규칙 - 반드시 지킬 것 🔥]
    당신의 답변은 반드시 아래의 특수 구분자 "===SPLIT==="을 사이에 두고 2개의 파트로 나뉘어야 합니다.
    마크다운 코드 블록(```html 등)은 절대 사용하지 마세요.

    [파트 1: 쉬운 판례 카드 (HTML)]
    - 판례 원문의 어려운 법률 용어를 비전문가인 일반 고객이 직관적으로 이해할 수 있도록 아주 쉽게 3~4줄 이내로 풀어서 요약할 것.
    - 다음 HTML 템플릿을 사용하여 검색된 판례 개수만큼 반복 작성:
    <div style="background: #ffffff; border-radius: 12px; padding: 24px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); border-top: 5px solid #1e3a8a; margin-bottom: 24px; font-family: 'Malgun Gothic', sans-serif;">
        <h3 style="color: #1e3a8a; font-size: 18px; margin-top: 0; margin-bottom: 15px; border-bottom: 1px solid #e2e8f0; padding-bottom: 10px;">⚖️ [사건명]</h3>
        <div style="margin-bottom: 10px;">
            <span style="background-color: #f1f5f9; padding: 4px 8px; border-radius: 4px; font-weight: bold; color: #475569; font-size: 13px; margin-right: 8px;">판례 요약</span>
            <p style="color: #334155; font-size: 14px; line-height: 1.6; margin-top: 8px;">[여기에 비전문가용 쉬운 요약 3줄 작성]</p>
        </div>
        <div>
            <span style="background-color: #fef2f2; padding: 4px 8px; border-radius: 4px; font-weight: bold; color: #991b1b; font-size: 13px; margin-right: 8px;">핵심 시사점</span>
            <p style="color: #334155; font-size: 14px; line-height: 1.6; margin-top: 8px;">[고객 상황(프로필)에 맞는 절세 시사점 1~2줄 요약]</p>
        </div>
        
        <!-- 👇 새롭게 추가된 원문 보기 접기/펴기 버튼 👇 -->
        <details style="margin-top: 15px; border-top: 1px dashed #cbd5e1; padding-top: 15px;">
            <summary style="cursor: pointer; color: #1e3a8a; font-weight: bold; font-size: 13px;">🔍 판례 원문 보기 (클릭하여 펼치기)</summary>
            <div style="margin-top: 10px; background-color: #f8fafc; padding: 15px; border-radius: 8px; border: 1px solid #e2e8f0;">
                <p style="color: #64748b; font-size: 12px; line-height: 1.6; margin: 0;">[여기에 제공된 판결요지 원문을 변형 없이 그대로 작성]</p>
            </div>
        </details>
    </div>

    ===SPLIT===

    [파트 2: 컨설턴트 답변 (Markdown)]
    - "라온헤리티지연구소 AI 컨설턴트입니다."로 시작.
    - 판례의 논리를 바탕으로 논리적이고 정중하게 브리핑.
    - 라온헤리티지가 제안 드리는 플랜' 2~3가지를 글머리 기호로 제시.
    """
