import os
import signal
import subprocess
import sys
import time

import httpx

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from app.core.db import test_db_connection
from app.core.llm import quick_model_call
from app.core.vector import test_qdrant_connection

HOST = "127.0.0.1"
PORT = int(os.getenv("TEST_PORT", "8001"))


def start_server() -> subprocess.Popen:
    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "app.main:app",
        "--host",
        HOST,
        "--port",
        str(PORT),
    ]
    return subprocess.Popen(
        cmd,
        cwd=ROOT_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def wait_for_health(timeout_seconds: int = 10) -> bool:
    url = f"http://{HOST}:{PORT}/health"
    deadline = time.time() + timeout_seconds
    with httpx.Client() as client:
        while time.time() < deadline:
            try:
                response = client.get(url, timeout=1.0)
                if response.status_code == 200:
                    return True
            except httpx.HTTPError:
                pass
            time.sleep(0.5)
    return False


def main() -> int:
    proc = start_server()
    try:
        api_ok = wait_for_health()
        db_ok = test_db_connection()
        qdrant_ok = test_qdrant_connection()
        llm_result = quick_model_call("ping")
        llm_ok = bool(llm_result.get("output"))

        print("API health:", "ok" if api_ok else "fail")
        print("PostgreSQL:", "ok" if db_ok else "fail")
        print("Qdrant:", "ok" if qdrant_ok else "fail")
        print("Groq wrapper:", "ok" if llm_ok else "fail")

        return 0 if all([api_ok, db_ok, qdrant_ok, llm_ok]) else 1
    finally:
        if proc.poll() is None:
            proc.send_signal(signal.SIGTERM)
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()


if __name__ == "__main__":
    raise SystemExit(main())
