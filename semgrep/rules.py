# ai-generated: 100% - Semgrep positive and negative fixtures for Lab 5 Stretch 3
import os

# ruleid: svcdesk.unbounded-upstream-read
payload = response.read()

# ok: svcdesk.unbounded-upstream-read
payload = response.read(65536)

# ruleid: svcdesk.env-controlled-upstream-url
base_url = os.getenv("KB_INDEX_URL", "http://kb-index:8080")

# ok: svcdesk.env-controlled-upstream-url
feature_flag = os.getenv("FEATURE_FLAG", "false")
