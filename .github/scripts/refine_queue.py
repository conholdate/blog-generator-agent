"""Drain the revision queue on a dashboard-request PR (used by blog_refine workflow).

Why a queue lives in PR comments instead of relying on Actions run ordering:
GitHub's concurrency group keeps only ONE pending run per group, so if a
reviewer submits three revisions in a row the middle run is cancelled and its
instruction is silently lost. The dashboard therefore writes every instruction
as a hidden comment on the PR *before* dispatching, and whichever run is
currently active works through all unprocessed comments, oldest first. A
cancelled pending run loses nothing - its instruction is still on the PR.

Comment protocol (also parsed by the dashboard's lib/github.ts):
  queued : <!-- refine-queued id=UUID -->\n**🕒 Revision queued:**\n\n<instruction>
  result : <!-- refine-result: success|failure id=UUID -->\n<human-readable text>

Each item is one independent single-target pass (main.py --revise); a failure
is reported on its own id and the queue continues.
"""

import json
import os
import re
import subprocess
import sys

QUEUED_RE = re.compile(
    r"<!--\s*refine-queued\s+id=([0-9A-Za-z-]+)\s*-->\n\*\*🕒 Revision queued:\*\*\n\n(.*)\Z",
    re.DOTALL,
)
RESULT_RE = re.compile(r"<!--\s*refine-result:\s*(?:success|failure)\s+id=([0-9A-Za-z-]+)\s*-->")

MAX_ITEMS = 25  # safety cap on one drain

TARGET_REPO = os.environ["TARGET_REPO"]
BRANCH = os.environ["BRANCH"]
PR_NUMBER = os.environ["PR_NUMBER"]
DRAFT_PATH = os.environ["DRAFT_PATH"]
BRAND = os.environ["BRAND"]
PRODUCT = os.environ.get("REQUEST_PRODUCT", "")
PLATFORM = os.environ.get("REQUEST_PLATFORM", "")
# The dispatch's own instruction/id: only used as a fallback when the queued
# comment is missing (a dashboard build that predates the queue).
PAYLOAD_ID = os.environ.get("REQUEST_ID", "")
PAYLOAD_INSTRUCTION = os.environ.get("INSTRUCTION", "")

REPO_DIR = os.path.abspath("blog-repo")
ENGINE_DIR = os.path.abspath("agent_engine/blog_generator")
STATUS_FILE = os.path.join(ENGINE_DIR, "revise_status.json")


def run(cmd, cwd=None, check=False):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=check)


def fetch_comments():
    out = run(
        ["gh", "api", "--paginate", f"repos/{TARGET_REPO}/issues/{PR_NUMBER}/comments?per_page=100",
         "--jq", ".[] | @json"]
    )
    if out.returncode != 0:
        print(f"⚠️ Could not list PR comments: {out.stderr.strip()}")
        return None
    return [json.loads(line) for line in out.stdout.splitlines() if line.strip()]


def pending_items(comments):
    done = set()
    for c in comments:
        m = RESULT_RE.search(c.get("body") or "")
        if m:
            done.add(m.group(1))
    items = []
    for c in comments:  # comment ids ascend with creation time
        m = QUEUED_RE.match((c.get("body") or "").strip())
        if m and m.group(1) not in done:
            items.append((m.group(1), m.group(2).strip()))
    return items, done


def post_result(item_id, ok, instruction, message):
    state = "success" if ok else "failure"
    head = f"🔁 **Revised per:** {instruction}" if ok else f"❌ **Revision failed** for: {instruction}"
    body = f"<!-- refine-result: {state} id={item_id} -->\n{head}\n\n{message}"
    res = run(["gh", "pr", "comment", PR_NUMBER, "--repo", TARGET_REPO, "--body", body])
    if res.returncode != 0:
        print(f"⚠️ Could not post result comment: {res.stderr.strip()}")
    return res.returncode == 0


def apply_item(instruction):
    """One revision pass on the latest branch state. Returns (ok, message)."""
    # Start from what's really on the branch: earlier queue items were pushed,
    # so this one sees their changes (and any manual edits).
    run(["git", "fetch", "origin", BRANCH], cwd=REPO_DIR)
    reset = run(["git", "reset", "--hard", f"origin/{BRANCH}"], cwd=REPO_DIR)
    if reset.returncode != 0:
        return False, f"Could not sync the branch: {reset.stderr.strip()}"

    if os.path.exists(STATUS_FILE):
        os.remove(STATUS_FILE)

    cmd = [
        sys.executable, "main.py", "--author", "Muhammad Mustafa", "--brand", BRAND,
        "--revise", "--draft-path", DRAFT_PATH, "--instruction", instruction,
        "--product", PRODUCT, "--platform", PLATFORM,
    ]
    proc = subprocess.run(cmd, cwd=ENGINE_DIR)
    print(f"main.py --revise exited {proc.returncode}")

    try:
        with open(STATUS_FILE) as f:
            status = json.load(f)
    except (OSError, ValueError):
        return False, "revise_status.json not found — the revision step did not run to completion"

    if status.get("status") != "success":
        return False, status.get("message", "") or "Revision did not succeed."

    message = status.get("message", "")
    if run(["git", "diff", "--quiet"], cwd=REPO_DIR).returncode != 0:
        run(["git", "add", "-A"], cwd=REPO_DIR)
        commit = run(["git", "commit", "-m", f"Revise draft per request: {instruction}"], cwd=REPO_DIR)
        if commit.returncode != 0:
            return False, f"Commit failed: {commit.stderr.strip()}"
        push = run(["git", "push", "origin", BRANCH], cwd=REPO_DIR)
        if push.returncode != 0:
            return False, f"Push failed: {push.stderr.strip()}"
        print(f"✅ Pushed revision to {BRANCH}")
    else:
        print("ℹ️  No changes produced by the revision")
    return True, message


def main():
    run(["git", "config", "--global", "user.email", "action@github.com"])
    run(["git", "config", "--global", "user.name", "GitHub Action"])

    processed = set()
    results = []  # (ok, instruction)
    legacy_tried = False

    while len(processed) < MAX_ITEMS:
        comments = fetch_comments()
        if comments is None:
            break
        items, done = pending_items(comments)
        items = [it for it in items if it[0] not in processed]

        if not items and PAYLOAD_INSTRUCTION and not legacy_tried:
            legacy_tried = True
            item_id = PAYLOAD_ID or "legacy"
            if item_id not in done and item_id not in processed:
                queued_ids = {m.group(1) for m in (QUEUED_RE.match((c.get("body") or "").strip()) for c in comments) if m}
                if item_id not in queued_ids:
                    print("ℹ️  No queued comment for this dispatch - using its payload instruction")
                    items = [(item_id, PAYLOAD_INSTRUCTION)]

        if not items:
            break

        item_id, instruction = items[0]
        processed.add(item_id)
        print(f"=== Revision {item_id}: {instruction}")
        ok, message = apply_item(instruction)
        post_result(item_id, ok, instruction, message)
        results.append((ok, instruction))

    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a") as f:
            f.write("### 🔁 Revision queue report\n\n")
            if not results:
                f.write("Nothing to do — the queue was already drained by an earlier run.\n")
            else:
                f.write("| Status | Instruction |\n|---|---|\n")
                for ok, instruction in results:
                    f.write(f"| {'success' if ok else 'failure'} | {instruction.replace('|', '/')} |\n")
            f.write(f"\nPR: https://github.com/{TARGET_REPO}/pull/{PR_NUMBER}\n")

    if any(not ok for ok, _ in results):
        sys.exit(1)


if __name__ == "__main__":
    main()
