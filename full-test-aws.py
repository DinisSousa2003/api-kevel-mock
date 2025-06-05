#1. Recieve as argument postgres, terminus or xtdb2

#2. Copy the file envs/<database-name>.env to .env

#3. Run the script in the scripts/docker-<database-name>.sh

#4. Run the application uvicorn main:app --reload

#5. Run the test in the scripts/test.py file python test.py diff 10000 80 80 100

import itertools
import os
import shutil
import subprocess
import sys
import time

#VALID_DATABASES = ["postgres", "xtdb2", "terminus"]
VALID_DATABASES = ["postgres", "xtdb2", "terminus"]
MODE = ["diff", "state"]
TOTAL_TIME = [1]  # in minutes
USERS = [1, 10]
RATE = [0.1, 1, 10]
PCT_GET = [30]
PCT_NOW = [95]

FAST_API_CONTAINER = "fastapi-app"
def main():
    if len(sys.argv) != 1:
        print("Usage: python full-test-aws.py")
        sys.exit(1)

    #1. Iterate trough the databases
    for database in VALID_DATABASES:

        #2. Check if the bash script exists
        aws_script = f"./aws/run.sh"
        if not os.path.isfile(aws_script):
            print(f"[ERROR] Docker script {aws_script} not found.")
            sys.exit(1)

        test_script = "./scripts/locusttest.py"
        if not os.path.isfile(test_script):
            print(f"[ERROR] Test script {test_script} not found.")
            sys.exit(1)

        os.makedirs(f"output-aws/{database}", exist_ok=True)

        for mode, pct_get, pct_now, tt, users, rate in itertools.product(MODE, PCT_GET, PCT_NOW, TOTAL_TIME, USERS, RATE):
            print(f"[INFO] Running Docker setup: {aws_script}")
            subprocess.run([aws_script, database])

            try:
                print("[INFO] Waiting for the server to initialize...")
                time.sleep(10)

                locust_command = [
                        "locust",
                        "-f", test_script,
                        "--headless",
                        "-u", str(users),
                        "--run-time", f"{tt}m",
                        "--mode", mode,
                        "--pct-get", str(pct_get),
                        "--pct-get-now", str(pct_now),
                        "--db", database,
                        "--time", str(tt),
                        "--user-number", str(users),
                        "--rate", str(rate),
                        "--host", "http://13.219.246.81:8000"
                    ]

                print(f"[INFO] Running test with mode={mode}, tt={tt}, get={pct_get}, now={pct_now}, number of users={users}")

                subprocess.run(locust_command)

            finally:
                #Wait for do over
                time.sleep(10)

if __name__ == "__main__":
    main()
