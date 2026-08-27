import requests
import json
import time
import random
import copy
import os
from datetime import datetime


BASE_URL = "https://ms.vietnamworks.com/job-search/v1.0/search"
BASE_SITE = "https://www.vietnamworks.com"
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"

RAW_DIR = DATA_DIR / "raw"
LOG_DIR = DATA_DIR / "logs"

RAW_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

MASTER_FILE = RAW_DIR / "vw_jobs_crawl_raw.jsonl"

today = datetime.now().strftime("%Y%m%d")
OUTPUT_FILE = RAW_DIR / f"vw_jobs_{today}.jsonl"
LOG_FILE = LOG_DIR / f"crawl_log_{today}.txt"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Content-Type": "application/json",
    "Origin": "https://www.vietnamworks.com",
    "Referer": "https://www.vietnamworks.com/",
    "x-source": "Page-Container"
}


PAYLOAD_TEMPLATE = {
    "userId": 0,
    "query": "",
    "filter": [],
    "ranges": [],
    "order": [],
    "hitsPerPage": 50,
    "page": 0,
    "retrieveFields": [
    "jobId",
    "jobTitle",
    "companyName",
    "industriesV3",
    "jobFunctionsV3",
    "groupJobFunctionsV3",
    "workingLocations",
    "skills",
    "jobDescription",
    "jobRequirement",
    "jobLevel",
    "yearsOfExperience",
    "salaryMin",
    "salaryMax",
    "createdOn",
    "expiredOn"
],
    "summaryVersion": ""
}


# ---------------- LOG ----------------
def log(msg):

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    message = f"[{ts}] {msg}"

    print(message)

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(message + "\n")

# ---------------- DRIVER ----------------


# ---------------- LOAD EXISTING URL ----------------
def load_urls_from_file(file_path):

    if not os.path.exists(file_path):
        return set()

    urls = set()

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                obj = json.loads(line)
                if obj.get("url"):
                    urls.add(obj["url"])
            except:
                pass

    return urls



def collect_jobs():

    page = 0
    total_pages = None
    jobs_data = []

    while True:

        payload = copy.deepcopy(PAYLOAD_TEMPLATE)
        payload["page"] = page

        r = requests.post(BASE_URL, headers=HEADERS, json=payload)

        if r.status_code != 200:
            log("API error")
            break

        result = r.json()

        meta = result.get("meta", {})
        total_pages = meta.get("nbPages")

        jobs = result.get("data", [])

        if not jobs:
            break

        log(f"Collect page {page+1}/{total_pages}")

        for job in jobs:

            job_id = job.get("jobId")

            url = f"{BASE_SITE}/{job_id}-jv"

            job_data = {
                "jobId": job.get("jobId"),
                "jobTitle": job.get("jobTitle"),
                "companyName": job.get("companyName"),

                "industriesV3": job.get("industriesV3"),
                "jobFunctionsV3": job.get("jobFunctionsV3"),
                "groupJobFunctionsV3": job.get("groupJobFunctionsV3"),

                "workingLocations": job.get("workingLocations"),

                "skills": job.get("skills"),

                "jobDescription": job.get("jobDescription"),
                "jobRequirement": job.get("jobRequirement"),

                "jobLevel": job.get("jobLevel"),
                "yearsOfExperience": job.get("yearsOfExperience"),

                "salaryMin": job.get("salaryMin"),
                "salaryMax": job.get("salaryMax"),
                "createdOn": job.get("createdOn"),
                "expiredOn": job.get("expiredOn"),
                "url": url
            }
            jobs_data.append(job_data)

        page += 1

        if total_pages and page >= total_pages:
            break

        time.sleep(random.uniform(1,2))

    return jobs_data
def merge_daily_to_master():

    if not os.path.exists(OUTPUT_FILE):
        log("Daily file not found")
        return

    master_urls = load_urls_from_file(MASTER_FILE)

    log(f"Master dataset jobs: {len(master_urls)}")

    added = 0

    with open(OUTPUT_FILE, "r", encoding="utf-8") as daily,\
         open(MASTER_FILE, "a", encoding="utf-8") as master:

        for line in daily:

            try:
                obj = json.loads(line)

                url = obj.get("url")

                if not url:
                    continue

                if url in master_urls:
                    continue

                master.write(json.dumps(obj, ensure_ascii=False) + "\n")

                master_urls.add(url)

                added += 1

            except:
                pass

    log(f"Added {added} new jobs to master dataset")

# ---------------- CRAWL DETAIL ----------------


# ---------------- MAIN ----------------
def crawl():

    log("Collecting jobs from API...")

    jobs = collect_jobs()

    log(f"Total jobs: {len(jobs)}")

    existing_daily = load_urls_from_file(OUTPUT_FILE)
    existing_master = load_urls_from_file(MASTER_FILE)

    existing_urls = existing_daily.union(existing_master)

    log(f"Existing jobs: {len(existing_urls)}")

    new_jobs = [j for j in jobs if j["url"] not in existing_urls]

    log(f"New jobs: {len(new_jobs)}")

    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:

        for job in new_jobs:

            f.write(json.dumps(job, ensure_ascii=False) + "\n")

    log("Merging daily dataset to master...")

    merge_daily_to_master()

    log("DONE")
    return {
        "collected_rows": len(jobs),
        "new_rows": len(new_jobs),
        "existing_rows": len(existing_urls),
    }


if __name__ == "__main__":
    crawl()
