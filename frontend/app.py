import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt

API_URL = "http://api:8000"

st.set_page_config(page_title="Job Recommendation", layout="wide")

query_params = st.query_params

if "token" in query_params:
    st.session_state["token"] = query_params["token"]
    st.session_state["user"] = query_params.get("name", "User")


headers = {}

if "token" in st.session_state:
     headers["Authorization"] = f"Bearer {st.session_state['token']}"

    
if "selected_level" not in st.session_state:
    st.session_state["selected_level"] = None

if "selected_industry" not in st.session_state:
    st.session_state["selected_industry"] = None

    
if st.button(" Login with Google"):
    st.write(
        '<meta http-equiv="refresh" content="0; url=http://localhost:8000/auth/google/login">',
        unsafe_allow_html=True
    )
if "user" in st.session_state:
    st.success(f"Logged in as: {st.session_state['user']}")

# =========================================
# PERSONALIZED HOME
# =========================================
if "token" in st.session_state:

    # chỉ hiện khi chưa search
    if "results" not in st.session_state:

        try:
            res = requests.get(
                f"{API_URL}/recommend/personalized",
                headers=headers
            )

            if res.status_code == 200:
                data = res.json()

                if data.get("suggested_keywords"):

                    st.subheader("🔥 Gợi ý cho bạn")

                    # compact layout
                    cols = st.columns(min(5, len(data["suggested_keywords"])))

                    for i, kw in enumerate(data["suggested_keywords"]):
                        if cols[i].button(kw, use_container_width=True):
                            st.session_state["history_query"] = kw
                            st.rerun()

                if data.get("jobs"):
                    st.subheader("💼 Công việc phù hợp")

                    for job in data["jobs"][:5]:
                        st.markdown(
                            f"**{job['job_title']}**  \n"
                            f"📍 {job['city']} | 🏢 {job['industry']}"
                        )

                st.divider()

        except:
            pass
    
# =========================================
# HISTORY (SIDEBAR)
# =========================================
if "token" in st.session_state:

    try:
        history_res = requests.get(
            f"{API_URL}/history",
            headers=headers
        )

        if history_res.status_code == 200:
            history = history_res.json()

            st.sidebar.subheader("🕓 Search History")

            for item in history:
                if st.sidebar.button(item["query"]):
                    st.session_state["history_query"] = item["query"]

    except:
        pass
# =========================================
# TITLE
# =========================================
st.title(" AI Job Recommendation System")
st.markdown("Gợi ý công việc dựa trên kỹ năng / mô tả của bạn")

# =========================================
# INPUT
# =========================================
default_text = st.session_state.get("history_query", "")

user_input = st.text_area(
    "Nhập kỹ năng hoặc mô tả của bạn:",
    value=default_text,
    placeholder="Ví dụ: python, machine learning, data analyst..."
)


# =========================================
# CALL API
# =========================================
if st.button("🔍 Recommend Jobs"):

    if not user_input.strip():
        st.warning("Vui lòng nhập dữ liệu")
        st.stop()

    with st.spinner("Đang tìm job phù hợp..."):

        try:
            

            response = requests.post(
                f"{API_URL}/recommend/analytics",
                headers=headers,
                json={
                    "text": user_input
                }
            )

            if response.status_code != 200:
                st.error("API lỗi")
                st.stop()

            data = response.json()

            # SAVE SESSION
            st.session_state["results"] = data.get("results", [])
            st.session_state["analytics"] = data.get("analytics", {})
            st.session_state["ai_summary"] = data.get("ai_summary", "")
        except Exception as e:
            st.error(f"Không kết nối được API: {e}")
            st.stop()


# =========================================
# LOAD FROM SESSION
# =========================================
results = st.session_state.get("results", [])
analytics = st.session_state.get("analytics", {})

if not results:
    st.info("Nhập dữ liệu và bấm Recommend Jobs")
    st.stop()

# =========================================
# ANALYTICS + FILTER
# =========================================
st.subheader("Market Insights")

ai_summary = st.session_state.get("ai_summary")


if not ai_summary:

    import time

    for _ in range(6):  # retry ~3s
        try:
            res = requests.get(
                f"{API_URL}/recommend/summary",
                params={"query": user_input},
                headers=headers
            )

            if res.status_code == 200:
                ai_summary = res.json().get("summary")

                if ai_summary:
                    st.session_state["ai_summary"] = ai_summary
                    break

        except Exception:
            pass

        time.sleep(0.5)

if ai_summary:
    st.subheader("AI Market Analysis")
    st.info(ai_summary)
else:
    st.info(" AI đang phân tích...")
col1, col2 = st.columns(2)


# =============================
# EXPERIENCE LEVEL (SINGLE BAR)
# =============================
with col1:
    st.markdown("### 📊 Experience Level")

    level_data = analytics.get("level_distribution", [])

    if level_data:
        levels = [item["level"] for item in level_data]

        selected = st.radio(
            "Chọn level",
            ["All"] + levels,
            horizontal=True
        )

        if selected != "All":
            st.session_state["selected_level"] = selected
        else:
            st.session_state["selected_level"] = None


# =============================
# INDUSTRY FILTER
# =============================
with col2:
    st.markdown("### 🏢 Industry")

    industries = list(
        set(job.get("industry", "Unknown") for job in results)
    )

    selected = st.selectbox(
        "Filter theo industry",
        ["All"] + industries
    )

    if selected != "All":
        st.session_state["selected_industry"] = selected
    else:
        st.session_state["selected_industry"] = None



# =========================================
# FILTER JOBS
# =========================================
filtered_results = []

for job in results:

    if st.session_state.get("selected_level"):
        if job.get("job_level") != st.session_state["selected_level"]:
            continue

    if st.session_state.get("selected_industry"):
        if job.get("industry") != st.session_state["selected_industry"]:
            continue

    filtered_results.append(job)




# =========================================
# SKILL DEMAND (DYNAMIC FROM FILTERED DATA)
# =========================================
st.subheader("Skill Demand")

skill_counter = {}

for job in filtered_results:
    skills = job.get("skills", "")

    if isinstance(skills, str):
        skills = [s.strip() for s in skills.split(",")]

    for skill in skills:
        if not skill:
            continue
        skill_counter[skill] = skill_counter.get(skill, 0) + 1


skill_data = [
    {"skill": k, "count": v}
    for k, v in skill_counter.items()
]

if skill_data:

    skill_data = sorted(
        skill_data,
        key=lambda x: x["count"],
        reverse=True
    )[:12]

    cols = st.columns(4)

    for i, item in enumerate(skill_data):
        skill = item["skill"]
        count = item["count"]

        with cols[i % 4]:
            st.markdown(
                f"""
                <div style="
                    padding:10px;
                    border-radius:10px;
                    background-color:#f0f2f6;
                    margin-bottom:8px;
                    text-align:center;
                ">
                    <b>{skill}</b><br>
                    <span style="color:gray">{count} jobs</span>
                </div>
                """,
                unsafe_allow_html=True
            )


# =========================================
# SKILL DEMAND (DYNAMIC FROM FILTERED DATA)
# =========================================
if analytics.get("career_path"):
    st.subheader("Career Roadmap & Skill Gaps")
    st.info("Phân tích lộ trình thăng tiến dựa trên các yêu cầu kỹ năng thực tế từ thị trường.")

    # Duyệt qua từng bước trong lộ trình (ví dụ: Junior -> Middle)
    for path, skills in analytics["career_path"].items():
        # Tách tên level để hiển thị đẹp hơn
        levels = path.split(" -> ")
        path_display = f" {levels[0].title()} ➜ {levels[1].title()} "
        
        with st.container():
            st.markdown(f"####  {path_display}")
            
            if skills:
                # Tạo giao diện các kỹ năng còn thiếu (Skill Gaps) dưới dạng thẻ
                cols = st.columns([1, 4])
                with cols[0]:
                    st.write("**Kỹ năng cần bổ sung:**")
                
                with cols[1]:
                    # Hiển thị skills dưới dạng các tag màu sắc
                    skill_html = "".join([
                        f'<span style="background-color: #E1F5FE; color: #01579B; padding: 4px 10px; '
                        f'border-radius: 15px; margin-right: 8px; font-size: 14px; display: inline-block; '
                        f'margin-bottom: 8px; border: 1px solid #B3E5FC;">{s.upper()}</span>' 
                        for s in skills
                    ])
                    st.markdown(skill_html, unsafe_allow_html=True)
                
                # Thêm một mẹo nhỏ cho người dùng
                st.caption(f"💡 Tip: Tập trung vào `{skills[0]}` vì đây là kỹ năng xuất hiện nhiều nhất ở level {levels[1].title()}.")
            else:
                st.warning("Dữ liệu hiện tại chưa đủ để phân tích sự khác biệt về kỹ năng cho cấp bậc này.")
            
            st.markdown("<br>", unsafe_allow_html=True) # Khoảng cách giữa các roadmap

# =========================================
# JOB TREND BY INDUSTRY
# =========================================
st.subheader("Job Trend by Industry")

industry_counter = {}

for job in filtered_results:
    industry = job.get("industry", "Unknown")
    industry_counter[industry] = industry_counter.get(industry, 0) + 1

if industry_counter:

    trend_data = sorted(
        industry_counter.items(),
        key=lambda x: x[1],
        reverse=True
    )[:8]

    industries = [x[0] for x in trend_data]
    counts = [x[1] for x in trend_data]

    fig, ax = plt.subplots()
    ax.barh(industries, counts)
    ax.invert_yaxis()
    ax.set_xlabel("Number of Jobs")
    ax.set_title("Top Hiring Industries")

    st.pyplot(fig)

# =========================================
# SKILL TREND BY LEVEL
# =========================================
st.subheader(" Skill Trend by Experience Level")

skill_by_level = {}

for job in filtered_results:
    level = job.get("job_level", "Unknown")
    skills = job.get("skills", "")

    if isinstance(skills, str):
        skills = [s.strip() for s in skills.split(",")]

    skill_by_level.setdefault(level, []).extend(skills)

for level, skills in skill_by_level.items():

    if not skills:
        continue

    st.markdown(f"### {level}")

    counter = {}
    for skill in skills:
        if not skill:
            continue
        counter[skill] = counter.get(skill, 0) + 1

    top_skills = sorted(
        counter.items(),
        key=lambda x: x[1],
        reverse=True
    )[:8]

    cols = st.columns(4)

    for i, (skill, count) in enumerate(top_skills):
        with cols[i % 4]:
            st.markdown(
                f"""
                <div style="
                    padding:8px;
                    border-radius:8px;
                    background-color:#f5f7fa;
                    margin-bottom:6px;
                    text-align:center;
                ">
                    <b>{skill}</b><br>
                    <span style="color:gray">{count} jobs</span>
                </div>
                """,
                unsafe_allow_html=True
            )
# =========================================
# JOB RESULTS
# =========================================
st.subheader("Job Results")

# Sort theo score nếu có
filtered_results = sorted(
    filtered_results,
    key=lambda x: x.get("score", 0),
    reverse=True
)

TOP_N = 10
display_results = filtered_results[:TOP_N]

st.success(
    f"Tìm thấy {len(filtered_results)} công việc phù hợp "
    f"(hiển thị {len(display_results)} job liên quan nhất)"
)

for job in display_results:
    with st.container():
        st.subheader(job.get("job_title", "No title"))

        col1, col2, col3 = st.columns(3)

        with col1:
            st.write(f"📍 {job.get('city', 'N/A')}")
        with col2:
            st.write(f"🏢 {job.get('industry', 'N/A')}")
        with col3:
            st.write(f"📊 {job.get('job_level', 'N/A')}")


        st.write(" Skills:", job.get("skills", ""))

        with st.expander("Xem chi tiết"):
            try:
                detail_res = requests.get(
                    f"{API_URL}/jobs/{job['job_id']}",
                    headers=headers
                )

                if detail_res.status_code == 200:
                    detail = detail_res.json()

                    st.markdown("**Mô tả công việc:**")
                    st.write(detail.get("job_description", ""))

                    st.markdown("**Yêu cầu:**")
                    st.write(detail.get("job_requirement", ""))

            except:
                st.warning("Không lấy được chi tiết")

        st.divider()