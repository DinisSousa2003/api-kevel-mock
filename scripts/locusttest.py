import sys
import os

import requests

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from locust import HttpUser, TaskSet, task, between, constant, events
import json
import random
import argparse
from collections import defaultdict
from imports.test_helper import GetType, PutType

# Command-line argument placeholders
USER_MODE = "diff"
PCT_GET = 80
PCT_GET_NOW = 50

START = 1733011200  # Dec 1, 2024
END = 1743379200    # Mar 31, 2025

USER_ENDPOINT = "http://127.0.0.1:8000/users/"

put_request_times = defaultdict(list)
get_request_times = defaultdict(list)

headers = {'Content-Type': 'application/json'}

user_id_set = set()

def random_timestamp(start, end):
    return (start + random.randint(0, end - start)) * 1000

@events.init_command_line_parser.add_listener
def init_parser(parser: argparse.ArgumentParser):
    parser.add_argument("--mode", default="diff", choices=["diff", "state"], help="User endpoint mode")
    parser.add_argument("--pct-get", type=int, default=80, help="Percentage of GETs (0-100)")
    parser.add_argument("--pct-get-now", type=int, default=50, help="Percentage of GETs without timestamp")

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    global USER_MODE, PCT_GET, PCT_GET_NOW
    USER_MODE = environment.parsed_options.mode
    PCT_GET = environment.parsed_options.pct_get
    PCT_GET_NOW = environment.parsed_options.pct_get_now

    print(f"\n--- Starting test ---")
    print(f"Mode: {USER_MODE}")
    print(f"GET percentage: {PCT_GET}%")
    print(f"GETs as of now: {PCT_GET_NOW}%")

@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    url = USER_ENDPOINT + USER_MODE + "/db/size"
    response = requests.get(url)

    print("\n=== Size Occupied Summary ===")
    for name, size in response.json().items():
        print(f"{name}: {size}")

    print("\n=== PUT SUMMARY by response type ===")
    for resp_type, times in put_request_times.items():
        avg = sum(times) / len(times)
        print(f"Status {PutType(resp_type)}: {len(times)} ops, avg = {avg:.4f}s")
    
    print("\n=== GET SUMMARY by response type ===")
    for resp_type, times in get_request_times.items():
        avg = sum(times) / len(times)
        print(f"Status {GetType(resp_type)}: {len(times)} ops, avg = {avg:.4f}s")

class ProfileUser(HttpUser):
    wait_time = constant(1)

    def on_start(self):
        # Open the file once and keep an iterator
        self.update_file = open("dataset/updates-0.jsonl", "r")
        self.update_lines = iter(self.update_file)

    def on_stop(self):
        # Clean up file handle
        self.update_file.close()

    @task
    def mixed_operation(self):
        choice = random.randint(1, 100)
        if choice <= PCT_GET:
            self.do_get()
        else:
            self.do_put()

    def do_put(self):
        try:
            line = next(self.update_lines)
        except StopIteration:
            print("[PUT] End of file reached.")
            return
        
        try:
            payload = json.loads(line.strip())
            user_id = payload.get("userId")

            response = self.client.patch(f"/users/{USER_MODE}", json=payload, headers=headers)
            elapsed = response.elapsed.total_seconds()

            if response.status_code == 404:
                response_type = PutType.NO_UPDATE
            else:
                #STORE INFORMATION OVER THE TIME FOR THE GIVEN RESPONSE TYPE
                data = response.json()
                response_type = data.get("response", "UNKNOWN")

            #SEND THE USER ID TO THE GET PROCESS SO IT CAN GET THE IDS
            if user_id:
                user_id_set.add(user_id)

            put_request_times[response_type].append(elapsed)

        except Exception as e:
            print(f"[PUT] Error: {e}")

    def do_get(self):
        if len(user_id_set) == 0:
            return

        user_id = random.choice(list(user_id_set))

        params = {}
        if random.randint(1, 100) > PCT_GET_NOW:
            params["timestamp"] = random_timestamp(START, END)

        response = self.client.get(f"/users/{USER_MODE}/{user_id}", headers=headers, params=params)
        elapsed = response.elapsed.total_seconds()

        if response.status_code == 404:
            response_type = GetType.NO_USER_AT_TIME
        else:
            data = response.json()
            response_type = data.get("response", "UNKNOWN")

        get_request_times[response_type].append(elapsed)