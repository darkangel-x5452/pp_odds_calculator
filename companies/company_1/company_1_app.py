from datetime import datetime
import json
import os
from zoneinfo import ZoneInfo
import requests
from companies.base_company import BaseCompany
from utils.entities_map import ContestantsEntity, MatchesEntity


class Company1App(BaseCompany):
    def __init__(self):
        super().__init__("company_1")
        self.match_result_options = [
            "Head To Head",
            "Result",
            "Winner",
            "Winner of Tie",
        ]
        self.ignore_options = [
            "Leading Point Scorer",
            "Total Points Odd/Even",
            "Home Team Points Odd/Even",
            "Away Team Points Odd/Even",
        ]


    def request_company_url(self) -> str:
        resp_raw = requests.request(
            "GET", self.company_url, headers=self.headers, data=self.payload
        )
        resp_jn = resp_raw.json()
        return resp_jn

    def get_matches_matches(self, input_jn: dict) -> list[MatchesEntity]:

        matches = input_jn["matches"]
        all_matches_ls = self._handle_matches(matches=matches)
        return all_matches_ls

    def _clean_propositions(self, propositions: list[dict]) -> list[dict]:
        cleaned_propositions = []
        keep_keys = [
            "name",
            "returnWin",
            "returnPlace",
        ]
        for _proposition in propositions:
            cleaned_proposition = {}
            for _key in keep_keys:
                if _key in _proposition.keys():
                    cleaned_proposition.update({_key: _proposition[_key]})
            cleaned_propositions.append(cleaned_proposition)
        return cleaned_propositions

    def _handle_matches(self, matches: list[dict]) -> list[MatchesEntity]:
        all_matches_ls: list[MatchesEntity] = []
        for _match in matches:
            inPlay = _match["inPlay"]
            if inPlay is True:
                continue
            match_name = _match["name"]
            start_time = _match["startTime"]
            contestants = _match["contestants"]
            cleaned_contestants: list[dict] = []
            for _contestant in contestants:
                _contestant.pop("image", None)  # None if key not found
                _contestant.pop("isHome", None)  # None if key not found
                _contestant["short_name"] = _contestant["name"]  # None if key not found
                _contestant.pop("name", None)  # None if key not found
                cleaned_contestants.append(_contestant)

            competitionName = _match["competitionName"]
            sportName = _match["sportName"]
            # competitors = _match['competitors'] if 'competitors' in _match else []

            markets = _match["_links"]["markets"]
            payload = {}
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "PostmanRuntime/7.51.0",
                "Accept": "*/*",
                "Accept-Encoding": "gzip, deflate, br",
            }
            resp_raw = requests.request("GET", markets, headers=headers, data=payload)

            markets_resp_jn = resp_raw.json()

            betOptionPriority = markets_resp_jn["betOptionPriority"]
            if not any(item in betOptionPriority for item in self.match_result_options):
                if not all(item in self.ignore_options for item in betOptionPriority):
                    print(
                        f"Expected 'Head To Head' in {match_name} betOptionPriority but got {json.dumps(betOptionPriority)}"
                    )
            if "markets" not in markets_resp_jn.keys():
                continue
            markets = markets_resp_jn["markets"]

            for _market in markets:
                betOption = _market["betOption"]
                if betOption not in self.match_result_options:
                    continue
                # bettingStatus = _market['bettingStatus']
                propositions = _market["propositions"]
                propositions_len = len(propositions)
                if propositions_len != 2:
                    continue
                clean_propositions = self._clean_propositions(propositions=propositions)
                two_dollar_flag = False
                for _proposition in clean_propositions:
                    return_win = _proposition["returnWin"]
                    if two_dollar_flag is False:
                        two_dollar_flag = (
                            True
                            if return_win >= self.min_odds
                            and return_win <= self.high_odds
                            else False
                        )
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
                if two_dollar_flag is True:
                    start_time_aest = datetime.fromisoformat(
                        start_time.replace("Z", "+00:00")
                    )
                    # Convert to AEST
                    aest_dt = start_time_aest.astimezone(ZoneInfo("Australia/Sydney"))
                    aest_dt_iso = aest_dt.isoformat()
                    match_contestants = [
                        ContestantsEntity(
                            **{
                                "full_name": cleaned_contestants[0]["full_name"],
                                "short_name": cleaned_contestants[0]["short_name"],
                                "odds": clean_propositions[0]["returnWin"],
                                "location": cleaned_contestants[0]["position"],
                            }
                        ),
                        ContestantsEntity(
                            **{
                                "full_name": cleaned_contestants[1]["full_name"],
                                "short_name": cleaned_contestants[1]["short_name"],
                                "odds": clean_propositions[1]["returnWin"],
                                "location": cleaned_contestants[1]["position"],
                            }
                        ),
                    ]
                    matches_entity = MatchesEntity(
                        **{
                            "contestants": match_contestants,
                            "sport": sportName,
                            "competition": competitionName,
                            "start_time_aest": aest_dt_iso,
                            "match_name": match_name,
                            "bet_option": betOption,
                        }
                    )
                    all_matches_ls.append(matches_entity)
        return all_matches_ls
