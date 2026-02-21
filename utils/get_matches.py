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
            "Gold Medal",
        ]
        self.ignore_options = [
            "Leading Point Scorer",
            "Total Points Odd/Even", "Home Team Points Odd/Even", "Away Team Points Odd/Even",
            ]
        
        self.high_odds = 2.5
        self.min_odds = 1.95

        self.result_path = "published/results/matches_odds.json"
        self.historical_path = "data/results/matches_odds_historical.json"

    def get_matches_comps(self, input_jn: dict):
        sports = input_jn['nextToGoMatches']['sports']

        all_matches_ls = []
        
        for _sport in sports:
            competitions = _sport['competitions']
            for _competition in competitions:
                competition_name = _competition['name']
                if competition_name == 'Racing Offers':
                    continue
                matches = _competition['matches']
                all_matches_ls = self._handle_matches(matches=matches)
        print(f"Total matches with two dollar odds: {len(all_matches_ls)}")
        self.save_file(all_matches_ls=all_matches_ls)

    def get_matches_matches(self, input_jn: dict):

        matches = input_jn['matches']
        all_matches_ls = self._handle_matches(matches=matches)
        print(f"Total matches with two dollar odds: {len(all_matches_ls)}")
        self.save_file(all_matches_ls=all_matches_ls)

    def save_file(self, all_matches_ls: list[dict]):

        if os.path.exists(self.result_path) is False:
            with open(self.result_path, "w") as f:
                json.dump([], f, indent=4)

        if os.path.exists(self.historical_path) is False:
            with open(self.historical_path, "w") as f:
                json.dump([], f, indent=4)

        with open(self.result_path, "r") as f:
            existing_matches: list[dict] = json.load(f)
        
        with open(self.historical_path, "r") as f:            
            historical_matches: list[dict] = json.load(f)

        adding_matches_ls = existing_matches.copy()

        # remove outdated matches
        current_dt = datetime.now(tz=ZoneInfo("Australia/Sydney"))
        filtered_matches_ls = []
        for _existing_match in adding_matches_ls:
            match_start_time = datetime.fromisoformat(_existing_match["start_time_aest"])
            if match_start_time >= current_dt:
                filtered_matches_ls.append(_existing_match)
            else:
                historical_matches.append(_existing_match)
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

        historical_matches.sort(
            key=lambda x: datetime.fromisoformat(x["start_time_aest"]),
            reverse=False
        )
        with open(self.historical_path, "w") as f:
            json.dump(historical_matches, f, indent=4)

    def _clean_propositions(self, propositions: list[dict]) -> list[dict]:
        cleaned_propositions = []
        keep_keys = [
            "name",
            "returnWin",
        ]
        for _proposition in propositions:
            cleaned_proposition = {}
            for _key in keep_keys:
                if _key in _proposition.keys():
                    cleaned_proposition.update({_key: _proposition[_key]})
            cleaned_propositions.append(cleaned_proposition)
        return cleaned_propositions

    def _handle_matches(self, matches: list[dict]) -> list[dict]:
        all_matches_ls: list[dict] = []
        for _match in matches:
            inPlay = _match['inPlay']
            if inPlay is True:
                continue
            match_name = _match['name']
            start_time = _match['startTime']
            contestants = _match['contestants']
            cleaned_contestants: list[dict] = []
            for _contestant in contestants:
                _contestant.pop("image", None)  # None if key not found
                _contestant.pop("isHome", None)  # None if key not found
                _contestant["short_name"] = _contestant["name"]  # None if key not found
                _contestant.pop("name", None)  # None if key not found
                cleaned_contestants.append(_contestant)

            competitionName = _match['competitionName']
            tournamentName = _match['tournamentName'] if "tournamentName" in _match else None
            sportName = _match['sportName']
            # competitors = _match['competitors'] if 'competitors' in _match else []

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
                # bettingStatus = _market['bettingStatus']
                propositions = _market['propositions']
                propositions_len = len(propositions)
                if propositions_len != 2:
                    continue
                clean_propositions = self._clean_propositions(propositions=propositions)
                two_dollar_flag = False
                for _proposition in clean_propositions:
                    return_win = _proposition['returnWin']
                    if two_dollar_flag is False:
                        two_dollar_flag = True if return_win >= self.min_odds and return_win <= self.high_odds else False
                full_name_0 = clean_propositions[0]["name"]
                full_name_1 = clean_propositions[1]["name"]
                if len(cleaned_contestants) == 0:
                    cleaned_contestants = [{}, {}]
                    cleaned_contestants[0]["full_name"] = full_name_0
                    cleaned_contestants[1]["full_name"] = full_name_1
                else:
                    cleaned_contestants[0]["full_name"] = full_name_0
                    cleaned_contestants[1]["full_name"] = full_name_1

                
                key = "full_name"
                cleaned_contestants_new: list[dict] = []
                for _clean_contentant in cleaned_contestants:
                    if key in _clean_contentant:
                        new_copy = _clean_contentant.copy()
                        value = new_copy.pop(key)
                        cleaned_contestants_new.append({key: value, **new_copy})
                cleaned_contestants = cleaned_contestants_new.copy()
                proposition_names = [f"{p['name']}, ({p['returnWin']})" for p in clean_propositions]
                contestant_full_names = " VERSES ".join(proposition_names)
                if two_dollar_flag is True:
                    start_time_aest = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                    # Convert to AEST
                    aest_dt = start_time_aest.astimezone(ZoneInfo("Australia/Sydney"))
                    aest_dt_iso = aest_dt.isoformat()

                    match_details = {
                        "contestant_names": contestant_full_names,
                        "start_time_aest": aest_dt_iso,
                        "sport_name": sportName,
                        "competition_name": competitionName,
                        "tournamentName": tournamentName,
                        "contestants": cleaned_contestants,
                        "propositions": clean_propositions,
                        "match_name": match_name,
                        # "competitors": competitors,
                        "betOption": betOption,
                        # "bettingStatus": bettingStatus,
                        "start_time": start_time,
                        # "two_dollar_flag": two_dollar_flag,
                    }

                    if tournamentName is None:
                        match_details.pop("tournamentName")

                    all_matches_ls.append(match_details.copy())
        return all_matches_ls