import sys
import os
import requests

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from locust import HttpUser, task, constant, events
import json
import random
import argparse
from collections import defaultdict
from imports.test_helper import GetType, PutType
import locust.stats
import matplotlib.pyplot as plt
import numpy as np
locust.stats.CONSOLE_STATS_INTERVAL_SEC = 600


# Command-line argument placeholders
USER_MODE = "diff"
PCT_GET = 80
PCT_GET_NOW = 50
DB_NAME = "xtdb2"

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
    parser.add_argument("--db", type=str, required=False, default="xtdb2", help="Name of the database being used (to store output)")

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    global USER_MODE, PCT_GET, PCT_GET_NOW, DB_NAME
    USER_MODE = environment.parsed_options.mode
    PCT_GET = environment.parsed_options.pct_get
    PCT_GET_NOW = environment.parsed_options.pct_get_now
    DB_NAME = environment.parsed_options.db

    print(f"\n--- Starting test ---")
    print(f"Database: {DB_NAME}%")
    print(f"Mode: {USER_MODE}")
    print(f"GET percentage: {PCT_GET}%")
    print(f"GETs as of now: {PCT_GET_NOW}%")

@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    output_folder = f"output/{DB_NAME}/test_{USER_MODE}_{PCT_GET}_{PCT_GET_NOW}"
    os.makedirs(output_folder, exist_ok=True)

    url = USER_ENDPOINT + USER_MODE + "/db/size"
    response = requests.get(url)

    summary_lines = []

    summary_lines.append("\n=== Size Occupied Summary ===")
    for name, size in response.json().items():
        summary_lines.append(f"{name}: {size}")

    summary_lines.append("\n=== PUT SUMMARY by response type ===")
    for resp_type, times in put_request_times.items():
        avg = sum(times) / len(times)
        p90 = np.percentile(times, 90)
        p99 = np.percentile(times, 99)
        summary_lines.append(
            f"Status {PutType(resp_type)}: {len(times)} ops, avg = {avg:.4f}s, p90 = {p90:.4f}s, p99 = {p99:.4f}s"
        )

    summary_lines.append("\n=== GET SUMMARY by response type ===")
    for resp_type, times in get_request_times.items():
        avg = sum(times) / len(times)
        p90 = np.percentile(times, 90)
        p99 = np.percentile(times, 99)
        summary_lines.append(
            f"Status {GetType(resp_type)}: {len(times)} ops, avg = {avg:.4f}s, p90 = {p90:.4f}s, p99 = {p99:.4f}s"
        )

    # Write summary to file
    summary_path = os.path.join(output_folder, "summary.txt")
    with open(summary_path, "w") as f:
        for line in summary_lines:
            print(line)  # Also print to console
            f.write(line + "\n")

    # Create plots
    def plot_distribution(times_dict, title, filename):
        plt.figure(figsize=(10, 6))
        for resp_type, times in times_dict.items():
            if "GET" in title:
                label = GetType(resp_type)
            else:
                label = PutType(resp_type)
            plt.hist(times, bins=20, alpha=0.5, label=label)

            # Percentile lines
            p90 = np.percentile(times, 90)
            p99 = np.percentile(times, 99)
            plt.axvline(p90, color='orange', linestyle='dashed', linewidth=1)
            plt.text(p90, plt.ylim()[1]*0.9, f'p90 ({label})', rotation=90, color='orange')

            plt.axvline(p99, color='red', linestyle='dashed', linewidth=1)
            plt.text(p99, plt.ylim()[1]*0.9, f'p99 ({label})', rotation=90, color='red')

        plt.title(title)
        plt.xlabel("Time (s)")
        plt.ylabel("Number of Requests")
        plt.legend()
        plt.tight_layout()
        plt.savefig(filename)
        plt.close()

    # Save plots to output folder
    put_plot_path = os.path.join(output_folder, "put_distribution.png")
    get_plot_path = os.path.join(output_folder, "get_distribution.png")

    plot_distribution(put_request_times, "PUT Request Time Distribution", "scripts/analysis/put_distribution.png")
    plot_distribution(get_request_times, "GET Request Time Distribution", "scripts/analysis/get_distribution.png")

    plot_distribution(put_request_times, "PUT Request Time Distribution", put_plot_path)
    plot_distribution(get_request_times, "GET Request Time Distribution", get_plot_path)

    print(f"\nSaved request time distribution plots and summary to '{output_folder}'")

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