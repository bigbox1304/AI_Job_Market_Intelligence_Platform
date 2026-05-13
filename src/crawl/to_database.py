import pandas as pd
from psycopg2.extras import execute_values
from src.core.database import get_db, release_db

def insert_to_db():
    conn = None

    try:
        conn = get_db()
        cursor = conn.cursor()

        # ---------- load csv ----------
        from pathlib import Path

        BASE_DIR = Path(__file__).resolve().parents[2]
        DATA_DIR = BASE_DIR / "data"

        CSV_FILE = DATA_DIR / "processed/vw_jobs_crawl_clean.csv"

        df = pd.read_csv(CSV_FILE)

        df["createdOn"] = pd.to_datetime(df["createdOn"], errors="coerce")
        df["expiredOn"] = pd.to_datetime(df["expiredOn"], errors="coerce")

        # ---------- clean basic ----------
        df = df.fillna("")

        df["companyName"] = df["companyName"].str.strip()
        df["jobTitle"] = df["jobTitle"].str.strip()
        df["skills_text"] = df["skills_text"].str.strip()

        # ---------- companies ----------
        companies = df["companyName"].drop_duplicates().tolist()

        cursor.execute("SELECT company_name, company_id FROM companies")
        company_map = dict(cursor.fetchall())

        new_companies = [(c,) for c in companies if c not in company_map]

        if new_companies:
            execute_values(
                cursor,
                "INSERT INTO companies (company_name) VALUES %s",
                new_companies
            )

        # ---------- jobs ----------
        cursor.execute("SELECT company_name, company_id FROM companies")
        company_map = dict(cursor.fetchall())

        jobs_data = []

        for _, row in df.iterrows():
            company_id = company_map.get(row["companyName"])

            jobs_data.append((
                row["jobId"],
                row["jobTitle"],
                company_id,
                row["industry"],
                row["job_function"],
                row["job_group"],
                row["jobLevel"],
                row["city"],
                row["jobDescription"],
                row["jobRequirement"],
                row["yearsOfExperience"],
                row["createdOn"],
                row["expiredOn"]
            ))

        execute_values(
            cursor,
            """
            INSERT INTO jobs (
                job_id,
                job_title,
                company_id,
                industry,
                job_function,
                job_group,
                job_level,
                city,
                job_description,
                job_requirement,
                years_of_experience,
                created_on,
                expired_on
            ) VALUES %s
            ON CONFLICT (job_id) DO NOTHING
            """,
            jobs_data
        )

        # ---------- extract skills ----------
        skill_set = set()
        job_skill_map = []

        for _, row in df.iterrows():
            job_id = row["jobId"]
            skills = row["skills_text"].split(",")

            for skill in skills:
                skill = skill.strip().lower()
                if skill:
                    skill_set.add(skill)
                    job_skill_map.append((job_id, skill))

        # ---------- insert skills ----------
        cursor.execute("SELECT LOWER(skill_name), skill_id FROM skills")
        skill_map = dict(cursor.fetchall())

        new_skills = [(s,) for s in skill_set if s not in skill_map]

        if new_skills:
            execute_values(
                cursor,
                "INSERT INTO skills (skill_name) VALUES %s",
                new_skills
            )

        cursor.execute("SELECT skill_name, skill_id FROM skills")
        skill_map = dict(cursor.fetchall())

        # ---------- job_skills ----------
        job_skills_data = []

        for job_id, skill_name in job_skill_map:
            skill_id = skill_map.get(skill_name)
            if skill_id:
                job_skills_data.append((job_id, skill_id))

        execute_values(
            cursor,
            """
            INSERT INTO job_skills (job_id, skill_id)
            VALUES %s
            ON CONFLICT DO NOTHING
            """,
            job_skills_data
        )

        # commit ONCE
        conn.commit()
        cursor.close()

    except Exception as e:
        if conn:
            conn.rollback()
        raise

    finally:
        if conn:
            release_db(conn)

    print("ETL Completed Successfully")