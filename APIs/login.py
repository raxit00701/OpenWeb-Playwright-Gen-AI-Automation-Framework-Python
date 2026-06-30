import os
import requests
from dotenv import load_dotenv

load_dotenv()


def login(base_url: str):
    response = requests.post(
        f"{base_url.rstrip('/')}/api/v1/auths/signin",
        json={
            "email": os.getenv("TEST_USER_EMAIL"),
            "password": os.getenv("TEST_USER_PASSWORD")
        }
    )

    response.raise_for_status()

    return response.json()["token"]