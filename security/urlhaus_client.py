import os

import requests
from dotenv import load_dotenv

load_dotenv()

URLHAUS_API_URL = "https://urlhaus-api.abuse.ch/v1/url/"


def check_urlhaus(url: str) -> dict:
    """
    Check a URL against URLhaus.

    status:
      listed      - URL found in URLhaus
      not_listed  - URL not found
      unavailable - API/key/network problem
    """

    auth_key = os.getenv("URLHAUS_AUTH_KEY")

    if not auth_key:
        return {
            "source": "URLhaus",
            "status": "unavailable",
            "message": "URLhaus authentication key is missing.",
            "details": None,
        }

    try:
        response = requests.post(
            URLHAUS_API_URL,
            data={"url": url},
            headers={"Auth-Key": auth_key},
            timeout=10,
        )

        response.raise_for_status()
        data = response.json()

        query_status = data.get("query_status")

        if query_status == "ok":
            urls = data.get("urls") or [{}]
            entry = urls[0] if urls else {}

            return {
                "source": "URLhaus",
                "status": "listed",
                "message": "URL found in URLhaus.",
                "details": {
                    "url_status": entry.get("url_status"),
                    "threat": entry.get("threat"),
                    "tags": entry.get("tags") or [],
                    "reference": entry.get("urlhaus_reference"),
                },
            }

        if query_status == "no_results":
            return {
                "source": "URLhaus",
                "status": "not_listed",
                "message": "URL was not found in URLhaus.",
                "details": None,
            }

        return {
            "source": "URLhaus",
            "status": "unavailable",
            "message": f"URLhaus returned status: {query_status}",
            "details": None,
        }

    except (requests.RequestException, ValueError) as exc:
        return {
            "source": "URLhaus",
            "status": "unavailable",
            "message": f"URLhaus request failed: {type(exc).__name__}",
            "details": None,
        }