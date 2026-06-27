import requests


def fetch_profile(api_base: str, user_id: str) -> dict:
    response = requests.get(f"{api_base}/users/{user_id}", timeout=10)
    response.raise_for_status()
    return response.json()
