
import os
import streamlit as st
from openai import OpenAI

# OpenAI 클라이언트 생성
client = OpenAI()

# 페이지 설정
st.set_page_config(page_title="한영 번역기 ", page_icon="  ")
st.title("멋진번역가")
st.write("한글영문번역기입니다.")

# 사용자 입력(텍스트)
korean_text = st.text_area(
    "번역할 한글 문장을 입력하세요.",
    height=150,
    placeholder="예: 인공지능은 우리의 일상과 업무 방식을 빠르게 변화시키고 있습니다."
)

# 번역 버튼
if st.button("번역하기"):

    if not korean_text.strip():
        st.warning("번역할 문장을 입력하세요.")
    else:
        with st.spinner("번역 중입니다..."):

            # 시스템 역할
            sys_role = """
              당신은 최고의 영어 한글 전문가입니다. 영어에서 한글로 한글에서 영어를 자유자재로 자연스러운 번역을 할 수 있는 능력이 있습니다.

            """

            # 프롬프트 구성
            prompt = f"""
            다음 문장을 영어로 번역하세요.
            TEXT:
            {korean_text}
            """

            # GPT 호출
            response = client.responses.create(
                model="gpt-4o-mini",
                input=[
                    {"role": "system", "content": sys_role   },
                    {"role": "user", "content": prompt   }
                ]
            )


            # 결과 출력
            translated_text = response.output_text

            st.subheader("번역 결과")
            st.success( translated_text   )
