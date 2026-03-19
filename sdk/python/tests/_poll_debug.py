"""Debug script: submit a fresh task with pipeline model and poll."""

import os
import time

from mineru._api import ApiClient

api = ApiClient(os.environ["MINERU_TOKEN"], "https://mineru.net/api/v4")

# Try pipeline model instead of vlm
body = api.post("/extract/task", {
    "url": "https://cdn-mineru.openxlab.org.cn/demo/example.pdf",
    "model_version": "pipeline",
})
task_id = body["data"]["task_id"]
print(f"task_id: {task_id}")

for i in range(30):
    body = api.get(f"/extract/task/{task_id}")
    data = body["data"]
    state = data.get("state")
    progress = data.get("extract_progress")
    zip_url = data.get("full_zip_url", "")
    print(f"[{i}] state={state} progress={progress} zip={zip_url[:60] if zip_url else ''}")
    if state in ("done", "failed"):
        if state == "done":
            print(f"Full zip URL: {zip_url}")
        break
    time.sleep(10)
