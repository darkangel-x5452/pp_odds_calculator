from datetime import datetime
import json
import os
from zoneinfo import ZoneInfo
import requests
from companies.base_company import BaseCompany
from utils.entities_map import ContestantsEntity, MatchesEntity
import http.client
import gzip


class Company3App(BaseCompany):
    def __init__(self):
        super().__init__("company_3")
        pass

    def request_company_url(self) -> str:
        
        conn = http.client.HTTPSConnection(self.company_url)
        payload = ''
        conn.request("GET", "/fixtures/sports/nexttoplay?pageSize=100&channel=website", payload, self.headers)
        res = conn.getresponse()
        data = res.read()
        decompressed = gzip.decompress(data)
        resp_jn = json.loads(decompressed.decode())
        return resp_jn

    def get_matches_matches(self, input_jn: dict) -> list[MatchesEntity]:

        matches = input_jn
        all_matches_ls = self._handle_matches(matches=matches)
        return all_matches_ls

    def _handle_matches(self, matches: list[dict]) -> list[dict]:
        all_matches_ls: list[MatchesEntity] = []

        for _match in matches["matches"]:
            if "draw" in _match.keys():
                continue
            competitionName = None
            match_name = None
            sportName = _match["sportType"]
            start_time = _match["startTime"]

            home_team = _match["homeTeam"]
            contestant_0_full_name = home_team["title"]
            contestant_0_short_name = home_team["title"]
            if "win" not in home_team.keys():
                continue
            contestant_0_odds = home_team['win']["price"]
            contestant_0_loc = "home"

            away_team = _match["awayTeam"]
            contestant_1_full_name = away_team["title"]
            contestant_1_short_name = away_team["title"]
            contestant_1_odds = away_team['win']["price"]
            contestant_1_loc = "away"

            utc_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))

            # Convert to Australia/Sydney (handles AEST/AEDT)
            aest_dt = utc_dt.astimezone(ZoneInfo("Australia/Sydney"))

            # ISO string
            aest_dt_iso = aest_dt.isoformat()

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
