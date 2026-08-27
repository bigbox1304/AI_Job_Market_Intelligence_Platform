"""Career-fit analysis that turns recommendation results into a decision aid."""

import re
from collections import Counter, defaultdict
from typing import Any, Dict, List, Set, Tuple


TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9+#./-]*", re.IGNORECASE)
STOP_WORDS = {
    "and", "with", "for", "the", "a", "an", "to", "in", "at", "of",
    "và", "với", "cho", "một", "có", "tại", "ở", "muốn", "tìm", "sang",
    "làm", "việc", "tôi", "mình", "cần", "những", "các",
}


class CareerFitService:
    """Build an explainable career report from the jobs already retrieved."""

    def analyze(self, query: str, jobs: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        query_terms = self._tokens(query)
        enriched_jobs: List[Dict[str, Any]] = []

        for job in jobs:
            enriched = dict(job)
            matched_skills = self._matching_skills(job, query_terms)
            match_score = self._match_score(job, query_terms, matched_skills)
            enriched["match_score"] = match_score
            enriched["match_reasons"] = self._match_reasons(job, query_terms, matched_skills)
            enriched["skill_gaps"] = []
            enriched_jobs.append(enriched)

        directions = self._directions(query_terms, enriched_jobs)
        top_direction = directions[0] if directions else None
        profile_strengths = self._profile_strengths(query_terms, enriched_jobs)
        global_gaps = top_direction.get("skill_gaps", []) if top_direction else []

        for job in enriched_jobs:
            job["skill_gaps"] = self._job_gaps(job, global_gaps)

        report = {
            "query": query,
            "headline": self._headline(top_direction),
            "top_direction": top_direction,
            "directions": directions,
            "profile_strengths": profile_strengths,
            "priority_gaps": global_gaps[:5],
            "action_plan": self._action_plan(global_gaps, top_direction),
        }
        return enriched_jobs, report

    def _tokens(self, value: Any) -> Set[str]:
        tokens = {match.group(0).lower() for match in TOKEN_RE.finditer(str(value or ""))}
        return {token for token in tokens if token not in STOP_WORDS and len(token) > 1}

    def _skills(self, job: Dict[str, Any]) -> List[str]:
        value = job.get("skills") or ""
        if isinstance(value, str):
            return [skill.strip() for skill in value.split(",") if skill.strip()]
        return [str(skill).strip() for skill in value if str(skill).strip()]

    def _matching_skills(self, job: Dict[str, Any], query_terms: Set[str]) -> List[str]:
        return [skill for skill in self._skills(job) if self._tokens(skill) & query_terms]

    def _score_as_percent(self, score: Any) -> float:
        try:
            number = float(score or 0)
        except (TypeError, ValueError):
            return 0
        if number <= 1:
            number *= 100
        return max(0, min(100, number))

    def _match_score(self, job: Dict[str, Any], query_terms: Set[str], matched_skills: List[str]) -> int:
        semantic_score = self._score_as_percent(job.get("recommendation_score", job.get("score")))
        searchable = " ".join(str(job.get(field) or "") for field in ("job_title", "industry", "job_function", "job_level", "city", "skills"))
        field_overlap = len(query_terms & self._tokens(searchable)) / max(1, len(query_terms)) * 100
        skill_signal = min(100, len(matched_skills) / max(1, min(5, len(self._skills(job)))) * 100)
        if semantic_score == 0:
            return round(max(field_overlap, skill_signal))
        return round(semantic_score * 0.7 + max(field_overlap, skill_signal) * 0.3)

    def _match_reasons(self, job: Dict[str, Any], query_terms: Set[str], matched_skills: List[str]) -> List[str]:
        reasons = []
        if matched_skills:
            reasons.append("Khớp kỹ năng: " + ", ".join(matched_skills[:3]))
        title_terms = query_terms & self._tokens(job.get("job_title"))
        if title_terms:
            reasons.append("Tên vai trò gần với mục tiêu tìm kiếm")
        if job.get("job_level"):
            reasons.append(f"Đang tuyển ở cấp độ {job['job_level']}")
        return reasons[:3] or ["Độ tương đồng ngữ nghĩa cao với mô tả của bạn"]

    def _directions(self, query_terms: Set[str], jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        grouped = defaultdict(list)
        for job in jobs:
            title = str(job.get("job_title") or "Vai trò chưa xác định").strip()
            grouped[title].append(job)

        directions = []
        for role, role_jobs in grouped.items():
            skill_counter = Counter()
            matched = Counter()
            for job in role_jobs:
                skills = self._skills(job)
                skill_counter.update(skill.lower() for skill in skills)
                matched.update(skill.lower() for skill in self._matching_skills(job, query_terms))

            gaps = [skill for skill, _ in skill_counter.most_common(8) if not self._tokens(skill) & query_terms][:5]
            avg_score = round(sum(job.get("match_score", 0) for job in role_jobs) / len(role_jobs))
            directions.append({
                "role": role,
                "fit_score": avg_score,
                "market_demand": len(role_jobs),
                "matched_skills": [skill for skill, _ in matched.most_common(5)],
                "skill_gaps": gaps,
                "why": self._direction_why(avg_score, matched, len(role_jobs)),
            })

        return sorted(directions, key=lambda item: (item["fit_score"], item["market_demand"]), reverse=True)[:3]

    def _direction_why(self, score: int, matched: Counter, demand: int) -> str:
        if matched:
            skills = ", ".join(skill for skill, _ in matched.most_common(3))
            return f"Bạn có tín hiệu phù hợp với {skills}; nhóm này hiện có {demand} cơ hội trong tập dữ liệu."
        return f"Đây là hướng có độ tương đồng {score}% và xuất hiện trong {demand} cơ hội phù hợp."

    def _profile_strengths(self, query_terms: Set[str], jobs: List[Dict[str, Any]]) -> List[str]:
        matched = Counter()
        for job in jobs:
            matched.update(skill.lower() for skill in self._matching_skills(job, query_terms))
        return [skill for skill, _ in matched.most_common(6)]

    def _job_gaps(self, job: Dict[str, Any], global_gaps: List[str]) -> List[str]:
        existing = self._tokens(" ".join(self._skills(job)))
        return [gap for gap in global_gaps if not self._tokens(gap) & existing][:3]

    def _headline(self, direction: Dict[str, Any] | None) -> str:
        if not direction:
            return "Hãy mở rộng truy vấn để tìm thấy hướng nghề nghiệp rõ hơn."
        return f"{direction['role']} là hướng nổi bật nhất cho hồ sơ hiện tại của bạn."

    def _action_plan(self, gaps: List[str], direction: Dict[str, Any] | None) -> List[Dict[str, str]]:
        if not direction:
            return []
        role = direction["role"]
        phases = [
            ("01 · Ưu tiên", "Đóng skill gap lớn nhất", "Tập trung vào {skill} — kỹ năng xuất hiện nhiều nhất ở nhóm {role}."),
            ("02 · Thực hành", "Biến kỹ năng thành bằng chứng", "Tạo một project nhỏ dùng {skill} và gắn vào portfolio của bạn."),
            ("03 · Hành động", "Bắt đầu ứng tuyển có chọn lọc", "Ưu tiên các vị trí {role} có match score cao và đọc kỹ phần yêu cầu còn thiếu."),
        ]
        plan = []
        for index, (phase, title, detail) in enumerate(phases):
            skill = gaps[0] if gaps else "kỹ năng cốt lõi"
            plan.append({"phase": phase, "title": title, "detail": detail.format(skill=skill, role=role)})
        return plan
