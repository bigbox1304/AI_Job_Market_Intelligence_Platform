import pandas as pd
import json
import re
from bs4 import BeautifulSoup
from tqdm import tqdm
import os

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"

INPUT_FILE = DATA_DIR / "raw/vw_jobs_crawl_raw.jsonl"
OUTPUT_FILE = DATA_DIR / "processed/vw_jobs_crawl_clean.csv"

(DATA_DIR / "processed").mkdir(parents=True, exist_ok=True)

# ==============================
# NOISE PATTERNS
# ==============================

NOISE_PATTERNS = [
    r"Mức độ phù hợp.*?khác như thế nào\?",
    r"Xem đầy đủ mô tả công việc"
]

# ==============================
# CLEAN JOB TITLE
# ==============================

def clean_job_title(title):

    if not isinstance(title, str):
        return ""

    title = title.lower()

    # remove [urgent], [hot]
    title = re.sub(r"\[.*?\]", " ", title)

    # remove content in parentheses
    title = re.sub(r"\(.*?\)", " ", title)

    # remove salary patterns
    title = re.sub(r"\$?\d+\s*(k|m)?", " ", title)

    # remove locations
    locations = [
        "hcm",
        "hồ chí minh",
        "ha noi",
        "hà nội",
        "da nang",
        "đà nẵng",
        "remote"
    ]

    for loc in locations:
        title = title.replace(loc, " ")

    # remove special char
    title = re.sub(r"[^\w\s]", " ", title)

    # normalize spaces
    title = re.sub(r"\s+", " ", title).strip()

    return title

# ==============================
# REMOVE HTML
# ==============================

def remove_html(text):

    soup = BeautifulSoup(text, "html.parser")

    for tag in soup(["script", "style"]):
        tag.decompose()

    return soup.get_text(separator=" ")


# ==============================
# REMOVE NOISE
# ==============================

def remove_noise(text):

    for pattern in NOISE_PATTERNS:
        text = re.sub(pattern, " ", text, flags=re.IGNORECASE)

    return text


# ==============================
# REMOVE BULLETS
# ==============================

def remove_bullets(text):

    text = re.sub(r"\n?\s*\d+\.\s*", " ", text)
    text = re.sub(r"[•\-\*]", " ", text)

    return text


# ==============================
# CLEAN SPECIAL CHAR
# ==============================

def clean_special(text):

    text = re.sub(r"[^\w\s\+#\.]", " ", text)

    return text


# ==============================
# NORMALIZE
# ==============================

def normalize(text):

    text = text.replace("\n", " ")
    text = text.lower()
    text = re.sub(r"\s+", " ", text).strip()

    return text


# ==============================
# FULL TEXT PIPELINE
# ==============================

def preprocess_text(text):

    if pd.isna(text):
        return ""

    if not isinstance(text, str):
        text = str(text)

    text = remove_html(text)
    text = remove_noise(text)
    text = remove_bullets(text)
    text = clean_special(text)
    text = normalize(text)

    return text
# ==============================
# LOAD JSONL
# ==============================


def clean_data():
    print("Loading raw data...")

    data = []

    # dùng tqdm trực tiếp
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        for line in tqdm(f, desc="Loading lines"):
            data.append(json.loads(line))

    df = pd.DataFrame(data)

    print("Initial shape:", df.shape)

    df = df.drop_duplicates(subset=["jobId"], keep="first")

    df = df.dropna(axis=1, how="all")


    # ==============================
    # FLATTEN STRUCTURES
    # ==============================

    df["skills_text"] = df["skills"].apply(
        lambda x: ", ".join([s.get("skillName","") for s in x])
        if isinstance(x, list) else ""
    )
    df["industry"] = df["industriesV3"].apply(
        lambda x: ", ".join([i["industryV3Name"] for i in x])
        if isinstance(x, list) else ""
    )

    df["job_function"] = df["jobFunctionsV3"].apply(
        lambda x: x.get("jobFunctionV3Name", "")
        if isinstance(x, dict) else ""
    )

    df["job_group"] = df["groupJobFunctionsV3"].apply(
        lambda x: x.get("groupJobFunctionV3Name", "")
        if isinstance(x, dict) else ""
    )

    df["city"] = df["workingLocations"].apply(
        lambda x: x[0]["cityName"]
        if isinstance(x, list) and len(x) > 0 else ""
    )
    df["createdOn"] = pd.to_datetime(df["createdOn"], errors="coerce").dt.normalize()
    df["expiredOn"] = pd.to_datetime(df["expiredOn"], errors="coerce").dt.normalize()

    # ==============================
    # CLEAN TEXT USING PIPELINE
    # ==============================

    print("Cleaning text fields...")

    
    tqdm.pandas(desc="Processing text fields") 

    df["jobDescription"] = df["jobDescription"].progress_apply(preprocess_text)
    df["jobRequirement"] = df["jobRequirement"].progress_apply(preprocess_text)


    # ==============================
    # SALARY PROCESSING
    # ==============================

    df["salaryMin"] = df["salaryMin"].replace(0, pd.NA)
    df["salaryMax"] = df["salaryMax"].replace(0, pd.NA)

    df["salary_avg"] = df[["salaryMin", "salaryMax"]].mean(axis=1)

    df["jobTitle"] = df["jobTitle"].apply(clean_job_title)
    # ==============================
    # SELECT ML FEATURES
    # ==============================

    selected_columns = [
        "jobId",
        "jobTitle",
        "companyName",
        "industry",
        "job_function",
        "job_group",
        "jobLevel",
        "city",
        "skills_text",
        "jobDescription",
        "jobRequirement",
        "yearsOfExperience",
        "createdOn",
        "expiredOn"
    ]

    df_ml = df[selected_columns]

    print("Final ML shape:", df_ml.shape)
    print("Columns:", df_ml.columns.tolist())

    required_cols = [
    "jobTitle",
    "skills_text",
    "jobDescription",
    "jobRequirement",
    "jobLevel",
    "city"
    ]

    df_ml = df_ml.replace(r"^\s*$", pd.NA, regex=True)

    before = len(df_ml)
    df_ml = df_ml.dropna(subset=required_cols)
    after = len(df_ml)

    print(f"Removed rows missing required fields: {before - after}")

    # ==============================
    # SAVE CSV
    # ==============================
    os.makedirs("data/processed", exist_ok=True)
    df_ml.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    print("Saved:", OUTPUT_FILE)
    print("DONE")