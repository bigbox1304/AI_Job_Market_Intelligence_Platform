import html
import os
from collections import Counter
from typing import Any, Dict, Iterable, List

import matplotlib.pyplot as plt
import requests
import streamlit as st


API_URL = os.getenv("API_URL", "http://api:8000").rstrip("/")

st.set_page_config(
    page_title="Pivot — AI Job Intelligence",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)


# -----------------------------------------------------------------------------
# Visual system
# -----------------------------------------------------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Manrope:wght@400;500;600;700;800&display=swap');

    :root { --ink:#12212b; --muted:#6c7b83; --line:#dce5e7; --paper:#f6f8f5; --white:#fff; --teal:#0e7475; --teal-dark:#075355; --mint:#c6f26d; --coral:#ff846d; }
    html, body, [class*="css"] { font-family:'Manrope', sans-serif; color:var(--ink); }
    .stApp { background:var(--paper); }
    [data-testid="stHeader"] { background:transparent; }
    [data-testid="stToolbar"] { visibility:hidden; }
    [data-testid="stSidebar"] { background:var(--teal-dark); border-right:0; }
    [data-testid="stSidebar"] * { color:#eefbf2; }
    [data-testid="stSidebar"] .stButton button { background:rgba(255,255,255,.08); border:1px solid rgba(255,255,255,.12); color:#f4fff5; text-align:left; }
    [data-testid="stSidebar"] .stButton button:hover { background:rgba(198,242,109,.16); border-color:var(--mint); }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color:#d5ece8; }
    .brand { display:flex; align-items:center; gap:10px; margin:4px 0 38px; }
    .brand-mark { display:grid; place-items:center; width:32px; height:32px; border-radius:11px; color:var(--teal-dark); background:var(--mint); font-weight:800; font-size:18px; }
    .brand-name { font-size:18px; font-weight:800; letter-spacing:-.04em; }
    .brand-meta { color:#9bcac4; font:10px 'DM Mono',monospace; letter-spacing:.14em; }
    .eyebrow { color:var(--teal); font:600 11px 'DM Mono',monospace; letter-spacing:.15em; text-transform:uppercase; margin-bottom:12px; }
    .eyebrow.light { color:var(--mint); }
    .hero { padding:38px 42px 34px; border-radius:28px; color:#f5fff5; background:linear-gradient(125deg,#0a5558 0%,#0d7372 62%,#15928a 100%); position:relative; overflow:hidden; margin-bottom:26px; }
    .hero:after { content:'✦'; position:absolute; right:42px; top:-26px; color:rgba(198,242,109,.28); font-size:180px; line-height:1; }
    .hero h1 { position:relative; z-index:1; max-width:730px; margin:0 0 12px; font-size:clamp(36px,4.4vw,64px); line-height:.99; letter-spacing:-.065em; }
    .hero-copy { position:relative; z-index:1; max-width:610px; color:#cce8df; font-size:15px; line-height:1.7; }
    .signal { position:relative; z-index:1; display:inline-flex; align-items:center; gap:8px; padding:7px 11px; border:1px solid rgba(198,242,109,.4); border-radius:999px; color:var(--mint); font:11px 'DM Mono',monospace; letter-spacing:.08em; }
    .signal-dot { width:7px; height:7px; border-radius:50%; background:var(--mint); }
    .search-shell { padding:22px 24px 14px; border:1px solid var(--line); border-radius:20px; background:var(--white); box-shadow:0 12px 32px rgba(18,33,43,.05); margin-top:-6px; margin-bottom:28px; }
    .search-label { font-size:13px; font-weight:800; margin-bottom:8px; }
    .search-hint { color:var(--muted); font-size:12px; margin:3px 0 12px; }
    .reco-flow { display:flex; align-items:stretch; gap:10px; margin:0 0 26px; }
    .reco-step { flex:1; padding:15px 16px; border:1px solid var(--line); border-radius:14px; background:rgba(255,255,255,.62); }
    .reco-step-no { color:var(--coral); font:600 10px 'DM Mono',monospace; letter-spacing:.12em; }
    .reco-step-title { margin:7px 0 4px; font-size:13px; font-weight:800; }
    .reco-step-copy { color:var(--muted); font-size:11px; line-height:1.5; }
    .reco-arrow { display:flex; align-items:center; color:#9bb2b0; font-size:18px; }
    .stTextArea textarea { border:1px solid #cbdadc !important; border-radius:13px !important; background:#fbfdfb !important; color:var(--ink) !important; font-size:15px !important; }
    .stTextArea textarea:focus { border-color:var(--teal) !important; box-shadow:0 0 0 2px rgba(14,116,117,.12) !important; }
    .stButton > button { min-height:42px; border:1px solid var(--teal); border-radius:12px; background:var(--teal); color:white; font-weight:800; transition:transform .15s ease,box-shadow .15s ease; }
    .stButton > button:hover { color:white; transform:translateY(-1px); box-shadow:0 7px 18px rgba(14,116,117,.2); }
    .section-title { font-size:25px; font-weight:800; letter-spacing:-.045em; margin:22px 0 4px; }
    .section-subtitle { color:var(--muted); font-size:13px; margin-bottom:18px; }
    .kpi { min-height:112px; padding:19px 20px; border:1px solid var(--line); border-radius:17px; background:var(--white); }
    .kpi-label { color:var(--muted); font:11px 'DM Mono',monospace; letter-spacing:.1em; text-transform:uppercase; }
    .kpi-value { margin-top:8px; font-size:31px; line-height:1; font-weight:800; letter-spacing:-.055em; }
    .kpi-note { color:var(--teal); font-size:11px; margin-top:9px; }
    .insight { padding:22px 25px; border-radius:18px; color:#f1fff3; background:var(--teal-dark); margin:20px 0 24px; }
    .insight-title { color:var(--mint); font:11px 'DM Mono',monospace; letter-spacing:.13em; text-transform:uppercase; margin-bottom:10px; }
    .insight-copy { font-size:15px; line-height:1.75; }
    .fit-report { padding:26px; border:1px solid #c9ded8; border-radius:22px; background:#edf7f1; margin:18px 0 28px; }
    .fit-header { display:flex; align-items:flex-start; justify-content:space-between; gap:24px; margin-bottom:22px; }
    .fit-kicker { color:var(--teal); font:11px 'DM Mono',monospace; letter-spacing:.14em; text-transform:uppercase; }
    .fit-headline { max-width:650px; margin-top:7px; font-size:25px; font-weight:800; line-height:1.2; letter-spacing:-.045em; }
    .fit-score { min-width:104px; padding:13px 14px; border-radius:16px; text-align:center; color:var(--teal-dark); background:var(--mint); }
    .fit-score-value { font-size:29px; line-height:1; font-weight:800; letter-spacing:-.06em; }
    .fit-score-label { margin-top:6px; font:10px 'DM Mono',monospace; letter-spacing:.08em; }
    .fit-section { height:100%; padding:17px 18px; border:1px solid rgba(14,116,117,.15); border-radius:15px; background:rgba(255,255,255,.7); }
    .fit-section-label { color:var(--muted); font:10px 'DM Mono',monospace; letter-spacing:.12em; text-transform:uppercase; }
    .fit-role { margin:7px 0 5px; font-size:18px; font-weight:800; letter-spacing:-.035em; }
    .fit-meta { color:var(--muted); font-size:12px; line-height:1.6; }
    .fit-chip { display:inline-block; margin:10px 5px 0 0; padding:5px 9px; border-radius:99px; color:var(--teal-dark); background:#d9f0dd; font-size:11px; }
    .fit-chip.gap { color:#93402f; background:#ffe0d8; }
    .direction-card { min-height:144px; padding:16px; border:1px solid var(--line); border-radius:15px; background:var(--white); }
    .direction-score { float:right; color:var(--teal); font:600 11px 'DM Mono',monospace; }
    .action-card { display:flex; gap:13px; padding:13px 0; border-bottom:1px solid rgba(14,116,117,.13); }
    .action-card:last-child { border-bottom:0; padding-bottom:0; }
    .action-number { color:var(--coral); font:600 11px 'DM Mono',monospace; white-space:nowrap; }
    .action-title { font-size:13px; font-weight:800; }
    .action-detail { margin-top:3px; color:var(--muted); font-size:12px; line-height:1.55; }
    .skill-card { min-height:92px; padding:16px 15px; border:1px solid var(--line); border-radius:14px; background:var(--white); }
    .skill-name { font-size:14px; font-weight:800; text-transform:capitalize; }
    .skill-count { color:var(--muted); font:11px 'DM Mono',monospace; margin-top:10px; }
    .skill-bar { height:4px; border-radius:99px; background:#e5eeee; margin-top:10px; overflow:hidden; }
    .skill-fill { height:100%; border-radius:99px; background:var(--coral); }
    .job-card { padding:21px 23px; border:1px solid var(--line); border-radius:18px; background:var(--white); margin-bottom:12px; }
    .job-card h3 { margin:0 0 10px; font-size:19px; letter-spacing:-.035em; }
    .job-meta { display:flex; flex-wrap:wrap; gap:8px; color:var(--muted); font-size:12px; }
    .job-meta span { padding:5px 9px; border-radius:7px; background:#f0f5f3; }
    .job-score { color:var(--teal); font:600 11px 'DM Mono',monospace; text-align:right; }
    .score-track { height:5px; width:100%; border-radius:99px; background:#e5eeee; margin-top:8px; }
    .score-fill { height:100%; border-radius:99px; background:var(--mint); }
    .job-reason { margin-top:13px; color:var(--teal-dark); font-size:11px; line-height:1.5; }
    .tag { display:inline-block; margin:13px 5px 0 0; padding:5px 9px; border:1px solid #d4e8de; border-radius:99px; color:var(--teal-dark); background:#f2faf5; font-size:11px; }
    .roadmap { padding:19px 21px; border-left:4px solid var(--coral); border-radius:0 15px 15px 0; background:var(--white); box-shadow:0 4px 18px rgba(18,33,43,.04); margin-bottom:12px; }
    .roadmap-title { font-size:16px; font-weight:800; text-transform:capitalize; }
    .roadmap-note { color:var(--muted); font-size:12px; margin:7px 0 12px; }
    .empty { padding:52px 30px; border:1px dashed #b9cccb; border-radius:20px; text-align:center; background:rgba(255,255,255,.52); }
    .empty-mark { color:var(--teal); font-size:36px; }
    .empty h3 { margin:10px 0 6px; font-size:22px; letter-spacing:-.04em; }
    .empty p { max-width:500px; margin:auto; color:var(--muted); font-size:13px; line-height:1.7; }
    .footer { color:#91a1a5; font:10px 'DM Mono',monospace; letter-spacing:.08em; text-align:center; margin:42px 0 18px; }
    </style>
    """,
    unsafe_allow_html=True,
)


# -----------------------------------------------------------------------------
# State and API helpers
# -----------------------------------------------------------------------------
if "selected_level" not in st.session_state:
    st.session_state.selected_level = None
if "selected_industry" not in st.session_state:
    st.session_state.selected_industry = None
if "query_input" not in st.session_state:
    st.session_state.query_input = ""

query_params = st.query_params
if "token" in query_params:
    st.session_state.token = query_params["token"]
    st.session_state.user = query_params.get("name", "User")


def auth_headers() -> Dict[str, str]:
    token = st.session_state.get("token")
    return {"Authorization": f"Bearer {token}"} if token else {}


def api_get(path: str, **kwargs: Any) -> requests.Response | None:
    try:
        return requests.get(f"{API_URL}{path}", headers=auth_headers(), timeout=8, **kwargs)
    except requests.RequestException:
        return None


def api_post(path: str, payload: Dict[str, Any]) -> requests.Response | None:
    try:
        return requests.post(f"{API_URL}{path}", headers=auth_headers(), json=payload, timeout=45)
    except requests.RequestException:
        return None


def track_job_event(job_id: Any, event_type: str) -> bool:
    if not st.session_state.get("token"):
        return False
    response = api_post("/events/job", {"job_id": int(job_id), "event_type": event_type})
    return response is not None and response.status_code == 204


def safe_text(value: Any, fallback: str = "—") -> str:
    if value is None or str(value).strip() == "":
        return fallback
    return html.escape(str(value))


def skill_list(value: Any) -> List[str]:
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    if isinstance(value, Iterable):
        return [str(item).strip() for item in value if str(item).strip()]
    return []


def set_query(value: str) -> None:
    st.session_state.query_input = value
    st.rerun()


def render_kpi(label: str, value: Any, note: str) -> None:
    st.markdown(f'<div class="kpi"><div class="kpi-label">{safe_text(label)}</div><div class="kpi-value">{safe_text(value)}</div><div class="kpi-note">{safe_text(note)}</div></div>', unsafe_allow_html=True)


def score_percent(score: Any) -> int:
    try:
        number = float(score)
        if number <= 1:
            number *= 100
        return max(0, min(100, round(number)))
    except (TypeError, ValueError):
        return 0


# -----------------------------------------------------------------------------
# Sidebar
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown('<div class="brand"><div class="brand-mark">✦</div><div><div class="brand-name">PIVOT</div><div class="brand-meta">AI JOB INTELLIGENCE</div></div></div>', unsafe_allow_html=True)
    st.markdown('<div class="eyebrow light">Workspace</div>', unsafe_allow_html=True)
    st.caption("Một góc nhìn nhanh hơn về kỹ năng, nhu cầu tuyển dụng và bước tiến tiếp theo của bạn.")

    if st.session_state.get("user"):
        st.markdown(f"👋  **{safe_text(st.session_state['user'])}**")
    else:
        st.markdown("**Khám phá thị trường việc làm**")
        if st.button("Đăng nhập với Google", use_container_width=True):
            st.markdown('<meta http-equiv="refresh" content="0; url=http://localhost:8000/auth/google/login">', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown('<div class="eyebrow light">Search history</div>', unsafe_allow_html=True)
    history_response = api_get("/history") if st.session_state.get("token") else None
    if history_response is not None and history_response.status_code == 200:
        history = history_response.json() or []
        if history:
            for index, item in enumerate(history[:8]):
                query = item.get("query", "Untitled search")
                if st.button(f"⌕  {query}", key=f"history_{index}", use_container_width=True):
                    set_query(query)
        else:
            st.caption("Các tìm kiếm của bạn sẽ xuất hiện ở đây.")
    elif not st.session_state.get("token"):
        st.caption("Đăng nhập để lưu và quay lại các tìm kiếm.")
    else:
        st.caption("Chưa thể tải lịch sử tìm kiếm.")

    st.markdown("---")
    st.caption("PIVOT v1.0  •  MARKET SIGNALS")


# -----------------------------------------------------------------------------
# Main header and search
# -----------------------------------------------------------------------------
st.markdown('<div class="hero"><div class="signal"><span class="signal-dot"></span> LIVE MARKET SIGNALS</div><h1>Đọc vị thị trường.<br>Chọn đúng bước tiến.</h1><div class="hero-copy">Mô tả điều bạn muốn làm tiếp theo. PIVOT sẽ kết nối kỹ năng của bạn với những cơ hội phù hợp và biến dữ liệu tuyển dụng thành một kế hoạch phát triển rõ ràng.</div></div>', unsafe_allow_html=True)

st.markdown('<div class="search-shell">', unsafe_allow_html=True)
st.markdown('<div class="search-label">Bạn đang tìm cơ hội nào?</div>', unsafe_allow_html=True)
st.markdown('<div class="search-hint">Viết bằng ngôn ngữ tự nhiên — kỹ năng, chức danh, ngành hoặc mục tiêu nghề nghiệp.</div>', unsafe_allow_html=True)
search_col, action_col, clear_col = st.columns([6, 1.3, 1])
with search_col:
    user_input = st.text_area("Từ khóa tìm kiếm", key="query_input", height=76, label_visibility="collapsed", placeholder="Ví dụ: Python + machine learning, muốn chuyển sang Data Analyst...")
with action_col:
    st.write("")
    st.write("")
    search_clicked = st.button("Phân tích →", use_container_width=True, type="primary")
with clear_col:
    st.write("")
    st.write("")
    if st.button("Xóa", use_container_width=True):
        for key in ("results", "analytics", "career_fit", "ai_summary"):
            st.session_state.pop(key, None)
        st.session_state.query_input = ""
        st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

st.markdown(
    '<div class="reco-flow">'
    '<div class="reco-step"><div class="reco-step-no">01 / UNDERSTAND</div><div class="reco-step-title">Đọc mục tiêu của bạn</div><div class="reco-step-copy">AI chuyển kỹ năng và định hướng viết tự nhiên thành tín hiệu tìm kiếm.</div></div>'
    '<div class="reco-arrow">→</div>'
    '<div class="reco-step"><div class="reco-step-no">02 / RETRIEVE</div><div class="reco-step-title">Tìm job bằng ngữ nghĩa</div><div class="reco-step-copy">Embedding + FAISS tìm những vị trí liên quan, kể cả khi không trùng exact keyword.</div></div>'
    '<div class="reco-arrow">→</div>'
    '<div class="reco-step"><div class="reco-step-no">03 / EXPLAIN</div><div class="reco-step-title">Giải thích & định hướng</div><div class="reco-step-copy">Career Fit Engine chỉ ra lý do match, skill gap và bước tiếp theo.</div></div>'
    '</div>',
    unsafe_allow_html=True,
)

if search_clicked:
    if not user_input.strip():
        st.warning("Hãy nhập một vài kỹ năng hoặc mục tiêu để PIVOT bắt đầu phân tích.")
    else:
        with st.spinner("Đang đọc tín hiệu từ thị trường..."):
            response = api_post("/recommend/analytics", {"text": user_input, "top_k": 100})
        if response is None:
            st.error("Không thể kết nối tới API. Hãy kiểm tra service backend đang chạy.")
        elif response.status_code != 200:
            st.error(f"API trả về lỗi {response.status_code}. Vui lòng thử lại.")
        else:
            data = response.json()
            if data.get("error"):
                st.error(data["error"])
            else:
                st.session_state.results = data.get("results", [])
                st.session_state.analytics = data.get("analytics", {})
                st.session_state.career_fit = data.get("career_fit", {})
                st.session_state.ai_summary = data.get("ai_summary")
                st.session_state.selected_level = None
                st.session_state.selected_industry = None
                st.rerun()


# -----------------------------------------------------------------------------
# Personalized suggestions and empty state
# -----------------------------------------------------------------------------
if "results" not in st.session_state and st.session_state.get("token"):
    personalized = api_get("/recommend/personalized")
    if personalized is not None and personalized.status_code == 200:
        suggestions = personalized.json() or {}
        keywords = suggestions.get("suggested_keywords", [])[:5]
        if keywords:
            st.markdown('<div class="section-title">Gợi ý dành cho bạn</div><div class="section-subtitle">Từ những gì bạn đã tìm kiếm gần đây.</div>', unsafe_allow_html=True)
            suggestion_cols = st.columns(min(5, len(keywords)))
            for index, keyword in enumerate(keywords):
                if suggestion_cols[index].button(f"✦  {keyword}", key=f"suggestion_{index}", use_container_width=True):
                    set_query(keyword)


if "results" not in st.session_state:
    st.markdown('<div class="empty"><div class="empty-mark">✦</div><h3>Không chỉ tìm việc — tìm bước tiến.</h3><p>Nhập một mô tả ở phía trên để xem độ phù hợp, kỹ năng đang được săn đón và lộ trình phát triển tiếp theo.</p></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Thử một truy vấn nhanh</div><div class="section-subtitle">Bắt đầu với một trong những hướng phổ biến.</div>', unsafe_allow_html=True)
    examples = ["Data Analyst với SQL và Python", "Machine Learning Engineer", "Frontend Developer tại Hà Nội", "Product Manager chuyển ngành"]
    example_cols = st.columns(4)
    for index, example in enumerate(examples):
        if example_cols[index].button(example, key=f"example_{index}", use_container_width=True):
            set_query(example)
    st.markdown('<div class="footer">PIVOT / TURN DATA INTO DIRECTION</div>', unsafe_allow_html=True)
    st.stop()


# -----------------------------------------------------------------------------
# Results data preparation
# -----------------------------------------------------------------------------
results: List[Dict[str, Any]] = st.session_state.get("results", [])
analytics: Dict[str, Any] = st.session_state.get("analytics", {}) or {}
career_fit: Dict[str, Any] = st.session_state.get("career_fit", {}) or {}
ai_summary = st.session_state.get("ai_summary")

industries = sorted({str(job.get("industry")) for job in results if job.get("industry")})
levels = [item.get("level") for item in analytics.get("level_distribution", []) if item.get("level")]
filter_col_1, filter_col_2, filter_col_3 = st.columns([1.3, 1.3, 2.4])
with filter_col_1:
    selected_level = st.selectbox("Cấp độ", ["Tất cả"] + levels, index=0)
with filter_col_2:
    selected_industry = st.selectbox("Ngành", ["Tất cả"] + industries, index=0)
with filter_col_3:
    st.markdown('<div class="section-subtitle" style="margin:29px 0 0; text-align:right;">Kết quả cho: <strong style="color:#0e7475;">{}</strong></div>'.format(safe_text(st.session_state.get("query_input", ""))), unsafe_allow_html=True)

st.session_state.selected_level = None if selected_level == "Tất cả" else selected_level
st.session_state.selected_industry = None if selected_industry == "Tất cả" else selected_industry

filtered_results = [job for job in results if (not st.session_state.selected_level or job.get("job_level") == st.session_state.selected_level) and (not st.session_state.selected_industry or job.get("industry") == st.session_state.selected_industry)]
filtered_results = sorted(filtered_results, key=lambda job: job.get("match_score") or job.get("score") or 0, reverse=True)

skill_counter = Counter()
for job in filtered_results:
    skill_counter.update(skill.lower() for skill in skill_list(job.get("skills")))

top_score = score_percent(filtered_results[0].get("score")) if filtered_results else 0
unique_industries = len({job.get("industry") for job in filtered_results if job.get("industry")})

st.markdown('<div class="section-title">Bức tranh cơ hội</div><div class="section-subtitle">Tín hiệu được rút ra từ các vị trí phù hợp với truy vấn của bạn.</div>', unsafe_allow_html=True)
kpi_cols = st.columns(4)
with kpi_cols[0]:
    render_kpi("Cơ hội phù hợp", len(filtered_results), "vị trí trong tập kết quả")
with kpi_cols[1]:
    render_kpi("Độ tương thích cao nhất", f"{top_score}%", "semantic match score")
with kpi_cols[2]:
    render_kpi("Ngành đang mở", unique_industries, "nhóm tuyển dụng nổi bật")
with kpi_cols[3]:
    render_kpi("Tín hiệu kỹ năng", len(skill_counter), "kỹ năng được phát hiện")

if not ai_summary:
    summary_response = api_get("/recommend/summary", params={"query": st.session_state.get("query_input", "")})
    if summary_response is not None and summary_response.status_code == 200:
        ai_summary = summary_response.json().get("summary")
        if ai_summary:
            st.session_state.ai_summary = ai_summary

if ai_summary:
    st.markdown(f'<div class="insight"><div class="insight-title">✦ AI market read</div><div class="insight-copy">{safe_text(ai_summary)}</div></div>', unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# Core product moment: Career Fit Report
# -----------------------------------------------------------------------------
top_direction = career_fit.get("top_direction") or {}
directions = career_fit.get("directions") or []
if top_direction:
    top_role = safe_text(top_direction.get("role"), "Chưa xác định")
    top_score = int(top_direction.get("fit_score") or 0)
    strengths = top_direction.get("matched_skills") or career_fit.get("profile_strengths") or []
    gaps = top_direction.get("skill_gaps") or career_fit.get("priority_gaps") or []
    strength_chips = "".join(f'<span class="fit-chip">{safe_text(skill)}</span>' for skill in strengths[:6]) or '<span class="fit-meta">Chưa đủ dữ liệu để xác nhận kỹ năng nổi bật.</span>'
    gap_chips = "".join(f'<span class="fit-chip gap">{safe_text(skill)}</span>' for skill in gaps[:6]) or '<span class="fit-meta">Không phát hiện khoảng trống lớn.</span>'

    st.markdown(
        f'<div class="fit-report"><div class="fit-header"><div><div class="fit-kicker">✦ Career fit report</div><div class="fit-headline">{safe_text(career_fit.get("headline"))}</div></div><div class="fit-score"><div class="fit-score-value">{top_score}%</div><div class="fit-score-label">TOP FIT</div></div></div>'
        f'<div class="fit-section"><div class="fit-section-label">Hướng nghề nghiệp nổi bật nhất</div><div class="fit-role">{top_role}</div><div class="fit-meta">{safe_text(top_direction.get("why"))}</div></div></div>',
        unsafe_allow_html=True,
    )
    fit_col_1, fit_col_2 = st.columns(2)
    with fit_col_1:
        st.markdown(f'<div class="fit-section"><div class="fit-section-label">Điểm mạnh đang có</div><div>{strength_chips}</div></div>', unsafe_allow_html=True)
    with fit_col_2:
        st.markdown(f'<div class="fit-section"><div class="fit-section-label">Khoảng trống cần đóng</div><div>{gap_chips}</div></div>', unsafe_allow_html=True)

    if len(directions) > 1:
        st.markdown('<div class="section-title">Các hướng thay thế</div><div class="section-subtitle">Không chỉ có một đáp án — đây là những hướng cũng đang có tín hiệu phù hợp.</div>', unsafe_allow_html=True)
        direction_cols = st.columns(min(3, len(directions)))
        for index, direction in enumerate(directions[:3]):
            direction_chips = "".join(
                f'<span class="fit-chip">{safe_text(skill)}</span>'
                for skill in (direction.get("matched_skills") or [])[:3]
            )
            direction_cols[index].markdown(
                f'<div class="direction-card"><div class="direction-score">{int(direction.get("fit_score") or 0)}% FIT</div><div class="fit-role">{safe_text(direction.get("role"))}</div><div class="fit-meta">{int(direction.get("market_demand") or 0)} cơ hội trong tập kết quả</div><div>{direction_chips}</div></div>',
                unsafe_allow_html=True,
            )

    action_plan = career_fit.get("action_plan") or []
    if action_plan:
        st.markdown('<div class="section-title">Bước tiếp theo đề xuất</div><div class="section-subtitle">Một lộ trình ngắn để biến insight thành hành động thực tế.</div>', unsafe_allow_html=True)
        action_html = "".join(
            f'<div class="action-card"><div class="action-number">{safe_text(item.get("phase"))}</div><div><div class="action-title">{safe_text(item.get("title"))}</div><div class="action-detail">{safe_text(item.get("detail"))}</div></div></div>'
            for item in action_plan
        )
        st.markdown(f'<div class="fit-section">{action_html}</div>', unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# Insight tabs
# -----------------------------------------------------------------------------
overview_tab, jobs_tab, roadmap_tab = st.tabs(["Tổng quan thị trường", "Cơ hội phù hợp", "Lộ trình kỹ năng"])

with overview_tab:
    chart_col, level_col = st.columns([1.25, 1])
    with chart_col:
        st.markdown('<div class="section-title">Ngành đang tuyển</div><div class="section-subtitle">Số cơ hội trong tập kết quả đã lọc.</div>', unsafe_allow_html=True)
        industry_counts = Counter(job.get("industry", "Khác") for job in filtered_results)
        trend_data = industry_counts.most_common(8)
        if trend_data:
            labels = [str(item[0])[:28] for item in trend_data][::-1]
            values = [item[1] for item in trend_data][::-1]
            fig, ax = plt.subplots(figsize=(7, 3.5))
            fig.patch.set_alpha(0)
            ax.set_facecolor("none")
            ax.barh(labels, values, color="#0e7475", height=.58)
            ax.spines[:].set_visible(False)
            ax.tick_params(axis="both", colors="#6c7b83", labelsize=9, length=0)
            ax.grid(axis="x", color="#dce5e7", linewidth=.7)
            ax.set_axisbelow(True)
            st.pyplot(fig, use_container_width=True)
            plt.close(fig)
        else:
            st.info("Chưa có đủ dữ liệu ngành để hiển thị.")

    with level_col:
        st.markdown('<div class="section-title">Phân bổ cấp độ</div><div class="section-subtitle">Thị trường đang cần người ở đâu?</div>', unsafe_allow_html=True)
        level_data = analytics.get("level_distribution", [])
        if level_data:
            st.bar_chart({item.get("level", "Unknown"): item.get("count", 0) for item in level_data}, color="#ff846d", height=250)
        else:
            st.info("Chưa có dữ liệu cấp độ.")

    st.markdown('<div class="section-title">Kỹ năng được săn đón</div><div class="section-subtitle">Các kỹ năng xuất hiện nhiều nhất trong kết quả hiện tại.</div>', unsafe_allow_html=True)
    if skill_counter:
        top_skills = skill_counter.most_common(12)
        max_count = max(count for _, count in top_skills) or 1
        skill_cols = st.columns(4)
        for index, (skill, count) in enumerate(top_skills):
            skill_cols[index % 4].markdown(f'<div class="skill-card"><div class="skill-name">{safe_text(skill)}</div><div class="skill-count">{count} job signal{"s" if count != 1 else ""}</div><div class="skill-bar"><div class="skill-fill" style="width:{round(count / max_count * 100)}%"></div></div></div>', unsafe_allow_html=True)
    else:
        st.info("Chưa phát hiện được kỹ năng trong dữ liệu trả về.")

with jobs_tab:
    st.markdown(f'<div class="section-title">{len(filtered_results)} cơ hội được xếp hạng</div><div class="section-subtitle">Hiển thị những vị trí có tín hiệu phù hợp nhất với mục tiêu của bạn.</div>', unsafe_allow_html=True)
    if not filtered_results:
        st.info("Không có vị trí nào khớp với bộ lọc hiện tại.")
    for job in filtered_results[:20]:
        title = safe_text(job.get("job_title"), "Untitled role")
        score = int(job.get("match_score") or score_percent(job.get("score")))
        skills = skill_list(job.get("skills"))[:8]
        tags = "".join(f'<span class="tag">{safe_text(skill)}</span>' for skill in skills)
        reasons = job.get("recommendation_reasons") or job.get("match_reasons") or []
        reason_text = safe_text(reasons[0]) if reasons else "Được xếp hạng theo mức độ phù hợp tổng thể"
        label = safe_text(job.get("recommendation_label"), "Recommended")
        st.markdown(f'<div class="job-card"><div style="display:flex; justify-content:space-between; gap:20px;"><div style="flex:1;"><h3>{title}</h3><div class="job-meta"><span>⌖ {safe_text(job.get("city"))}</span><span>◈ {safe_text(job.get("industry"))}</span><span>◎ {safe_text(job.get("job_level"))}</span></div></div><div style="width:150px;"><div class="job-score">{label} · {score}%</div><div class="score-track"><div class="score-fill" style="width:{score}%"></div></div></div></div><div>{tags}</div><div class="job-reason">✦ {reason_text}</div></div>', unsafe_allow_html=True)
        if st.session_state.get("token"):
            action_cols = st.columns([1, 1, 1, 3])
            if action_cols[0].button("Đã xem", key=f"view_{job.get('job_id')}", use_container_width=True):
                if track_job_event(job.get("job_id"), "view"):
                    st.toast("Đã ghi nhận lượt xem")
            if action_cols[1].button("Lưu", key=f"save_{job.get('job_id')}", use_container_width=True):
                if track_job_event(job.get("job_id"), "save"):
                    st.toast("Đã lưu tín hiệu sở thích")
            if action_cols[2].button("Ứng tuyển", key=f"apply_{job.get('job_id')}", use_container_width=True):
                if track_job_event(job.get("job_id"), "apply"):
                    st.toast("Đã ghi nhận ý định ứng tuyển")
            if action_cols[3].button("Không phù hợp", key=f"dismiss_{job.get('job_id')}", use_container_width=True):
                if track_job_event(job.get("job_id"), "dismiss"):
                    st.toast("Đã giảm ưu tiên nhóm job tương tự")
        with st.expander("Xem mô tả & yêu cầu"):
            reasons = job.get("match_reasons") or []
            gaps = job.get("skill_gaps") or []
            if reasons:
                st.markdown("**Vì sao phù hợp**")
                for reason in reasons:
                    st.markdown(f"- {safe_text(reason)}")
            if gaps:
                st.markdown("**Skill gap cần lưu ý:** " + ", ".join(safe_text(gap) for gap in gaps))
            job_id = job.get("job_id")
            detail_response = api_get(f"/jobs/{job_id}") if job_id else None
            if detail_response is not None and detail_response.status_code == 200:
                detail = detail_response.json()
                detail_col_1, detail_col_2 = st.columns(2)
                with detail_col_1:
                    st.markdown("**Mô tả công việc**")
                    st.write(detail.get("job_description") or "Chưa có mô tả.")
                with detail_col_2:
                    st.markdown("**Yêu cầu**")
                    st.write(detail.get("job_requirement") or "Chưa có yêu cầu.")
            else:
                st.warning("Không thể tải chi tiết vị trí này.")

with roadmap_tab:
    st.markdown('<div class="section-title">Lộ trình bù đắp khoảng trống</div><div class="section-subtitle">Những kỹ năng nổi bật hơn ở cấp độ tiếp theo, dựa trên dữ liệu tuyển dụng hiện có.</div>', unsafe_allow_html=True)
    career_path = analytics.get("career_path", {}) or {}
    if career_path:
        for path, skills in career_path.items():
            parts = path.split(" -> ")
            title = "  →  ".join(safe_text(part.title()) for part in parts)
            skill_tags = "".join(f'<span class="tag">{safe_text(skill)}</span>' for skill in (skills or []))
            first_skill = safe_text(skills[0]) if skills else "các kỹ năng cốt lõi"
            empty_gap = '<span class="roadmap-note">Chưa đủ dữ liệu để xác định skill gap.</span>'
            st.markdown(f'<div class="roadmap"><div class="roadmap-title">{title}</div><div class="roadmap-note">Ưu tiên học {first_skill} để tiến gần hơn tới cấp độ tiếp theo.</div>{skill_tags or empty_gap}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="empty"><div class="empty-mark">↗</div><h3>Roadmap sẽ rõ hơn khi dữ liệu dày hơn</h3><p>Hãy thử truy vấn rộng hơn hoặc bỏ bớt bộ lọc để PIVOT có thể so sánh nhiều cấp độ nghề nghiệp.</p></div>', unsafe_allow_html=True)

st.markdown('<div class="footer">PIVOT / TURN DATA INTO DIRECTION  •  AI-POWERED CAREER INTELLIGENCE</div>', unsafe_allow_html=True)
