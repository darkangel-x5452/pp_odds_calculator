import json
import os
from zoneinfo import ZoneInfo

from datetime import datetime

import pandas as pd
import requests

from analysis.result_analysis.utils.variables_names import SchemaName


class GetMatchesOdds:
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
            "Total Points Odd/Even",
            "Home Team Points Odd/Even",
            "Away Team Points Odd/Even",
        ]

        self.doubles_only_sports = [
            "tennis",
            "badminton",
        ]

        self.ignore_sports = [
            # "cricket",  # Too long and can be cancelled for weather
            # "golf",  # Too long and can be cancelled for weather
            # "snooker",  # Too long
            # "baseball",  # Too long and can be cancelled for weather
            # "darts",  # Too long
        ]
        self.ignore_competitions = [
            # terrible percentage results, not worth attempting
            "NHL",
            "Challenger",
            "ITF Womens",
            "ITF Mens",
            "China CBA",
            "WTA 125 Tour",
            "Mexico CIBACOPA",
            "Argentina Liga A",
            # These ones so low, best against ai  wins well.
            "Triple A Minor League",  # for low and high odds
            "Turkey TBL",  # for low and high odds
            "China CBA",  # for high odds
            "South Korea KBL",  # for high odds
            "Counter Strike 2",  # for low odds
        ]

        self.high_odds = 3.5
        self.min_odds = 1.5

        self.odds_analysis_fp = "data/results/win_rate_sport_genre_competition_name.csv"

        self.lower_odds_result_path = "published/results/matches_odds.json"
        self.lower_odds_historical_path = "data/results/matches_odds_historical.json"
        self.fifty_odds_result_path = "published/results/matches_odds_50.json"
        self.fifty_odds_historical_path = "data/results/matches_odds_50_historical.json"

    def get_matches_comps(self, input_jn: dict):
        sports = input_jn["nextToGoMatches"]["sports"]

        all_matches_ls = []

        for _sport in sports:
            competitions = _sport["competitions"]
            for _competition in competitions:
                competition_name = _competition["name"]
                if competition_name == "Racing Offers":
                    continue
                matches = _competition["matches"]
                all_matches_ls = self._handle_matches(matches=matches)
        print(f"Total matches with two dollar odds: {len(all_matches_ls)}")
        self.save_file(all_matches_ls=all_matches_ls)

    def get_matches_matches(self, input_jn: dict):

        matches = input_jn["matches"]
        all_matches_ls = self._handle_matches(matches=matches)
        print(
            f"Total matches with two dollar odds: {len(all_matches_ls['lower_odds'])}"
        )
        print(
            f"Total matches with fifty dollar odds: {len(all_matches_ls['fifty_odds'])}"
        )
        self.save_file(all_matches_ls=all_matches_ls)

    def _validate_data_to_files(
        self,
        final_matches_ls: list[dict],
        current_matches_fp: str,
        historical_matches_fp: str,
    ):
        if os.path.exists(current_matches_fp) is False:
            with open(current_matches_fp, "w") as f:
                json.dump([], f, indent=4)

        if os.path.exists(historical_matches_fp) is False:
            with open(historical_matches_fp, "w") as f:
                json.dump([], f, indent=4)

        with open(current_matches_fp, "r") as f:
            existing_matches: list[dict] = json.load(f)

        with open(historical_matches_fp, "r") as f:
            historical_matches: list[dict] = json.load(f)

        existing_matches_ls = existing_matches.copy()

        # final_current_ls = []
        revised_cln_match_ls = []
        # Update existing matches with new datetime if exists
        # Add new matches to the list
        for _existing_match in existing_matches_ls:
            match_exists = False
            for _new_match in final_matches_ls:
                if (
                    _new_match["match_name"] == _existing_match["match_name"]
                    # and _new_match["start_time"] == _existing_match["start_time"]
                    and _new_match["competition_name"]
                    == _existing_match["competition_name"]
                    and _new_match["sport_name"] == _existing_match["sport_name"]
                ):
                    match_exists = True
                    if (
                        _existing_match["start_time_aest"]
                        != _new_match["start_time_aest"]
                    ):
                        if "start_time_aest_old" not in _existing_match.keys():
                            _new_match.update(
                                {
                                    "start_time_aest_old": _existing_match[
                                        "start_time_aest"
                                    ]
                                }
                            )
                    break
            if match_exists is False:
                revised_cln_match_ls.append(_existing_match)
        revised_cln_match_ls.extend(final_matches_ls)

        # remove outdated matches
        current_dt = datetime.now(tz=ZoneInfo("Australia/Sydney"))
        filtered_matches_ls = []
        for _existing_match in revised_cln_match_ls:
            match_start_time = datetime.fromisoformat(
                _existing_match["start_time_aest"]
            )
            if match_start_time >= current_dt:
                filtered_matches_ls.append(_existing_match)
            else:
                historical_matches.append(_existing_match)
        existing_matches_ls_new = filtered_matches_ls

        repeated_dicts = [
            _dict
            for _dict in existing_matches_ls_new
            if "start_time_aest_old" in _dict.keys()
        ]
        new_dicts = [
            _dict
            for _dict in existing_matches_ls_new
            if "start_time_aest_old" not in _dict.keys()
        ]

        repeated_dicts.sort(
            key=lambda x: datetime.fromisoformat(x["start_time_aest"]), reverse=False
        )
        new_dicts.sort(
            key=lambda x: datetime.fromisoformat(x["start_time_aest"]), reverse=False
        )
        repeated_dicts.extend(new_dicts)

        final_current_matches = repeated_dicts.copy()
        # existing_matches_ls_new.sort(
        #     key=lambda x: datetime.fromisoformat(x["start_time_aest"]), reverse=False
        # )
        with open(current_matches_fp, "w") as f:
            json.dump(final_current_matches, f, indent=4)

        historical_matches.sort(
            key=lambda x: datetime.fromisoformat(x["start_time_aest"]), reverse=False
        )
        with open(historical_matches_fp, "w") as f:
            json.dump(historical_matches, f, indent=4)

    def save_file(self, all_matches_ls: dict[str, list[dict]]):
        lower_odds_matches = all_matches_ls["lower_odds"]
        # fifty_odds_matches = all_matches_ls["fifty_odds"]

        self._validate_data_to_files(
            final_matches_ls=lower_odds_matches,
            current_matches_fp=self.lower_odds_result_path,
            historical_matches_fp=self.lower_odds_historical_path,
        )
        # self._validate_data_to_files(
        #     final_matches_ls=fifty_odds_matches,
        #     current_matches_fp=self.fifty_odds_result_path,
        #     historical_matches_fp=self.fifty_odds_historical_path,
        # )

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

    def _get_lower_odds_flag(self, clean_propositions) -> bool:
        two_lower_odds_flag = True
        for _proposition in clean_propositions:
            return_win = _proposition["returnWin"]
            if two_lower_odds_flag is True:
                two_lower_odds_flag = (
                    False
                    if return_win < self.min_odds  # and return_win <= self.high_odds
                    else True
                )
        return two_lower_odds_flag

    def _get_fifty_odds_flag(self, clean_propositions) -> bool:
        not_fifty_flag = False
        for _proposition in clean_propositions:
            return_win = _proposition["returnWin"]
            if not_fifty_flag is False:
                not_fifty_flag = True if return_win >= self.min_odds else False
        return not not_fifty_flag

    def _get_comp_statistics(
        self,
        stats_data: pd.DataFrame,
        comp_name: str,
        sport_name: str,
        tournament_name: str,
    ) -> str:

        comp_stat_data = stats_data[
            stats_data[SchemaName.ColNames.competition_name_col].isin(
                [comp_name, tournament_name]
            )
            & stats_data[SchemaName.ColNames.sport_name_col].isin(
                [sport_name, comp_name]
            )
        ]
        cols = [
            SchemaName.ColNames.home_percentage_col,
            SchemaName.ColNames.won_odds_low_percentage_col,
            SchemaName.ColNames.total_odds_low_col,
            SchemaName.ColNames.won_odds_high_percentage_col,
            SchemaName.ColNames.total_odds_high_col,
        ]
        rename_cols = {
            SchemaName.ColNames.home_percentage_col: "home_perc",
            SchemaName.ColNames.won_odds_low_percentage_col: "low_perc_won",
            SchemaName.ColNames.total_odds_low_col: "low_total",
            SchemaName.ColNames.won_odds_high_percentage_col: "high_perc_won",
            SchemaName.ColNames.total_odds_high_col: "high_total",
        }
        if len(comp_stat_data) > 1:
            raise ValueError(
                f"Expected one row of comp stats data for comp '{comp_name}' and sport '{sport_name}' but got {len(comp_stat_data)} rows"
            )
        if len(comp_stat_data) == 0:
            result = None
        else:
            row = comp_stat_data.iloc[0]
            result = ", ".join(f"{rename_cols.get(col, col)}={row[col]}" for col in cols) if row is not None else ""
        return result

    def _handle_matches(self, matches: list[dict]) -> dict[str, list[dict]]:
        all_matches_ls: dict[str, list[dict]] = {
            "lower_odds": [],
            "fifty_odds": [],
        }

        odds_analysis_pd = pd.read_csv(self.odds_analysis_fp)
        for _match in matches:
            inPlay = _match["inPlay"]
            if inPlay is True:
                continue
            match_name = _match["name"]
            start_time = _match["startTime"]
            contestants = _match["contestants"]
            cleaned_contestants: list[dict] = []
            competitionName = _match["competitionName"]
            tournamentName = (
                _match["tournamentName"] if "tournamentName" in _match else None
            )
            sportName: str = _match["sportName"]
            if sportName.lower() in self.ignore_sports:
                print(f"Ignoring {sportName} match: {match_name}")
                continue
            if competitionName in self.ignore_competitions:
                print(f"Ignoring {sportName} match: {match_name}")
                continue
            for _contestant in contestants:
                _contestant.pop("image", None)  # None if key not found
                _contestant.pop("isHome", None)  # None if key not found
                _contestant["short_name"] = _contestant["name"]  # None if key not found
                _contestant.pop("name", None)  # None if key not found
                cleaned_contestants.append(_contestant)

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
                match_shortName = (
                    _market["shortName"] if "shortName" in _market.keys() else None
                )
                propositions_len = len(propositions)
                if propositions_len != 2:
                    continue
                clean_propositions = self._clean_propositions(propositions=propositions)

                two_lower_flag = self._get_lower_odds_flag(
                    clean_propositions=clean_propositions
                )
                # two_fifty_flag = self._get_fifty_odds_flag(
                #     clean_propositions=clean_propositions
                # )

                full_name_0 = clean_propositions[0]["name"]
                full_name_1 = clean_propositions[1]["name"]
                if len(cleaned_contestants) == 0:
                    cleaned_contestants = [{}, {}]
                    cleaned_contestants[0]["full_name"] = full_name_0
                    cleaned_contestants[1]["full_name"] = full_name_1
                else:
                    cleaned_contestants[0]["full_name"] = full_name_0
                    cleaned_contestants[1]["full_name"] = full_name_1
                doubles_or_other_flag = True
                if (
                    sportName.lower() in self.doubles_only_sports
                    and "/" not in full_name_0
                    and "/" not in full_name_1
                ):
                    print(
                        f"Expected doubles match for '{sportName}' but got '{match_name}' with propositions '{full_name_0}' and '{full_name_1}'"
                    )
                    doubles_or_other_flag = False

                key = "full_name"
                cleaned_contestants_new: list[dict] = []
                for _clean_contentant in cleaned_contestants:
                    if key in _clean_contentant:
                        new_copy = _clean_contentant.copy()
                        value = new_copy.pop(key)
                        cleaned_contestants_new.append({key: value, **new_copy})
                cleaned_contestants = cleaned_contestants_new.copy()
                proposition_names_odds = [
                    f"{p['name']}, ({p['returnWin']})" for p in clean_propositions
                ]
                proposition_names = [f"{p['name']}" for p in clean_propositions]
                contestant_full_names_odds = " VERSES ".join(proposition_names_odds)
                contestant_full_names = " VERSES ".join(proposition_names)
                # if any([two_lower_flag, two_fifty_flag]):
                if any([two_lower_flag]):
                    start_time_aest = datetime.fromisoformat(
                        start_time.replace("Z", "+00:00")
                    )
                    # Convert to AEST
                    aest_dt = start_time_aest.astimezone(ZoneInfo("Australia/Sydney"))
                    aest_dt_iso = aest_dt.isoformat()

                    comp_stats_str = self._get_comp_statistics(
                        stats_data=odds_analysis_pd,
                        comp_name=competitionName,
                        sport_name=sportName,
                        tournament_name=tournamentName,
                    )
                    # compress contestants dict
                    contestants_locations = {
                        f"{item['position']}_contestant": item["full_name"]
                        for item in contestants
                    }


                    match_details = {
                        "contestant_names_prop": contestant_full_names_odds,
                        "contestant_names": contestant_full_names,
                        "start_time_aest": aest_dt_iso,
                        "sport_name": sportName,
                        "competition_name": competitionName,
                        "tournamentName": tournamentName,
                        "HOME_contestant": contestants_locations["HOME_contestant"],
                        "AWAY_contestant": contestants_locations["AWAY_contestant"],
                        # "contestants": cleaned_contestants,
                        # "propositions": clean_propositions,
                        "comp_stats": comp_stats_str,
                        "match_name": match_name,
                        "match_shortName": match_shortName,
                        # "competitors": competitors,
                        # "betOption": betOption,
                        # "bettingStatus": bettingStatus,
                        "start_time": start_time,
                        # "two_dollar_flag": two_dollar_flag,
                    }
                    if tournamentName is None:
                        match_details.pop("tournamentName")

                if two_lower_flag is True and doubles_or_other_flag is True:
                    all_matches_ls["lower_odds"].append(match_details.copy())
                # if two_fifty_flag is True:
                #     all_matches_ls["fifty_odds"].append(match_details.copy())
        return all_matches_ls
