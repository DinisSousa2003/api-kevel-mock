import json
from terminusdb_client import WOQLQuery as wq
import requests
from requests.auth import HTTPBasicAuth

class TerminusDBAPI():
    def __init__(self, db_name, auth: HTTPBasicAuth):
        self.db_name = db_name
        self.auth = auth

    def get_schema(self):
        url = f"http://127.0.0.1:6363/api/schema/admin/{self.db_name}"

        response = requests.request("GET", url, auth=self.auth)
        schema = json.loads(response.text)

        return schema
    
    def get_history(self, customer_id):
        url = f"http://127.0.0.1:6363/api/history/admin/{self.db_name}?id={customer_id}"

        response = requests.request("GET", url, auth=self.auth)
        commits = json.loads(response.text)

        return commits

    def get_latest_state(self, customer_id, timestamp):
        url = f"http://127.0.0.1:6363/api/history/admin/{self.db_name}?id={customer_id}"

        response = requests.request("GET", url, auth=self.auth)
        commits = json.loads(response.text)

        # Filter commits to only those with timestamps lower than the given timestamp
        valid_commits = [commit for commit in commits if int(commit['message']) <= timestamp]

        # Find the most recent commit among the valid ones
        latest_commit = max(valid_commits, key=lambda x: int(x['message']), default=None)

        if latest_commit:
            return latest_commit['identifier']
        return None


