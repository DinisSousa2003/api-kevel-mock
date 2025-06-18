#1. Recieve as argument postgres, terminus or xtdb2

#2. Copy the file envs/<database-name>.env to .env

#3. Run the script in the scripts/docker-<database-name>.sh

#4. Run the application uvicorn main:app --reload

#5. Run the test in the scripts/test.py file python test.py diff 10000 80 80 100

import itertools
import os
import subprocess
import sys
import time

#VALID_DATABASES = ["postgres", "xtdb2", "terminus"]
VALID_DATABASES = ["postgres"]
MODE = ["diff"]
TOTAL_TIME = [120]  # in minutes
STEP_TIME = [30] # in minutes, time between collecting metrics
USERS = [10]
RATE = [10]
PCT_GET = [30]
PCT_NOW = [99]

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

        os.makedirs(f"output-aws/", exist_ok=True)

        #3. Run tests for all combinations of parameters
        print(f"[INFO] Running tests for database: {database}")
        for mode, pct_get, pct_now, tt, st, users, rate in itertools.product(MODE, PCT_GET, PCT_NOW, TOTAL_TIME, STEP_TIME, USERS, RATE):
            
            try:
                print(f"[INFO] Running aws script: {aws_script}")
                subprocess.run([aws_script, database, str(tt), str(st), mode, str(pct_get), str(pct_now), str(users), str(rate)], check=True)


            except subprocess.CalledProcessError as e:
                print(f"[ERROR] Docker setup failed: {e}")
                continue

            finally:
                #Wait for do over
                time.sleep(10)

    #4. Get the output folder from the locust and database machine
    print("[INFO] Fetching all output from Locust and Database machine...")
    try:
        subprocess.run(["./aws/fetch-all-output.sh"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Fetching full output failed: {e}")
        

if __name__ == "__main__":
    main()
