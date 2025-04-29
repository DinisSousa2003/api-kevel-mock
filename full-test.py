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

VALID_DATABASES = ["postgres", "terminus", "xtdb2"]
MODE = ["diff", "state"]
TOTAL_TIME = [1]  # in minutes
PCT_GET = [30, 70]
PCT_NOW = [90, 100]
RATE = [50]

def main():
    if len(sys.argv) != 2:
        print("Usage: python full-test.py <postgres|terminus|xtdb2>")
        sys.exit(1)

    database = sys.argv[1].lower()
    
    #1. Recieve as argument postgres, terminus or xtdb2
    if database not in VALID_DATABASES:
        print(f"Error: Invalid database '{database}'. Choose one of: {', '.join(VALID_DATABASES)}")
        sys.exit(1)

    #2. Copy the file envs/<database-name>.env to .env
    src_env = f"envs/{database}.env"
    dst_env = ".env"
    try:
        shutil.copy(src_env, dst_env)
        print(f"[INFO] Copied {src_env} to {dst_env}")
    except FileNotFoundError:
        print(f"[ERROR] {src_env} not found.")
        sys.exit(1)

    #3. Run the script in the scripts/docker-<database-name>.sh
    docker_script = f"./scripts/docker-{database}.sh"
    if not os.path.isfile(docker_script):
        print(f"[ERROR] Docker script {docker_script} not found.")
        sys.exit(1)

    test_script = "./scripts/test.py"
    if not os.path.isfile(test_script):
        print(f"[ERROR] Test script {test_script} not found.")
        sys.exit(1)

    os.makedirs(f"output/{database}", exist_ok=True)

    for mode, tt, pct_get, pct_now, rate in itertools.product(MODE, TOTAL_TIME, PCT_GET, PCT_NOW, RATE):
        print(f"[INFO] Running Docker setup: {docker_script}")
        subprocess.run(["bash", docker_script], check=True)

        print("[INFO] Waiting for the database to initialize...")
        time.sleep(30)

        print("[INFO] Starting FastAPI server with Uvicorn...")
        uvicorn_process = subprocess.Popen(["uvicorn", "main:app", "--reload"])

        try:
            print("[INFO] Waiting for the server to initialize...")
            time.sleep(10)

            output_file = f"output/{database}/test_{mode}_{tt}_{pct_get}_{pct_now}_{rate}.txt"
            print(f"[INFO] Running test with mode={mode}, tt={tt}, get={pct_get}, now={pct_now}, rate={rate}")
            with open(output_file, "w") as outfile:
                subprocess.run(
                    ["python", test_script, mode, str(tt), str(pct_get), str(pct_now), str(rate)],
                    stdout=outfile,
                    stderr=subprocess.STDOUT,
                    check=True
                )
            print(f"[INFO] Output saved to {output_file}")

        finally:
            print("[INFO] Terminating Uvicorn server...")
            uvicorn_process.terminate()
            uvicorn_process.wait()

if __name__ == "__main__":
    main()
