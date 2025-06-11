import csv
import sys
import os
import requests

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from locust import HttpUser, constant_throughput, task, events
import json
import random
import argparse
from collections import defaultdict
import locust.stats
import matplotlib.pyplot as plt
import numpy as np
locust.stats.CONSOLE_STATS_INTERVAL_SEC = 600
from enum import Enum
import gevent
from datetime import datetime

class PutType(Enum):
    PAST = 1
    MOST_RECENT = 2
    NO_UPDATE = 3

class GetType(Enum):
    CURRENT = 1
    TIMESTAMP = 2
    NO_USER_AT_TIME = 3


# Command-line argument placeholders
USER_MODE = "diff"
PCT_GET = 80
PCT_GET_NOW = 50
DB_NAME = "xtdb2"
TIME = 60
USERS = 1
RATE = 10
HOST = "http://10.0.63.154:8000/users"

START = 1733011200  # Dec 1, 2024
END = 1743379200    # Mar 31, 2025

db_size_greenlet = None
output_folder = None

put_request_times = defaultdict(list)
get_request_times = defaultdict(list)

headers = {'Content-Type': 'application/json'}

running_check = True

user_id_set = set()

def random_timestamp(start, end):
    return (start + random.randint(0, end - start)) * 1000

def periodic_db_size_check(host, db_name, user_mode):
    global running_check

    csv_path = os.path.join(output_folder, "size_query.csv")
    while running_check:
        try:
            response = requests.get(f"{host}/users/{user_mode}/db/size")
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            if response.status_code == 200:
                size_dict = response.json()
                with open(csv_path, 'a') as f:
                    for key, value in size_dict.items():
                        f.write(f"{timestamp},{key},{value}\n")
                print(f"[DB SIZE CHECK] Current size of {db_name}: {size_dict}")
            else:
                print(f"[DB SIZE CHECK] Failed to get size for {db_name}: {response.status_code}")
        except Exception as e:
            print(f"[DB SIZE CHECK] Error checking database size: {e}")
        gevent.sleep(3600)  # Check every hour

@events.init_command_line_parser.add_listener
def init_parser(parser: argparse.ArgumentParser):
    parser.add_argument("--mode", default="diff", choices=["diff", "state"], help="User endpoint mode")
    parser.add_argument("--pct-get", type=int, default=80, help="Percentage of GETs (0-100)")
    parser.add_argument("--pct-get-now", type=int, default=50, help="Percentage of GETs without timestamp")
    parser.add_argument("--db", type=str, required=False, default="xtdb2", help="Name of the database being used (to store output)")
    parser.add_argument("--time", type=int, required=False, default="60", help="Time of test in minutes")
    parser.add_argument("--user-number", type=int, required=False, default="10", help="Number of users per test")
    parser.add_argument("--rate", type=float, required=False, default="10", help="Wait time between requests in seconds")

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    global USER_MODE, PCT_GET, PCT_GET_NOW, DB_NAME, TIME, USERS, RATE, HOST, db_size_greenlet, output_folder
    USER_MODE = environment.parsed_options.mode
    PCT_GET = environment.parsed_options.pct_get
    PCT_GET_NOW = environment.parsed_options.pct_get_now
    DB_NAME = environment.parsed_options.db
    TIME = environment.parsed_options.time
    USERS = environment.parsed_options.user_number
    RATE = environment.parsed_options.rate
    HOST = environment.host

    output_folder = f"output/{DB_NAME}/{USER_MODE}/time-{TIME}-users-{USERS}-gpt-{PCT_GET}-now-{PCT_GET_NOW}-rate-{RATE}"

    # Start background monitoring size task
    db_size_greenlet = gevent.spawn(periodic_db_size_check, HOST, DB_NAME, USER_MODE)
    
    print(f"\n--- Starting test with parameters ---")
    print(f"Database: {DB_NAME}")
    print(f"Mode: {USER_MODE}")
    print(f"GET percentage: {PCT_GET}%")
    print(f"GETs as of now: {PCT_GET_NOW}%")
    print(f"Test duration: {TIME} minutes")
    print(f"Number of users: {USERS}")
    print(f"Rate: {RATE} seconds")
    print(f"-------------------------------------")

@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    global output_folder, running_check

    os.makedirs(output_folder, exist_ok=True)

    #Stop checking size (run one last time?)
    running_check = False
    db_size_greenlet.kill()

    def build_csv_row(label, times):
        count = len(times)
        if count == 0:
            return [label, 0, "", "", "", "", "", "", "", ""]
        
        stats = get_stats(times)
        return [
            label,
            count,
            f"{stats['avg']:.6f}",
            f"{stats['min']:.6f}",
            f"{stats['max']:.6f}",
            f"{stats['p25']:.6f}",
            f"{stats['p50']:.6f}",
            f"{stats['p75']:.6f}",
            f"{stats['p90']:.6f}",
            f"{stats['p99']:.6f}"
        ]

    def get_stats(times):
        return {
            "avg": sum(times) / len(times),
            "min": min(times),
            "max": max(times),
            "p25": np.percentile(times, 25),
            "p50": np.percentile(times, 50),
            "p75": np.percentile(times, 75),
            "p90": np.percentile(times, 90),
            "p99": np.percentile(times, 99),
        }

    # === MAIN ===

    csv_rows = []

    # CSV Header
    csv_rows.append(["label", "count", "avg", "min", "max", "p25", "p50", "p75", "p90", "p99"])

    # PUT stats
    all_put_times = [time for times in put_request_times.values() for time in times]
    csv_rows.append(build_csv_row("ALL PUT", all_put_times))

    for resp_type, times in put_request_times.items():
        label = str(PutType(resp_type))
        csv_rows.append(build_csv_row(label, times))

    # GET stats
    all_get_times = [time for times in get_request_times.values() for time in times]
    csv_rows.append(build_csv_row("ALL GET", all_get_times))

    for resp_type, times in get_request_times.items():
        label = str(GetType(resp_type))
        csv_rows.append(build_csv_row(label, times))

    # Write CSV summary
    csv_path = os.path.join(output_folder, "times.csv")
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(csv_rows)

class ProfileUser(HttpUser):

    def on_start(self):
        # Open the file once and keep an iterator
        self.update_file = open("dataset/updates-0.jsonl", "r")
        self.update_lines = iter(self.update_file)
        global RATE
        self.wait_time = lambda: constant_throughput(RATE)(self)

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