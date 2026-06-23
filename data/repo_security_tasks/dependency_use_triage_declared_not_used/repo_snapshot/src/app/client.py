from urllib.request import urlopen


def fetch_profile(api_base: str, user_id: str) -> bytes:
    with urlopen(f"{api_base}/users/{user_id}", timeout=10) as response:
        return response.read()
