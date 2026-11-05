"""Current work-order directory behavior."""
from copy import deepcopy
from threading import RLock
from .data import load_workspace, load_activity


class StoreError(Exception):
    def __init__(self, status, code, message):
        self.status, self.code, self.message = status, code, message
        super().__init__(message)


class WorkOrders:
    def __init__(self, workspace=None, activity=None):
        workspace = deepcopy(workspace if workspace is not None else load_workspace())
        self.accounts = {row["id"]: row for row in workspace["accounts"]}
        self.sites = {row["id"]: row for row in workspace["sites"]}
        self.priorities = workspace["priorities"]
        self.jobs = {row["id"]: row for row in workspace["jobs"]}
        self.activity = deepcopy(activity if activity is not None else load_activity())
        self.dataset_revision = workspace["datasetRevision"]
        self.lock = RLock()

    def catalog(self):
        return {"accounts": deepcopy(list(self.accounts.values())),
                "datasetRevision": self.dataset_revision}

    def get_job(self, account, job_id):
        row = self.jobs.get(job_id)
        if account not in self.accounts or row is None or row["accountId"] != account:
            raise StoreError(404, "NOT_FOUND", "Work order not found")
        return row

    def list_jobs(self, account, search="", status="", limit=100):
        if account not in self.accounts:
            raise StoreError(404, "NOT_FOUND", "Account not found")
        search = search.casefold().strip()
        rows = [job for job in self.jobs.values()
                if job["accountId"] == account
                and (not status or job["status"] == status)
                and (not search or any(search in str(job.get(key, "")).casefold()
                                     for key in ("id", "asset", "summary")))]
        rows.sort(key=lambda job: job["id"])
        return {"jobs": deepcopy(rows[:limit]), "total": len(rows),
                "datasetRevision": self.dataset_revision}

    def detail(self, account, job_id):
        with self.lock:
            job = self.get_job(account, job_id)
            return {"job": deepcopy(job), "site": deepcopy(self.sites[job["siteId"]]),
                    "datasetRevision": self.dataset_revision}

    def note(self, account, job_id, note, expected_revision):
        with self.lock:
            job = self.get_job(account, job_id)
            if not isinstance(note, str) or len(note) > 500:
                raise StoreError(400, "INVALID_NOTE", "Note must be text of at most 500 characters")
            if type(expected_revision) is not int or expected_revision < 0:
                raise StoreError(400, "INVALID_REVISION", "expectedRevision must be an integer")
            if job["revision"] != expected_revision:
                raise StoreError(409, "STALE_REVISION", "Work order was changed")
            clean = note.strip()
            changed = clean != job["note"]
            if changed:
                job["note"] = clean
                job["revision"] += 1
                self.dataset_revision += 1
            return {"job": deepcopy(job), "datasetRevision": self.dataset_revision,
                    "unchanged": not changed}
