import json
import os

import requests
from datetime import datetime, timezone, timedelta


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

    resp_jn = resp_raw.json()

    sports = resp_jn['nextToGoMatches']['sports']

    all_matches_ls = []

    for _sport in sports:
        sport_name = _sport['name']
        competitions = _sport['competitions']
        for _competition in competitions:
            competition_name = _competition['name']
            matches = _competition['matches']
            for _match in matches:
                inPlay = _match['inPlay']
                if inPlay is True:
                    continue
                match_name = _match['name']
                start_time = _match['startTime']
                contestants = _match['contestants']
                competitors = _match['competitors'] if 'competitors' in _match else []
                betOptionPriority = _match['betOptionPriority']

                match_result_options = [
                    "Head To Head",
                    "Result",
                    "Winner",
                ]
                if len([_item in betOptionPriority for _item in match_result_options]) == 0:
                    print(f"Expected 'Head To Head' in {match_name} betOptionPriority but got {json.dumps(betOptionPriority)}")

                markets = _match['markets']

                for _market in markets:
                    betOption = _market['betOption']
                    if betOption != "Head To Head":
                        continue
                    bettingStatus = _market['bettingStatus']
                    propositions = _market['propositions']
                    propositions_len = len(propositions)
                    if propositions_len != 2:
                        continue
                    two_dollar_flag = False
                    for _proposition in propositions:
                        return_win = _proposition['returnWin']
                        if two_dollar_flag is False:
                            two_dollar_flag = True if return_win >= 2.0 and return_win <= 2.3 else False
                    if two_dollar_flag is True:
                        start_time_aest = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                        # Convert to AEST
                        aest = timezone(timedelta(hours=10))
                        aest_dt = start_time_aest.astimezone(aest)
                        aest_dt_iso = aest_dt.isoformat()
                        
                        match_details = {
                            "start_time_aest": aest_dt_iso,
                            "sport_name": sport_name,
                            "competition_name": competition_name,
                            "match_name": match_name,
                            "contestants": contestants,
                            "propositions": propositions,
                            "competitors": competitors,
                            "betOption": betOption,
                            "bettingStatus": bettingStatus,
                            "start_time": start_time,
                            "two_dollar_flag": two_dollar_flag,
                        }
                        all_matches_ls.append(match_details)
    all_matches_ls.sort(
        key=lambda x: datetime.fromisoformat(x["start_time_aest"])
    )
    with open(f"data/results/matches_with_two_dollar_odds_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", "w") as f:
        json.dump(all_matches_ls, f, indent=4)
    print("App is stopped.")


if __name__ == "__main__":
    print("Starting the application...")
    run_app()
    print("Application has stopped.")