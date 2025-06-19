import json
from terminusdb_client import WOQLQuery as wq
import requests
from requests.auth import HTTPBasicAuth
import bisect

class TerminusDBAPI():
    def __init__(self, netloc, user, db_name, auth: HTTPBasicAuth):
        self.netloc = netloc
        self.user = user
        self.db_name = db_name
        self.auth = auth


    def get_users_diff(self, customer_id, timestamp):

        (v_customer, v_attributes_id, v_attributes, v_at) = wq().vars('customer', 'attributes_id', 'attributes', 'at')

        query = wq().select(v_attributes, v_at, 
                    wq().woql_and(
                        wq().select(v_attributes_id, v_at,
                            wq().woql_and(
                                wq().triple(v_customer, "rdf:type", "@schema:Customer"),
                                wq().triple(v_customer, "userId", wq().string(customer_id)),
                                wq().triple(v_customer, "attributes", v_attributes_id),
                                wq().triple(v_customer, "at", v_at),
                                wq().woql_not(
                                    wq().greater(v_at, timestamp)
                                ),
                            ),
                        ),
                        wq().read_document(v_attributes_id,  v_attributes),
                        wq().order_by(v_at, order="asc")
                    )
                )
    
        return query
    
    def get_size(self, user, db_name):
        (v_size) = wq().vars('size')

        query = wq().size(f"{user}/{db_name}", v_size)
        
        return query


    def get_schema(self):
        url = f"http://{self.netloc}/api/schema/{self.user}/{self.db_name}"

        response = requests.request("GET", url, auth=self.auth)
        schema = json.loads(response.text)

        return schema
    
    def get_history(self, customer_id):
        url = f"http://{self.netloc}/api/history/{self.user}/{self.db_name}?id={customer_id}"

        response = requests.request("GET", url, auth=self.auth)
        commits = json.loads(response.text)

        return commits

    def get_latest_state(self, customer_id, timestamp):
        url = f"http://{self.netloc}/api/history/{self.user}/{self.db_name}?id={customer_id}"


        #1. Get all the commits associated with a document

        response = requests.request("GET", url, auth=self.auth)
        commits = json.loads(response.text)

        #print(f"[INFO] Commits: {commits}, commit type: {type(commits)}, first commit: {commits[0] if commits else 'No commits'}, commit type of first: {type(commits[0]) if commits else 'No commits'}")

        #2. In Terminus (with state), we are enforcing that the commits are made in order, so the commits are already sorted
        index = bisect.bisect_right([-(int(commit['message'])) for commit in commits], -timestamp)
        
        # The most recent commit before or at the timestamp is the one at index-1
        latest_commit = commits[index-1] if index > 0 else None

        if latest_commit:
            return latest_commit['identifier']
        return None


