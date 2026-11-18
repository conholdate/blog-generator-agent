"""Apply one revision to a markdown file uploaded on the dashboard's
"Edit a blog post" page (used by blog_local_revise.yml).

Same editor as reviewing a draft PR (main.py --revise -> section-aware
classify_and_apply), but the file isn't on any branch: the dashboard stores
the post + instruction in Redis and dispatches this workflow; we read it,
revise a temp copy, and write the result back to the same key. Nothing is
committed anywhere.

Redis key  localedit:<request_id>  (JSON, 1-day TTL, written by the dashboard's
lib/local-edit.ts):
  in : {status: "queued", brand, instruction, input, ...}
  out: {status: "running" | "success" | "rejected" | "error", output?, message, ...}
"""

import json
import os
import subprocess
import sys

import requests

REQUEST_ID = os.environ["REQUEST_ID"]
KEY = f"localedit:{REQUEST_ID}"
TTL_SECONDS = 24 * 60 * 60
GENERATOR_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "agent_engine", "blog_generator")
DRAFT_PATH = os.path.abspath(os.path.join(os.environ.get("RUNNER_TEMP", "/tmp"), "local_post", "index.md"))

BASE_URL = os.environ["KV_REST_API_URL"].rstrip("/")
HEADERS = {"Authorization": f"Bearer {os.environ['KV_REST_API_TOKEN']}"}


def redis(*command):
    resp = requests.post(BASE_URL, headers=HEADERS, json=list(command), timeout=20)
    resp.raise_for_status()
    return resp.json().get("result")


def save(record: dict) -> None:
    redis("SET", KEY, json.dumps(record, ensure_ascii=False), "EX", str(TTL_SECONDS))


def main() -> int:
    raw = redis("GET", KEY)
    if not raw:
        print(f"❌ {KEY} not found (expired, or never stored)")
        return 1
    record = json.loads(raw)
    instruction = (record.get("instruction") or "").strip()
    content = record.get("input") or ""
    brand = record.get("brand") or "aspose.cloud"
    if not instruction or not content:
        save({**record, "status": "error", "message": "Missing post or instruction."})
        return 1

    save({**record, "status": "running"})

    # Files from Windows editors are often CRLF - the section editor refuses
    # those, so normalize (the dashboard gets LF back either way).
    content = content.replace("\r\n", "\n").replace("\r", "\n")
    os.makedirs(os.path.dirname(DRAFT_PATH), exist_ok=True)
    with open(DRAFT_PATH, "w", encoding="utf-8") as f:
        f.write(content)

    status_file = os.path.join(GENERATOR_DIR, "revise_status.json")
    if os.path.exists(status_file):
        os.remove(status_file)

    proc = subprocess.run(
        [
            sys.executable, "main.py",
            "--author", "Muhammad Mustafa",
            "--brand", brand,
            "--revise",
            "--draft-path", DRAFT_PATH,
            "--instruction", instruction,
        ],
        cwd=GENERATOR_DIR,
    )

    status = {"status": "error", "message": f"Revision exited with code {proc.returncode} and no status."}
    if os.path.exists(status_file):
        with open(status_file, encoding="utf-8") as f:
            status = json.load(f)

    result = {k: v for k, v in record.items() if k != "input"}
    result.update(status=status.get("status", "error"), message=status.get("message", ""))
    if result["status"] == "success":
        with open(DRAFT_PATH, encoding="utf-8") as f:
            result["output"] = f.read()
        for field in ("operation", "target", "lines_changed_outside_section", "SEO_Score"):
            if status.get(field) is not None:
                result[field] = status[field]
    else:
        result["input"] = record.get("input")  # keep it so the page still has the post
    save(result)
    print(f"Result: {result['status']} - {result['message']}")
    return 0 if result["status"] in ("success", "rejected") else 1


if __name__ == "__main__":
    sys.exit(main())
