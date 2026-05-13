class SearchHistoryService:

    def __init__(self, repo):
        self.repo = repo

    def save_history(self, user_email, query, filters):
        if not user_email:
            return

        self.repo.save(user_email, query, filters)

    def get_history(self, user_email):
        return self.repo.get_by_user(user_email)