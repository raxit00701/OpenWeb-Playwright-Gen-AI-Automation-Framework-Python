# APIs/wait_for_processing.py

import json
import requests


def wait_for_processing(base_url: str, token: str, file_id: str):

    response = requests.get(
        f"{base_url.rstrip('/')}/api/v1/files/{file_id}/process/status",
        params={"stream": "true"},
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "text/event-stream",
        },
        stream=True,
    )

    response.raise_for_status()

    for line in response.iter_lines(decode_unicode=True):

        if not line:
            continue

        if not line.startswith("data:"):
            continue

        payload = json.loads(line[5:].strip())

        print(payload)

        if payload["status"] == "completed":
            return True

        if payload["status"] == "failed":
            raise Exception("Document processing failed")