# APIs/chat_query.py

import requests


def chat_query(
        base_url: str,
        token: str,
        model: str,
        prompt: str,
        file_data: dict,
):
    """
    Send a chat completion request with an uploaded document.

    Returns:
        dict: Raw OpenAI-compatible response
    """

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    file_id = file_data["id"]

    payload = {
        "stream": False,
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": prompt,
            }
        ],
        "params": {},
        "files": [
            {
                "type": "file",
                "file": file_data,
                "id": file_id,
                "url": file_id,
                "name": file_data["filename"],
                "status": "uploaded",
                "size": file_data["meta"]["size"],
                "error": "",
                "itemId": file_id,
                "content_type": file_data["meta"]["content_type"],
            }
        ],
        "tool_servers": [],
        "features": {
            "voice": False,
            "image_generation": False,
            "code_interpreter": False,
            "web_search": False,
            "memory": True,
        },
        "background_tasks": {
            "title_generation": True,
            "tags_generation": True,
            "follow_up_generation": True,
        },
    }

    response = requests.post(
        f"{base_url.rstrip('/')}/api/chat/completions",
        headers=headers,
        json=payload,
    )

    print("=" * 80)
    print("STATUS :", response.status_code)
    print("BODY :")
    print(response.text)
    print("=" * 80)

    response.raise_for_status()

    return response.json()