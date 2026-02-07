from datetime import datetime
import json
import os
from zoneinfo import ZoneInfo
import requests
from companies.base_company import BaseCompany
from utils.entities_map import ContestantsEntity, MatchesEntity


class Company2App(BaseCompany):
    def __init__(self):
        super().__init__("company_2")
        pass

    def request_company_url(self) -> str:
        headers = {}
        resp_raw = requests.request(
            "GET", self.company_url, headers=headers, data=self.payload
        )
        resp_jn = resp_raw.json()
        return resp_jn

    def get_matches_matches(self, input_jn: dict) -> list[MatchesEntity]:

        matches = input_jn
        all_matches_ls = self._handle_matches(matches=matches)
        return all_matches_ls

    def _handle_matches(self, matches: list[dict]) -> list[dict]:
        all_matches_ls: list[MatchesEntity] = []

        for _match in matches:
            if "primaryMarket" not in _match.keys():
                continue
            selections = _match["primaryMarket"]["selections"]
            if len(selections) != 2:
                continue
            
            match_name = _match["name"]
            start_time = _match["startTime"]
            sportName = _match["className"]
            competitionName = _match["competitionName"]
            match_aest = datetime.fromtimestamp(start_time, tz=ZoneInfo("Australia/Sydney"))
            aest_dt_iso = match_aest.isoformat()

            contestant_0_short_name = selections[0]["name"]
            contestant_0_full_name = selections[0]["name"]
            contestant_0_odds = selections[0]["price"]["winPrice"]
            contestant_0_loc = selections[0]["resultType"]

            contestant_1_short_name = selections[1]["name"]
            contestant_1_full_name = selections[1]["name"]
            contestant_1_odds = selections[1]["price"]["winPrice"]
            contestant_1_loc = selections[1]["resultType"]
            odds_flag = False
            if self.min_odds < contestant_1_odds < self.high_odds:
                odds_flag = True
            if self.min_odds < contestant_0_odds < self.high_odds:
                odds_flag = True
            if odds_flag is False:
                continue

            match_contestants = [
                ContestantsEntity(
                    **{
                        "full_name": contestant_0_full_name,
                        "short_name": contestant_0_short_name,
                        "odds": contestant_0_odds,
                        "location": contestant_0_loc,
                    }
                ),
                ContestantsEntity(
                    **{
                        "full_name": contestant_1_full_name,
                        "short_name": contestant_1_short_name,
                        "odds": contestant_1_odds,
                        "location": contestant_1_loc,
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
                    "bet_option": None,
                }
            )
            all_matches_ls.append(matches_entity)
        return all_matches_ls
