"""
Single entry point: sets up the database, starts the background worker and
the API server, runs the automated test suite once, then polls the API and
prints the JSON response to the terminal. Run with: python main.py
(after activating your venv). Press Ctrl+C to stop everything cleanly.
"""

import json
import subprocess
import sys
import time

import requests

API_URL = "http://127.0.0.1:8000"
POLL_EVERY_SECONDS = 15


def run_step(description, command):
    print(f"[setup] {description} ...")
    result = subprocess.run(command)
    if result.returncode != 0:
        print(f"[error] '{description}' failed - fix this before continuing.")
        sys.exit(1)


def wait_for_api(timeout_seconds=30):
    print("[setup] waiting for the API to come online ...")
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        try:
            resp = requests.get(f"{API_URL}/health", timeout=2)
            if resp.status_code == 200:
                print("[setup] API is up.")
                return True
        except requests.RequestException:
            pass
        time.sleep(1)
    return False


def run_tests():
    print("\n[info] running automated test suite ...\n")
    result = subprocess.run([sys.executable, "-m", "pytest", "-v"])
    if result.returncode == 0:
        print("\n[info] all tests passed.\n")
    else:
        print("\n[warning] some tests failed - see output above.\n")


def main():
    run_step("creating database tables", [sys.executable, "-m", "db.init_db"])

    worker_process = subprocess.Popen([sys.executable, "-m", "worker.background_worker"])
    api_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "api.main:app", "--host", "127.0.0.1", "--port", "8000"]
    )

    try:
        if not wait_for_api():
            print("[error] API did not start in time.")
            return

        print("[info] worker and API are both running.")

        run_tests()
        print(f"[info] polling {API_URL}/v1/energy/commodity/price every {POLL_EVERY_SECONDS}s.")
        print("[info] press Ctrl+C to stop.\n")

        while True:
            try:
                resp = requests.get(
                    f"{API_URL}/v1/energy/commodity/price",
                    params={"commodity": "WTI"},
                    timeout=5,
                )
                print(f"--- {time.strftime('%H:%M:%S')} --- status {resp.status_code} ---")
                print(json.dumps(resp.json(), indent=2))
                print()
            except requests.RequestException as e:
                print(f"[warning] could not reach API: {e}")

            time.sleep(POLL_EVERY_SECONDS)

    except KeyboardInterrupt:
        print("\n[info] stopping worker and API ...")

    finally:
        worker_process.terminate()
        api_process.terminate()
        worker_process.wait()
        api_process.wait()
        print("[info] stopped.")


if __name__ == "__main__":
    main()