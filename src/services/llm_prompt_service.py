class LLMPromptService:

    def build_market_prompt(self, query, analytics):

        job_dist = analytics.get("job_distribution", [])
        skill_demand = analytics.get("skill_demand", [])
        level_dist = analytics.get("level_distribution", [])

        return f"""
Bạn là chuyên gia phân tích thị trường việc làm IT.

Người dùng tìm kiếm: "{query}"

Dữ liệu thống kê:

1. Phân bố công việc:
{job_dist}

2. Kỹ năng được yêu cầu nhiều:
{skill_demand}

3. Phân bố cấp độ:
{level_dist}

Hãy viết 1 đoạn phân tích ngắn gọn (5-7 dòng):
- Xu hướng tuyển dụng
- Kỹ năng nên học
- Level phổ biến
- Gợi ý cho ứng viên

Viết bằng tiếng Việt tự nhiên.
"""