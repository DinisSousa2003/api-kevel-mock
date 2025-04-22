import sys
import os

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


import json
import requests
import random
import time
import argparse
from threading import Thread, Condition
from collections import defaultdict
from imports.test_helper import GetType, PutType

BASE_URL = "http://127.0.0.1:8000"

# Define the date range
START = 1733011200 #1 December 2024 00:00:00
END = 1743379200 #31 March 2025 00:00:00

put_request_times = defaultdict(list)
get_request_times = defaultdict(list)


# Function to get a random timestamp between given range
def random_timestamp(start, end):
    delta = end - start
    random_timestamp = random.randint(0, delta)
    return (start + random_timestamp) * 1000

def put_requests(endpoint, number_ops, user_id_set, condition, ops_per_second):
    headers = {'Content-Type': 'application/json'}
    n = 0
    with open(f'dataset/updates-0.jsonl', "r") as updates:
            for line in updates:
                    payload = json.loads(line.strip())
                    user_id = payload.get("userId")

                    response = requests.patch(endpoint, headers=headers, json=payload)
                    elapsed = response.elapsed.total_seconds()

                    #SEND THE USER ID TO THE GET PROCESS SO IT CAN GET THE IDS
                    if user_id:
                        with condition:
                            user_id_set.add(user_id)
                            condition.notify()
                                                
                    #STORE INFORMATION OVER THE TIME FOR THE GIVEN RESPONSE TYPE
                    data = response.json()
                    response_type = data.get("response", "UNKNOWN")

                    #print(f"[PUT] ID: {user_id} | Status: {PutType(response_type)} | Time: {elapsed:.4f}s")

                    put_request_times[response_type].append(elapsed)

                    n += 1
                    if n == number_ops:
                        break

                    sleep_time = max(0, (1 / ops_per_second) - elapsed)
                    time.sleep(sleep_time)
                    

def get_requests(endpoint, number_ops, user_id_set, condition, pct_get_now, ops_per_second):
    headers = {'Content-Type': 'application/json'}
    n = 0
    while n < number_ops:
        with condition:
            while not user_id_set:
                print("[GET] Waiting for user IDs to become available...")
                condition.wait()
            user_id = random.choice(list(user_id_set))
                
        is_now = random.randint(1, 100) <= pct_get_now
        url = f"{endpoint}/{user_id}"
        params = {}

        if not is_now:
            params["timestamp"] = random_timestamp(START, END)

        response = requests.get(url, headers=headers, params=params)
        elapsed = response.elapsed.total_seconds()

        if response.status_code == 404:
            response_type = GetType.NO_USER_AT_TIME
            #print(f"[GET] ID: {user_id} | Status: {response_type} | Time: {elapsed:.4f}s")

        else:
            #STORE INFORMATION OVER THE TIME FOR THE GIVEN RESPONSE TYPE
            data = response.json()
            response_type = data.get("response", "UNKNOWN")
            #print(f"[GET] ID: {user_id} | Status: {GetType(response_type)} | Time: {elapsed:.4f}s")


        n += 1

        get_request_times[response_type].append(elapsed)
        sleep_time = max(0, (1 / ops_per_second) - elapsed)
        time.sleep(sleep_time)

    
# Argument parsing
def parse_args():
    parser = argparse.ArgumentParser(description="Test program for a database.")
    parser.add_argument("mode", choices=["diff", "state"], help="Mode of operation: 'diff' or 'state'")
    parser.add_argument("num_ops", type=int, help="Number of operations to perform")
    parser.add_argument("pct_get", type=int, choices=range(0, 101), metavar="[0-100]",
                        help="Percentage of GET operations (0-100)")
    parser.add_argument("pct_get_now", type=int, choices=range(0, 101), metavar="[0-100]",
                        help="Percentage of GET operations that do not include a timestamp (0-100)")
    parser.add_argument("ops_per_second", type=int, help="Rate of operations")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    print(f"Mode: {args.mode}")
    print(f"Number of operations: {args.num_ops}")
    print(f"Percentage of GETs: {args.pct_get}%")
    print(f"Percentage of GETs as of now: {args.pct_get_now}%")
    print(f"Ops per second (request rate): {args.ops_per_second} per second")

    MODE, NUM_OPS, PCT_GET, PCT_NOW, RATE = args.mode, args.num_ops, args.pct_get, args.pct_get_now, args.ops_per_second

    USER_ENDPOINT = f"{BASE_URL}/users/{MODE}"

    total_puts = NUM_OPS * (100 - PCT_GET) // 100
    total_gets = NUM_OPS - total_puts

    user_id_set = set()
    condition = Condition()

    put_thread = Thread(target=put_requests, args=(USER_ENDPOINT, total_puts, user_id_set, condition, RATE))
    get_thread = Thread(target=get_requests, args=(USER_ENDPOINT, total_gets, user_id_set, condition, PCT_NOW, RATE))

    put_thread.start()
    get_thread.start()

    put_thread.join()
    get_thread.join()

    print("All operations completed.")

    #Get size occupied

    # url = USER_ENDPOINT + "/db/size"
    # response = requests.get(url)

    # print("\n=== Size Occupied Summary ===")
    # print(response.json())
    

    print("\n=== PUT Request Timing Summary ===")
    for status, times in put_request_times.items():
        avg = sum(times) / len(times) if times else 0
        print(f"Status {PutType(status)}: {len(times)} requests, Avg Time: {avg:.4f}s")

    print("\n=== GET Request Timing Summary ===")
    for status, times in get_request_times.items():
        avg = sum(times) / len(times) if times else 0
        print(f"Status {GetType(status)}: {len(times)} requests, Avg Time: {avg:.4f}s")