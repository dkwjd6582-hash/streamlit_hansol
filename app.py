import streamlit as st
from openai import OpenAI
import json
import urllib.parse

st.set_page_config(
    page_title="🎵 노래 추천 서비스",
    page_icon="🎵",
    layout="centered"
)

# session_state 초기화
if "songs" not in st.session_state:
    st.session_state.songs = []
if "summary" not in st.session_state:
    st.session_state.summary = ""
if "selected_artist" not in st.session_state:
    st.session_state.selected_artist = None
if "artist_songs" not in st.session_state:
    st.session_state.artist_songs = []


def fetch_recommendations(client, prompt):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "당신은 다양한 장르와 시대의 음악에 정통한 음악 큐레이터입니다. 반드시 지정된 JSON 형식으로만 응답하세요."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.8,
        max_tokens=1500,
        response_format={"type": "json_object"}
    )
    return json.loads(response.choices[0].message.content)


def fetch_artist_songs(client, artist):
    prompt = f"""음악 전문가로서 '{artist}'의 대표곡 및 추천 노래 6곡을 알려주세요.
반드시 아래 JSON 형식으로만 응답하세요.

{{
  "songs": [
    {{
      "title": "곡 제목",
      "year": "발매 연도",
      "description": "곡 소개 한 줄"
    }}
  ]
}}"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "당신은 음악 전문가입니다. 반드시 JSON 형식으로만 응답하세요."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=1000,
        response_format={"type": "json_object"}
    )
    return json.loads(response.choices[0].message.content)


def youtube_url(title, artist=""):
    query = urllib.parse.quote(f"{title} {artist}")
    return f"https://www.youtube.com/results?search_query={query}"


# ── 사이드바 ──────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ 설정")
    api_key = st.text_input(
        "OpenAI API Key",
        type="password",
        placeholder="sk-...",
        help="OpenAI API 키를 입력하세요"
    )
    st.markdown("---")
    st.markdown("🔒 API 키는 브라우저 세션에만 저장되며 외부로 전송되지 않습니다.")

    # 아티스트 더보기 패널
    if st.session_state.selected_artist:
        artist = st.session_state.selected_artist
        st.markdown("---")
        st.markdown(f"### 🎤 {artist}")
        st.markdown("**다른 추천 곡들**")

        if st.session_state.artist_songs:
            for s in st.session_state.artist_songs:
                t = s.get("title", "")
                y = s.get("year", "")
                desc = s.get("description", "")
                yt = youtube_url(t, artist)
                st.markdown(
                    f"**{t}** ({y})  \n"
                    f"<span style='font-size:12px; color:#666;'>{desc}</span>  \n"
                    f"<a href='{yt}' target='_blank'>▶ YouTube</a>",
                    unsafe_allow_html=True
                )
                st.markdown("<hr style='margin:6px 0;'>", unsafe_allow_html=True)

        if st.button("✕ 닫기", key="close_artist"):
            st.session_state.selected_artist = None
            st.session_state.artist_songs = []
            st.rerun()


# ── 메인 ──────────────────────────────────────────────
st.title("🎵 AI 노래 추천 서비스")
st.markdown("몇 가지 질문에 답하면 딱 맞는 노래를 추천해드릴게요!")
st.markdown("---")

st.subheader("📋 설문 조사")
col1, col2 = st.columns(2)

with col1:
    mood = st.selectbox(
        "1️⃣ 지금 기분이 어때요?",
        ["선택해주세요", "😊 행복하고 신남", "😌 평온하고 차분함", "😢 슬프고 감성적", "😤 에너지 넘침", "😴 나른하고 여유로움", "💔 외롭고 그리움"]
    )
    genre = st.selectbox(
        "2️⃣ 좋아하는 음악 장르는?",
        ["선택해주세요", "팝 (Pop)", "K-POP", "발라드", "힙합/R&B", "록/인디", "재즈/클래식", "일렉트로닉/EDM", "장르 무관"]
    )
    situation = st.selectbox(
        "3️⃣ 어떤 상황에서 들을 건가요?",
        ["선택해주세요", "🏃 운동할 때", "📚 공부/집중할 때", "🚗 드라이브할 때", "😴 잠들기 전", "🍽️ 식사할 때", "💃 파티/모임", "🌿 혼자 힐링할 때"]
    )

with col2:
    language = st.selectbox(
        "4️⃣ 선호하는 언어는?",
        ["선택해주세요", "한국어", "영어", "일본어", "언어 무관"]
    )
    era = st.selectbox(
        "5️⃣ 선호하는 연대는?",
        ["선택해주세요", "최신 (2020년대)", "2010년대", "2000년대", "90년대", "80~70년대 레트로", "연대 무관"]
    )
    tempo = st.selectbox(
        "6️⃣ 원하는 템포는?",
        ["선택해주세요", "빠르고 신나는 곡", "중간 템포", "느리고 잔잔한 곡", "무관"]
    )

additional = st.text_area(
    "7️⃣ 추가로 원하는 조건이 있나요? (선택)",
    placeholder="예: 가사가 위로가 되는 곡, 특정 아티스트와 비슷한 스타일, 어쿠스틱 느낌 등...",
    height=80
)

st.markdown("---")

if st.button("🎵 노래 추천받기", type="primary", use_container_width=True):
    if not api_key:
        st.error("⚠️ 사이드바에서 OpenAI API 키를 먼저 입력해주세요!")
    elif "선택해주세요" in [mood, genre, situation, language, era, tempo]:
        st.warning("⚠️ 모든 항목을 선택해주세요! (7번 항목 제외)")
    else:
        prompt = f"""당신은 음악 전문가입니다. 사용자의 취향과 상황에 맞는 노래를 추천해주세요.

사용자 정보:
- 현재 기분: {mood}
- 선호 장르: {genre}
- 청취 상황: {situation}
- 선호 언어: {language}
- 선호 연대: {era}
- 원하는 템포: {tempo}
- 추가 조건: {additional if additional else '없음'}

위 조건에 맞는 노래 5곡을 추천해주세요.
반드시 아래 JSON 형식으로만 응답하세요.

{{
  "songs": [
    {{
      "title": "곡 제목",
      "artist": "아티스트명",
      "reason": "추천 이유 (2~3문장)"
    }}
  ],
  "summary": "전체 플레이리스트 분위기 한 줄 요약"
}}"""

        with st.spinner("🎵 노래를 추천하는 중..."):
            try:
                client = OpenAI(api_key=api_key)
                result = fetch_recommendations(client, prompt)
                st.session_state.songs = result.get("songs", [])
                st.session_state.summary = result.get("summary", "")
                st.session_state.selected_artist = None
                st.session_state.artist_songs = []
            except Exception as e:
                error_msg = str(e)
                if "Invalid API key" in error_msg or "Incorrect API key" in error_msg:
                    st.error("❌ API 키가 올바르지 않습니다. 다시 확인해주세요.")
                elif "quota" in error_msg.lower():
                    st.error("❌ API 사용 한도를 초과했습니다. OpenAI 계정을 확인해주세요.")
                else:
                    st.error(f"❌ 오류가 발생했습니다: {error_msg}")

# ── 추천 결과 표시 ─────────────────────────────────────
if st.session_state.songs:
    st.success("✅ 추천 완료!")
    st.markdown("### 🎶 맞춤 추천 플레이리스트")
    st.markdown("<span style='font-size:13px; color:#888;'>💡 아티스트 이름을 클릭하면 해당 아티스트의 다른 추천 곡을 볼 수 있어요!</span>", unsafe_allow_html=True)
    st.markdown("")

    for i, song in enumerate(st.session_state.songs):
        title = song.get("title", "")
        artist = song.get("artist", "")
        reason = song.get("reason", "")
        yt = youtube_url(title, artist)

        with st.container():
            col_icon, col_info, col_btn = st.columns([0.07, 0.73, 0.20])
            with col_icon:
                st.markdown("<div style='font-size:26px; padding-top:10px;'>🎵</div>", unsafe_allow_html=True)
            with col_info:
                st.markdown(
                    f"<b style='font-size:16px;'>{title}</b> &nbsp;"
                    f"<a href='{yt}' target='_blank' style='text-decoration:none;'>"
                    f"<span style='background:#FF0000; color:white; padding:2px 8px; border-radius:10px; font-size:12px;'>▶ YouTube</span></a><br>"
                    f"<span style='color:#555; font-size:13px;'>{reason}</span>",
                    unsafe_allow_html=True
                )
            with col_btn:
                if st.button(f"🎤 {artist}", key=f"artist_{i}", help=f"{artist}의 다른 곡 보기"):
                    if not api_key:
                        st.warning("API 키를 먼저 입력해주세요.")
                    else:
                        with st.spinner(f"{artist} 곡 불러오는 중..."):
                            try:
                                client = OpenAI(api_key=api_key)
                                data = fetch_artist_songs(client, artist)
                                st.session_state.selected_artist = artist
                                st.session_state.artist_songs = data.get("songs", [])
                                st.rerun()
                            except Exception as e:
                                st.error(f"오류: {e}")

        st.markdown("<hr style='margin:8px 0; border:none; border-top:1px solid #eee;'>", unsafe_allow_html=True)

    if st.session_state.summary:
        st.markdown(f"💿 **플레이리스트 분위기:** {st.session_state.summary}")

    st.markdown("---")
    st.markdown("💡 **마음에 드는 곡이 있나요?** 다시 설문에 답하면 새로운 추천을 받을 수 있어요!")

st.markdown("---")
st.markdown(
    "<div style='text-align:center; color:gray; font-size:12px;'>Powered by OpenAI gpt-4o-mini</div>",
    unsafe_allow_html=True
)
