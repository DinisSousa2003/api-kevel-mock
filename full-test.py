#1. Recieve as argument postgres, terminus or xtdb2

#2. Copy the file envs/<database-name>.env to .env

#3. Run the script in the scripts/docker-<database-name>.sh

#4. Run the application uvicorn main:app --reload

#5. Run the test in the scripts/test.py file python test.py diff 10000 80 80 100

import os
import shutil
import subprocess
import sys
import time

VALID_DATABASES = ["postgres", "terminus", "xtdb2"]

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

    print(f"[INFO] Running Docker setup: {docker_script}")
    subprocess.run(["bash", docker_script], check=True)

    time.sleep(15)

    #4. Run the application uvicorn main:app --reload
    print("[INFO] Starting FastAPI server with Uvicorn...")
    uvicorn_process = subprocess.Popen(["uvicorn", "main:app", "--reload"])

    try:
        # Give the server some time to start
        print("[INFO] Waiting for the server to initialize...")
        time.sleep(10)

        # Step 5: Run the test script
        test_script = "./scripts/test.py"
        if not os.path.isfile(test_script):
            print(f"[ERROR] Test script {test_script} not found.")
            uvicorn_process.terminate()
            sys.exit(1)

        print("[INFO] Running test script...")
        #MODE, NUM_OPS, PCT_GET, PCT_NOW, RATE
        subprocess.run(["python", test_script, "state", "100", "80", "50", "100"], check=True)

    finally:
        # Make sure the server stops after testing
        print("[INFO] Terminating Uvicorn server...")
        uvicorn_process.terminate()
        uvicorn_process.wait()

if __name__ == "__main__":
    main()
