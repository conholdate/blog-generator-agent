"""Quick health probe for the self-hosted Professionalize LLM endpoint.

Uses the same openai client the app uses, so it exercises the real path.
Run from this directory so `config` imports:  python check_llm_endpoint.py
Exit code 0 = healthy (3/3 completions came back), 1 = not usable yet.
"""
import sys
import time

from openai import OpenAI
from config import settings

BASE = settings.PROFESSIONALIZE_BASE_URL
MODEL = settings.PROFESSIONALIZE_LLM_MODEL

client = OpenAI(base_url=BASE, api_key=settings.PROFESSIONALIZE_API_KEY_2, timeout=45, max_retries=0)

print(f"endpoint: {BASE}  model: {MODEL}")

try:
    t = time.monotonic()
    n = len(client.models.list().data)
    print(f"  models.list()        -> {n} models in {time.monotonic() - t:.1f}s")
except Exception as e:
    print(f"  models.list()        -> FAIL: {type(e).__name__}: {e}")
    sys.exit(1)

ok = 0
for i in range(1, 4):
    try:
        t = time.monotonic()
        r = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": "Reply with just the word: pong"}],
            max_tokens=200,
            temperature=0,
        )
        text = r.choices[0].message.content
        print(f"  chat.completions {i}   -> OK in {time.monotonic() - t:.1f}s: {text!r}")
        if text:
            ok += 1
        else:
            print(f"  chat.completions {i}   -> WARN: empty content (reasoning-only response)")
    except Exception as e:
        print(f"  chat.completions {i}   -> FAIL in {time.monotonic() - t:.1f}s: {type(e).__name__}: {e}")
    time.sleep(1)

if ok == 3:
    print("HEALTHY - safe to re-dispatch the workflow")
    sys.exit(0)
print(f"NOT READY - {ok}/3 completions succeeded")
sys.exit(1)
