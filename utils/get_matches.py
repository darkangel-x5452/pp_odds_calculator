import json
import os
from zoneinfo import ZoneInfo

from datetime import datetime

import requests

class GetMatchesOdds():
    def __init__(self):
        self.match_result_options = [
            "Head To Head",
            "Result",
            "Winner",
            "Winner of Tie",
        ]
        self.ignore_options = [
            "Leading Point Scorer",
            "Total Points Odd/Even", "Home Team Points Odd/Even", "Away Team Points Odd/Even",
            ]
        
        self.high_odds = 2.5

        self.result_path = "published/results/matches_odds.json"

    def get_matches_comps(self, input_jn: dict):
        sports = input_jn['nextToGoMatches']['sports']

        all_matches_ls = []
        
        for _sport in sports:
            sport_name = _sport['name']
            competitions = _sport['competitions']
            for _competition in competitions:
                competition_name = _competition['name']
                if competition_name == 'Racing Offers':
                    continue
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

                    if not any(item in betOptionPriority for item in self.match_result_options):
                        if not all(item in self.ignore_options for item in betOptionPriority):
                            print(f"Expected 'Head To Head' in {match_name} betOptionPriority but got {json.dumps(betOptionPriority)}")
                    if "markets" not in _match.keys():
                        continue
                    markets = _match['markets']

                    for _market in markets:
                        betOption = _market['betOption']
                        if betOption not in self.match_result_options:
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
                                two_dollar_flag = True if return_win >= 2.0 and return_win <= self.high_odds else False
                        if two_dollar_flag is True:
                            start_time_aest = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                            # Convert to AEST
                            aest_dt = start_time_aest.astimezone(ZoneInfo("Australia/Sydney"))
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
        print(f"Total matches with two dollar odds: {len(all_matches_ls)}")
        self.save_file(all_matches_ls=all_matches_ls)

    def get_matches_matches(self, input_jn: dict):

        all_matches_ls = []
        matches = input_jn['matches']
        for _match in matches:
            inPlay = _match['inPlay']
            if inPlay is True:
                continue
            match_name = _match['name']
            start_time = _match['startTime']
            contestants = _match['contestants']
            competitionName = _match['competitionName']
            sportName = _match['sportName']
            competitors = _match['competitors'] if 'competitors' in _match else []

            markets = _match['_links']['markets']
            payload = {}
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "PostmanRuntime/7.51.0",
                "Accept": "*/*",
                "Accept-Encoding": "gzip, deflate, br",
            }
            resp_raw = requests.request("GET", markets, headers=headers, data=payload)

            markets_resp_jn = resp_raw.json()
            
            betOptionPriority = markets_resp_jn['betOptionPriority']
            if not any(item in betOptionPriority for item in self.match_result_options):
                if not all(item in self.ignore_options for item in betOptionPriority):
                    print(f"Expected 'Head To Head' in {match_name} betOptionPriority but got {json.dumps(betOptionPriority)}")
            if "markets" not in markets_resp_jn.keys():
                continue
            markets = markets_resp_jn['markets']

            for _market in markets:
                betOption = _market['betOption']
                if betOption not in self.match_result_options:
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
                        two_dollar_flag = True if return_win >= 2.0 and return_win <= self.high_odds else False
                if two_dollar_flag is True:
                    start_time_aest = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                    # Convert to AEST
                    aest_dt = start_time_aest.astimezone(ZoneInfo("Australia/Sydney"))
                    aest_dt_iso = aest_dt.isoformat()
                    
                    match_details = {
                        "start_time_aest": aest_dt_iso,
                        "sport_name": sportName,
                        "competition_name": competitionName,
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
        print(f"Total matches with two dollar odds: {len(all_matches_ls)}")
        self.save_file(all_matches_ls=all_matches_ls)

    def save_file(self, all_matches_ls: list[dict]):

        if os.path.exists(self.result_path) is False:
            with open(self.result_path, "w") as f:
                json.dump([], f, indent=4)

        with open(self.result_path, "r") as f:
            existing_matches: list[dict] = json.load(f)

        adding_matches_ls = existing_matches.copy()

        # remove outdated matches
        current_dt = datetime.now(tz=ZoneInfo("Australia/Sydney"))
        filtered_matches_ls = []
        for _existing_match in adding_matches_ls:
            match_start_time = datetime.fromisoformat(_existing_match["start_time_aest"])
            if match_start_time >= current_dt:
                filtered_matches_ls.append(_existing_match)
        adding_matches_ls = filtered_matches_ls

        # Add new matches to the list
        for _new_match in all_matches_ls:
            match_exists = False
            for _existing_match in adding_matches_ls:
                if _new_match["match_name"] == _existing_match["match_name"] \
                    and _new_match["start_time"] == _existing_match["start_time"] \
                    and _new_match["competition_name"] == _existing_match["competition_name"] \
                    and _new_match["sport_name"] == _existing_match["sport_name"]:
                    match_exists = True
                    break
            if match_exists is False:
                adding_matches_ls.append(_new_match)


        adding_matches_ls.sort(
            key=lambda x: datetime.fromisoformat(x["start_time_aest"]),
            reverse=False
        )
        with open(self.result_path, "w") as f:
            json.dump(adding_matches_ls, f, indent=4)