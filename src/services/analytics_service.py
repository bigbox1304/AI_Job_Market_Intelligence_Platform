from typing import List, Dict
from collections import Counter


class AnalyticsService:
    def __init__(self):
        pass

    # =========================================
    # MAIN ANALYZE
    # =========================================
    def analyze(self, jobs: List[Dict]) -> Dict:

        if not jobs:
            return {
                "job_distribution": [],
                "skill_demand": [],
                "level_distribution": [],
                "career_path": {}
            }

        level_skills = self.skill_by_level(jobs)
        career_path = self.career_gap(level_skills)

        return {
            "job_distribution": self._job_distribution(jobs),
            "skill_demand": self._skill_demand(jobs),
            "level_distribution": self._level_distribution(jobs),
            "career_path": career_path
        }

    # =========================================
    # JOB DISTRIBUTION
    # =========================================
    def _job_distribution(self, jobs: List[Dict]):

        counter = Counter()

        for job in jobs:
            title = job.get("job_title")
            if title:
                counter[title] += 1

        return [
            {"job_title": k, "count": v}
            for k, v in counter.most_common(10)
        ]

    # =========================================
    # SKILL DEMAND
    # =========================================
    def _skill_demand(self, jobs: List[Dict]):

        counter = Counter()

        for job in jobs:
            skills = job.get("skills")

            if not skills:
                continue

            for skill in skills.split(","):
                skill = skill.strip().lower()
                if skill:
                    counter[skill] += 1

        return [
            {"skill": k, "count": v}
            for k, v in counter.most_common(15)
        ]

    # =========================================
    # LEVEL DISTRIBUTION
    # =========================================
    def _level_distribution(self, jobs: List[Dict]):

        counter = Counter()

        for job in jobs:
            level = job.get("job_level")
            if level:
                counter[level] += 1

        return [
            {"level": k, "count": v}
            for k, v in counter.most_common()
        ]
    
    from collections import Counter

    # =========================================
    # SKILL BY LEVEL
    # =========================================
    def skill_by_level(self, jobs):

        level_skill = {}

        for job in jobs:
            level = job.get("job_level")
            skills = job.get("skills", "")

            if not level:
                continue

            level = level.lower()
            level_skill.setdefault(level, Counter())

            if isinstance(skills, str):
                skills = skills.split(",")

            for skill in skills:
                skill = skill.strip().lower()
                if skill:
                    level_skill[level][skill] += 1

        return {
            level: counter.most_common(10)
            for level, counter in level_skill.items()
        }
         
    def career_gap(self, level_skills):
        # 1. Cập nhật danh sách khớp với dữ liệu thực tế của bạn
        # Lưu ý: Phải viết thường toàn bộ vì level_skills đã được .lower() ở hàm skill_by_level
        progression = [
            "intern/student",
            "fresher/entry level", 
            "experienced (non-manager)", 
            "manager",
            "Director and above",
           
        ]

        roadmap = {}
        for i in range(len(progression) - 1):
            current = progression[i]
            next_level = progression[i + 1]

            # Kiểm tra xem level có tồn tại trong dữ liệu trả về không
            if current not in level_skills or next_level not in level_skills:
                continue

            # Lấy tập hợp skill (đã được xử lý lower-case ở hàm skill_by_level)
            current_skills = set([s for s, _ in level_skills[current]])
            next_skills = set([s for s, _ in level_skills[next_level]])

            # Tìm những skill mà level cao hơn yêu cầu nhưng level thấp hơn chưa có
            gap = list(next_skills - current_skills)

            # Nếu không có gap (do tập dữ liệu nhỏ), có thể lấy những skill phổ biến nhất của level tiếp theo
            if not gap:
                gap = [s for s, _ in level_skills[next_level][:5]]

            roadmap[f"{current} -> {next_level}"] = gap[:8]

        return roadmap