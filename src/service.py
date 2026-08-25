VALID_STATUSES = {"open", "pending", "resolved"}
VALID_PRIORITIES = {"low", "normal", "high", "urgent"}

class CaseService:
    def __init__(self, store):
        self.store = store

    def list_cases(self, status=None, priority=None):
        cases = self.store.list_cases()
        if status:
            if status not in VALID_STATUSES:
                raise ValueError("invalid_status")
            cases = [case for case in cases if case["status"] == status]
        if priority:
            if priority not in VALID_PRIORITIES:
                raise ValueError("invalid_priority")
            cases = [case for case in cases if case["priority"] == priority]
        return cases

    def get_case(self, case_id):
        return self.store.get_case(case_id)

    def add_note(self, case_id, text, expected_revision):
        if not isinstance(expected_revision, int):
            raise ValueError("invalid_revision")
        return self.store.add_note(case_id, text, expected_revision)
