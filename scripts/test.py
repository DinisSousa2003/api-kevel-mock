import requests
import random
import time
import sys

BASE_URL = "http://127.0.0.1:8000"

# Define the date range
START = 1733011200 #1 December 2024 00:00:00
END = 1743379200 #31 March 2025 00:00:00

N_QUERIES = 100

# Function to get a random timestamp between given range
def random_timestamp(start, end):
    delta = end - start
    random_timestamp = random.randint(0, delta)
    return (start + random_timestamp) * 1000

if len(sys.argv) != 2 or sys.argv[1] not in ["state", "diff"]:
    print("Usage: python3 test.py <state|diff>")
    exit(1)

mode = sys.argv[1]

POPULATE_ENDPOINT = f"{BASE_URL}/populate/{mode}/"
USER_ENDPOINT = f"{BASE_URL}/users/{mode}/"

print(f"Started test in mode {mode}!")

# Step 1: Populate the database
start_time = time.time()
populate_response = requests.post(POPULATE_ENDPOINT, params={"u":100, "n":0})
end_time = time.time()

if populate_response.status_code == 200:
    data = populate_response.json()
    user_ids = data.get("ids", set())
    user_ids = list(user_ids)
    print(f"Database populated. Time taken: {end_time - start_time:.4f} seconds")
else:
    print("Failed to populate database.", populate_response.text)
    exit()

# Step 2: Query users at random
query_times = []

for _ in range(N_QUERIES):
    user_id = random.choice(user_ids)
    timestamp = random_timestamp(START, END)
    
    start_time = time.time()
    response = requests.get(f"{USER_ENDPOINT}{user_id}", params={"timestamp": timestamp})
    end_time = time.time()
    
    query_times.append(end_time - start_time)
    if response.status_code == 200:
        print(f"Queried user {user_id} at {timestamp}. Time taken: {end_time - start_time:.4f} seconds")
    else:
        print(f"Failed to query user {user_id}.", response.text)

# Summary
print(f"Average query time: {sum(query_times) / len(query_times):.4f} seconds")
