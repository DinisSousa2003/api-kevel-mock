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

#VALID_DATABASES = ["postgres", xtdb2", "terminus"]
VALID_DATABASES = ["postgres", "xtdb2", "terminus"]
MODE = ["diff", "state"]
TOTAL_TIME = [60]  # in minutes
USERS = [1, 10]
RATE = [0.1, 1, 10]
PCT_GET = [30]
PCT_NOW = [95]

def main():
    if len(sys.argv) != 1:
        print("Usage: python full-test.py")
        sys.exit(1)

    #1. Iterate trough the databases
    for database in VALID_DATABASES:

        #2. Copy the file envs/<database-name>.env to .env
        src_env = f"envs/{database}.env"
        dst_env = ".env"
        try:
            shutil.copy(src_env, dst_env)
            print(f"[INFO] Copied {src_env} to {dst_env}")
        except FileNotFoundError:
            print(f"[ERROR] {src_env} not found.")
            sys.exit(1)

        #3. Check if the docker script exists
        docker_script = f"./scripts/docker-{database}.sh"
        if not os.path.isfile(docker_script):
            print(f"[ERROR] Docker script {docker_script} not found.")
            sys.exit(1)

        test_script = "./scripts/locusttest.py"
        if not os.path.isfile(test_script):
            print(f"[ERROR] Test script {test_script} not found.")
            sys.exit(1)

        os.makedirs(f"output/{database}", exist_ok=True)

        for mode, pct_get, pct_now, tt, users, rate in itertools.product(MODE, PCT_GET, PCT_NOW, TOTAL_TIME, USERS, RATE):
            print(f"[INFO] Running Docker setup: {docker_script}")
            subprocess.run(["bash", docker_script], check=True)

            print("[INFO] Waiting for the database to initialize...")
            time.sleep(30)

            print("[INFO] Ensuring nothing is running on port 8000...")

            # Try to find and kill any process using port 8000
            try:
                # macOS: use lsof; Linux: use fuser or lsof
                result = subprocess.run(
                    ["lsof", "-ti", ":8000"], capture_output=True, text=True, check=True
                )
                pids = result.stdout.strip().splitlines()

                for pid in pids:
                    print(f"[INFO] Killing process on port 8000: PID {pid}")
                    subprocess.run(["kill", "-9", pid])
            except subprocess.CalledProcessError:
                print("[INFO] No process found on port 8000.")

            print("[INFO] Starting FastAPI server with Uvicorn...")
            uvicorn_process = subprocess.Popen(["uvicorn", "main:app", "--reload"])

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
                        "--host", "http://127.0.0.1:8000"
                    ]

                print(f"[INFO] Running test with mode={mode}, tt={tt}, get={pct_get}, now={pct_now}, number of users={users}")

                subprocess.run(locust_command)

            finally:
                print("[INFO] Terminating Uvicorn server...")
                uvicorn_process.kill()
                uvicorn_process.wait()

if __name__ == "__main__":
    main()
