# api/upload_doc.py

from pathlib import Path
import mimetypes
import requests


def upload_doc(base_url: str, token: str, file_path: str, process: bool = True):
    """
    Upload a document to OpenWebUI.

    Returns:
        dict: uploaded file metadata
    """

    file = Path(file_path)

    if not file.exists():
        raise FileNotFoundError(file)

    content_type = (
            mimetypes.guess_type(file.name)[0]
            or "application/octet-stream"
    )

    with open(file, "rb") as f:
        response = requests.post(
            f"{base_url.rstrip('/')}/api/v1/files/",
            params={"process": str(process).lower()},
            headers={
                "Authorization": f"Bearer {token}",
            },
            files={
                "file": (
                    file.name,
                    f,
                    content_type,
                )
            },
        )

    response.raise_for_status()

    return response.json()