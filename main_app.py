import json
import os

import requests
from datetime import datetime, timezone, timedelta

from utils.get_matches import GetMatchesOdds, get_matches_comps, get_matches_matches


def run_app():
    print("App is running...")
    odds_api = os.environ["ODDS_API"]
    payload = {}
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "PostmanRuntime/7.51.0",
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br",
    }
    resp_raw = requests.request("GET", odds_api, headers=headers, data=payload)
    gmo = GetMatchesOdds()
    resp_jn = resp_raw.json()
    if "-info-service" in odds_api:
        gmo.get_matches_matches(input_jn=resp_jn)
    elif "recommendation-service" in odds_api:
        gmo.get_matches_comps(input_jn=resp_jn)
    else:
        print("Unknown ODDS_API endpoint.")
    print("App is stopped.")


if __name__ == "__main__":
    print("Starting the application...")
    run_app()
    print("Application has stopped.")