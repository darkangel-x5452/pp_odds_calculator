import json
import os
import re
import ast
from pathlib import Path
import shutil

import numpy as np
import pandas as pd
import yaml

import pandas as pd

from utils.variables_names import SchemaName

STRICT_TS_REGEX = r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}$"
STRICT_TS_FORMAT = "%Y-%m-%d %H:%M:%S%z"


def parse_strict_timestamp_col(series: pd.Series, col_name: str) -> pd.Series:
    s = series.astype("string")

    # 1) Exact visual format check
    bad_format_mask = ~s.str.fullmatch(STRICT_TS_REGEX, na=False)
    if bad_format_mask.any():
        bad = s[bad_format_mask]
        raise ValueError(
            f"{col_name} has values not matching "
            f"'YYYY-MM-DD HH:MM:SS+HH:MM'. "
            f"Bad rows: {bad.index.tolist()[:10]} | "
            f"Bad values: {bad.tolist()[:10]}"
        )

    # 2) Real datetime validation check
    parsed = pd.to_datetime(
        s,
        format=STRICT_TS_FORMAT,
        exact=True,
        errors="coerce",
        utc=True,
    )

    bad_datetime_mask = parsed.isna()
    if bad_datetime_mask.any():
        bad = s[bad_datetime_mask]
        raise ValueError(
            f"{col_name} has invalid datetime values even though the string "
            f"shape looked correct. "
            f"Bad rows: {bad.index.tolist()[:10]} | "
            f"Bad values: {bad.tolist()[:10]}"
        )

    return parsed

def copy_missing_prefixed_files(
    source_dir: str,
    dest_dir: str,
    prefix: str,
) -> None:
    src = Path(source_dir)
    dst = Path(dest_dir)

    if not src.exists():
        raise FileNotFoundError(f"Source directory does not exist: {src}")

    dst.mkdir(parents=True, exist_ok=True)

    # Existing filenames already in destination
    existing_files = {file.name for file in dst.iterdir() if file.is_file()}

    # Find source files with matching prefix
    for file in src.iterdir():
        if not file.is_file():
            continue

        if not file.name.startswith(prefix):
            continue

        if file.name in existing_files:
            print(f"Skipping already exists: {file.name}")
            continue

        shutil.copy2(file, dst / file.name)
        print(f"Copied: {file.name}")

class ResultsAnalysis(SchemaName):
    """
    Analyse the results of odd placements and accuracy of the odd placements.
    """

    def __init__(self):
        super().__init__()
        data_raw_dir = "/mnt/c/Users/s/Downloads/"
        data_dir = "data/source/odd_site/results/"
        copy_missing_prefixed_files(source_dir=data_raw_dir, dest_dir=data_dir, prefix="statement_4912079")

        data_files = os.listdir(data_dir)


        data_statements = [f"{data_dir}/{_file}" for _file in data_files if _file.startswith("statement_4912079")]
        data_transact = [f"{data_dir}/{_file}" for _file in data_files if _file.startswith("Transaction Details ")]

        self.src_data_ls = data_statements + data_transact
        
        self.hist_files_ls = [
            "data/results/matches_odds_50_historical.json",
            "data/results/matches_odds_historical_snapshot_20260125.json",
            "data/results/matches_odds_historical_snapshot_20260207.json",
            "data/results/matches_odds_historical_snapshot_20260303.json",
            "data/results/matches_odds_historical.json",
        ]
        # self.src_hist_odds_fp = "data/results/matches_odds_historical.json"
        self.description_col = "Description"
        self.odds_on_col = "odds_on"
        self.return_price_col = "return_price"
        self.match_code_col = "match_code"
        self.sport_genre_col = "sport_genre"
        self.hash_id_col = "hash_id"
        self.timestamp_aest_col = "timestamp_aest"
        self.start_time_aest_col = "start_time_aest"
        self.outcome_prob_fp = "data/results/outcome_probabilities.yml"
        self.time_diff_col = "time_diff"

        self.result_col = "Result"
        self.competition_name_col = "competition_name"
        self.home_result_col = "home_result"

        self.separators = [
            "Hd to Hd",
            "Hd2Hd",
            "WnrOfTie",
            "Winner",
            "Method of Result",
            "Lift Trophy",
            "Result",
            "Top 6",
            "Top 2",
            "25/26",
            "Colombia President",
        ]

        # Define all possible price marker strings
        self.price_markers = [
            "@Price",
            "match must be",
            "includes overtime",
            "normal time",
            "regular season",
            "includes super over",
        ]

    def read_and_cln_data(self) -> pd.DataFrame:
        debit_col = "Debit"
        timestamp_aest_col = self.timestamp_aest_col
        result_df = pd.DataFrame()
        for _file in self.src_data_ls:
            file_name = _file.split("/")[-1]
            data_df = pd.read_csv(_file, skiprows=3, on_bad_lines="skip")
            data_df_copy = data_df.copy()
            find = data_df_copy[data_df_copy["Description"].str.contains("5338939")]
            if len(find) > 0:
                print(f"Found match code in description: {find['Description'].iloc[0]}")
                print(find)
            if file_name.startswith("statement"):
                dropna_subset = ["Time (AEST)"]
                filter_rows = ~data_df_copy[self.description_col].str.startswith(
                    ("Transaction number: ", "Withdrawal", "Deposit")
                )
                data_df_copy = data_df_copy.dropna(subset=dropna_subset)
                data_df_copy = data_df_copy[filter_rows]
                data_df_copy = data_df_copy.dropna(subset=["Result"])
            elif file_name.startswith("Transaction"):
                dropna_subset = ["Bet Type"]
                data_df_copy = data_df_copy.dropna(subset=dropna_subset)
                dropna_subset = ["Fixed Price Odds"]
                data_df_copy = data_df_copy.dropna(subset=dropna_subset)
                data_df_copy = data_df_copy.dropna(subset=["Results"])
            else:
                raise ValueError("Bad file naming.")

            if file_name.startswith("statement"):
                data_cln_df = self._statement_description_extraction(
                    input_df=data_df_copy
                )
            elif file_name.startswith("Transaction"):
                data_cln_df = self._transaction_description_extraction(
                    input_df=data_df_copy
                )
            else:
                raise ValueError("Bad file naming.")

            data_cln_df[debit_col] = (
                data_cln_df[debit_col].replace(r"[\$,]", "", regex=True).astype(float)
            )
            data_cln_df["return_price"] = data_cln_df["return_price"].astype(float)

            data_cln_df["timestamp_aest"] = pd.to_datetime(
                data_cln_df["Date (AEST)"] + ", " + data_cln_df["Time (AEST)"],
                format="%a %d %b %Y, %H:%M:%S",
            ).dt.tz_localize("Australia/Sydney")

            group_cols = ["match_code", "odds_on", "Date (AEST)"]
            sum_col = "return_price"
            max_col = "Date (AEST)"

            agg_dict = {
                "return_price": "sum",
                debit_col: "sum",
                timestamp_aest_col: "min",
            }

            for col in data_cln_df.columns:
                if col not in group_cols + [sum_col, max_col]:
                    agg_dict[col] = "first"

            df_agg = data_cln_df.groupby(group_cols, as_index=False).agg(agg_dict)

            # Create hash id column
            hash_cols = [self.match_code_col, self.odds_on_col, timestamp_aest_col]
            df_agg[self.hash_id_col] = pd.util.hash_pandas_object(
                df_agg[hash_cols].astype(str), index=False
            ).astype(str)
            keep_cols = [
                self.description_col,
                self.odds_on_col,
                self.return_price_col,
                self.match_code_col,
                # "Date (AEST)",
                # "Time (AEST)",
                "timestamp_aest",
                # "Type",
                # "Description",
                # "Detail",
                "Odds",
                "Result",
                debit_col,
                self.hash_id_col,
            ]
            df_agg = df_agg[keep_cols]
            result_df = pd.concat([result_df, df_agg], ignore_index=True)
        return result_df

    def read_hist_data(self):
        contestants_col = "contestants"
        non_sports_list = [
            # "Tennis",
            # "Badminton",
            "Esports",
            # "Basketball",
            # "Ice Hockey",
            # "Volleyball",
            # "Soccer",
            # "Boxing",
            # "Beach Volleyball",
            # "Rugby Union",
            # "Rugby League",
            # "AFL Football",
            # "UFC",
            # "Table Tennis",
            # "Squash",
            # "Netball",
            "Winter Olympics",
        ]
        combined_df = pd.DataFrame()
        for hist_file in self.hist_files_ls:
            with open(hist_file, "r") as _f:
                hist_jn = json.load(_f)
            for _item in hist_jn:
                if "propositions" in _item.keys():
                    _item["contestants"][0]["full_name"] = _item["propositions"][0][
                        "name"
                    ]
                    _item["contestants"][1]["full_name"] = _item["propositions"][1][
                        "name"
                    ]

            # hist_odds_df = pd.read_json(hist_file)
            hist_odds_df = pd.DataFrame(hist_jn)
            new_cols = [
                "contestant_names_odds",
                "start_time_old",
                "start_time_aest_old",
                "contestant_names_prop",
            ]
            for _new_col in new_cols:
                if _new_col not in hist_odds_df.columns:
                    if _new_col in ["contestant_names_odds", "contestant_names_prop"]:
                        hist_odds_df[_new_col] = hist_odds_df["contestant_names"]
                    elif _new_col in ["start_time_old", "start_time_aest_old"]:
                        hist_odds_df[_new_col] = hist_odds_df["start_time_aest"]
            hist_odds_cln_df = hist_odds_df.drop(
                columns=[
                    "contestant_names",
                    # "start_time_aest",
                    # "sport_name",
                    # "competition_name",
                    # "tournamentName",
                    # "contestants",
                    "propositions",
                    # "match_name",
                    "betOption",
                    "start_time",
                    "contestant_names_odds",
                    "start_time_old",
                    "start_time_aest_old",
                    "contestant_names_prop",
                    # "match_shortName",
                ]
            )
            hist_odds_cln_df = pd.concat(
                [
                    hist_odds_cln_df,
                    hist_odds_cln_df[contestants_col].apply(self._flatten_players),
                ],
                axis=1,
            )

            hist_odds_cln_df[self.sport_genre_col] = np.where(
                hist_odds_cln_df["sport_name"].isin(non_sports_list),
                hist_odds_cln_df["competition_name"],
                hist_odds_cln_df["sport_name"],
            )

            mask = (
                hist_odds_cln_df["home_full_name"].str.contains("/", na=False)
                | hist_odds_cln_df["away_full_name"].str.contains("/", na=False)
            ) & hist_odds_cln_df["sport_name"].isin(["Tennis", "Badminton"])

            hist_odds_cln_df.loc[mask, self.sport_genre_col] = (
                hist_odds_cln_df.loc[mask, self.sport_genre_col] + " Doubles"
            )
            combined_df = pd.concat([combined_df, hist_odds_cln_df], ignore_index=True)
        # hist_df[hist_df["home_full_name"]=='Aleksandar Kovacevic']
        combined_df = combined_df.drop(columns=[contestants_col]).drop_duplicates()
        # TODO: Need to remove dupes caused by start time changing
        return combined_df

    def _flatten_players(self, lst):
        # d = {x["position"]: x for x in lst}
        return pd.Series(
            {
                "home_full_name": lst[0].get("full_name", None),
                "home_short_name": lst[0].get("short_name", None),
                "away_full_name": lst[1].get("full_name", None),
                "away_short_name": lst[1].get("short_name", None),
            }
        )

    def _get_unique_matches(self, input_data: pd.DataFrame) -> pd.DataFrame:

        input_data[self.start_time_aest_col] = pd.to_datetime(
            input_data[self.start_time_aest_col]
            .astype("string")
            .str.replace("T", " ", regex=False),
            utc=True,
            errors="raise",
        ).dt.tz_convert("Australia/Sydney")

        start_dt = parse_strict_timestamp_col(input_data[self.start_time_aest_col], self.start_time_aest_col)
        ts_dt = parse_strict_timestamp_col(input_data[self.timestamp_aest_col], self.timestamp_aest_col)

        input_data[self.time_diff_col] = (start_dt - ts_dt).dt.total_seconds() / 3600
        input_data[self.time_diff_col] = (
            (
                pd.to_datetime(input_data[self.start_time_aest_col])
                - pd.to_datetime(input_data[self.timestamp_aest_col])
            ).dt.total_seconds()
            / 60
            / 60
        )

        input_data = input_data[
            (input_data[self.time_diff_col] > -6)
            & (input_data[self.time_diff_col] < 12)
        ]
        return input_data

    def _check_missing_ids(self, core_df: pd.DataFrame, other_df: pd.DataFrame):
        remaining_df = core_df[
            ~core_df[self.hash_id_col].isin(other_df[self.hash_id_col])
        ]
        return remaining_df

    def _remove_dupe_matches(self, input_df: pd.DataFrame) -> pd.DataFrame:
        input_df[self.time_diff_col] = input_df[self.time_diff_col].abs()
        input_df = input_df.sort_values([self.hash_id_col, self.time_diff_col])
        input_df = input_df.drop_duplicates(
            subset=self.hash_id_col, keep="first"
        ).reset_index(drop=True)

        return input_df

    def combine_metadata(
        self, data_df: pd.DataFrame, hist_df: pd.DataFrame, prob_df: pd.DataFrame
    ) -> pd.DataFrame:

        # Merge results with hist based on match code first
        joined_df = data_df.merge(
            hist_df,
            left_on=["match_code"],
            right_on=["match_shortName"],
            how="left",
            # suffixes=("", "_hist_home")
        ).dropna(subset=["match_shortName"])

        joined_df = self._get_unique_matches(input_data=joined_df)

        remaining_df = data_df[
            ~data_df[self.hash_id_col].isin(joined_df[self.hash_id_col])
        ]

        home_joined = remaining_df.merge(
            hist_df,
            left_on=[self.odds_on_col],
            right_on=["home_full_name"],
            how="left",
            # suffixes=("", "_hist_home")
        ).dropna(subset=["home_full_name"])

        away_joined = remaining_df.merge(
            hist_df,
            left_on=[self.odds_on_col],
            right_on=["away_full_name"],
            how="left",
            # suffixes=("", "_hist_away")
        ).dropna(subset=["away_full_name"])
        union_df = pd.concat([home_joined, away_joined], ignore_index=True)

        remaining_joined_df = self._get_unique_matches(input_data=union_df)

        combined_unique_df = pd.concat(
            [joined_df, remaining_joined_df], ignore_index=True
        )

        dup_cols = [
            c
            for c in combined_unique_df.columns
            if c not in [self.time_diff_col, "start_time_aest", "contestants"]
        ]

        df_result = combined_unique_df.sort_values(
            self.time_diff_col, ascending=False
        ).drop_duplicates(subset=dup_cols, keep="first")
        df_result = df_result.sort_values(self.timestamp_aest_col, ascending=False)
        check_dupes = df_result[df_result.duplicated("hash_id", keep=False)]

        if len(check_dupes) > 0:
            print(f"Warning: Duplicates found in combined data: '{len(check_dupes)}'")
            df_result = self._remove_dupe_matches(df_result)
        df_result = df_result.merge(
            prob_df[[self.hash_id_col, "probability"]], on=self.hash_id_col, how="left"
        )
        missing_ids = self._check_missing_ids(data_df, df_result)
        if len(missing_ids) > 0:
            print(f"Missing ids from core in result df. Len '{len(missing_ids)}'")


        mask = df_result["competition_name"].eq("League of Legends")

        df_result.loc[mask, ["competition_name", "sport_name"]] = (
            df_result.loc[mask, ["tournamentName", "competition_name"]].to_numpy()
        )
        return df_result

    def save_results(self, df: pd.DataFrame, fp: str):
        df.to_parquet(fp, index=False)

    def read_prob_data(self) -> pd.DataFrame:
        with open(self.outcome_prob_fp, "r") as _f:
            prob_jn = yaml.safe_load(_f)
        prob_df = pd.json_normalize(prob_jn)
        prob_df["probability"] = pd.to_numeric(
            prob_df["probability"].astype(str).str.lstrip("0")
        ).astype(float)
        return prob_df

    def update_prob_data_rows(self, input_data: pd.DataFrame):
        with open(self.outcome_prob_fp, "r") as _f:
            prob_data_str = _f.read()

        prob_data_str = prob_data_str.replace("probability: 0", "probability: ")
        prob_data_jn = yaml.safe_load(prob_data_str)
        if prob_data_jn is not None:
            prob_df = pd.DataFrame(prob_data_jn)

            prob_df_hashes = prob_df[[self.hash_id_col]]
            joined_df = prob_df_hashes.merge(
                input_data, on=self.hash_id_col, how="left", suffixes=("", "_prob")
            )
            has_dupes = joined_df[self.hash_id_col].duplicated().any()
            if has_dupes is True:
                raise ValueError(
                    "Warning: Duplicates found when merging probability data with input data."
                )
            new_data_df = input_data[
                ~input_data[self.hash_id_col].isin(prob_df[self.hash_id_col])
            ]
        else:
            new_data_df = input_data
            prob_data_jn = []

        new_data_df["placed_datetimestamp_aest"] = (
            pd.to_datetime(new_data_df[self.timestamp_aest_col])
            .dt.tz_convert("Australia/Sydney")
            .dt.strftime("%Y-%m-%d %H:%M:%S%z")
        )
        selected_df = new_data_df[
            ["match_code", "odds_on", "placed_datetimestamp_aest", "Odds", "hash_id"]
        ]
        selected_jn = selected_df.to_dict(orient="records")
        [_dict.update({"probability": 0}) for _dict in selected_jn]
        prob_data_updated = selected_jn + prob_data_jn
        prob_data_updated = sorted(
            prob_data_updated,
            key=lambda x: x["placed_datetimestamp_aest"],
            reverse=True,
        )

        key_order = [
            "probability",
            "odds_on",
            "match_code",
            "placed_datetimestamp_aest",
            "Odds",
            "hash_id",
        ]

        data = prob_data_updated

        ordered_data = [{k: d[k] for k in key_order if k in d} for d in data]

        with open(self.outcome_prob_fp, "w") as _f:
            yaml.dump(ordered_data, _f, sort_keys=False)

    def _statement_description_extraction(self, input_df: pd.DataFrame):
        # Build regex patterns from the lists (case-insensitive)
        sep_pattern = "|".join(re.escape(s) for s in self.separators)
        price_pattern = "|".join(re.escape(s) for s in self.price_markers)

        # Combine listed separators with the dd/dd date pattern
        combined_sep_pattern = rf"(?:{sep_pattern})"

        # Extract name between any separator and any price marker
        input_df[self.odds_on_col] = input_df[self.description_col].str.extract(
            rf"(?:{combined_sep_pattern})\s+(.+?)\s+(?:{price_pattern})",
            flags=re.IGNORECASE,
        )
        input_df[self.odds_on_col] = input_df[self.odds_on_col].str.replace(
            r"^\d{2}/\d{2}\s*", "", regex=True
        )

        # Extract return price after "Return:"
        input_df[self.return_price_col] = input_df[self.description_col].str.extract(
            r"Return:\$(\d+\.\d+)"
        )
        # Extract match code after "Transaction number: "
        input_df[self.match_code_col] = input_df[self.description_col].str.extract(
            rf"(.+(?:{combined_sep_pattern}))", flags=re.IGNORECASE
        )

        return input_df

    def _transaction_description_extraction(self, input_df: pd.DataFrame):
        # Build regex patterns from the lists (case-insensitive)
        sep_pattern = "|".join(re.escape(s) for s in self.separators)
        price_pattern = "|".join(re.escape(s) for s in self.price_markers)

        # Combine listed separators with the dd/dd date pattern
        combined_sep_pattern = rf"(?:{sep_pattern})"

        # Extract name between any separator and any price marker
        input_df[self.odds_on_col] = input_df[self.description_col].str.extract(
            rf"(?:{combined_sep_pattern})\s+(.+?)\s+(?:{price_pattern})",
            flags=re.IGNORECASE,
        )
        input_df[self.odds_on_col] = input_df[self.odds_on_col].str.replace(
            r"^\d{2}/\d{2}\s*", "", regex=True
        )

        # Extract return price after "Return:"
        input_df[self.return_price_col] = input_df[self.description_col].str.extract(
            r"Return:\$(\d+\.\d+)"
        )
        # Extract match code after "Transaction number: "
        input_df[self.match_code_col] = input_df[self.description_col].str.extract(
            rf"(.+(?:{combined_sep_pattern}))", flags=re.IGNORECASE
        )
        # NOTE:

        # Convert "Date & Time" to Date (AEST)
        input_df["Date (AEST)"] = pd.to_datetime(
            input_df["Date & Time"], format="%a %b %d %Y %H:%M:%S"
        ).dt.strftime("%a %d %b %Y")
        input_df["Time (AEST)"] = pd.to_datetime(
            input_df["Date & Time"], format="%a %b %d %Y %H:%M:%S"
        ).dt.strftime("%H:%M:%S")

        # Convert "Amount" to "Debit" and multiply by -1
        input_df["Debit"] = input_df["Amount"].str.lstrip("-")
        # Rename "Fixed Price Odds" to "Odds"
        input_df["Odds"] = input_df["Fixed Price Odds"].abs()
        # Rename "Results" to "Result", Pay/Won to Credit
        input_df["Result"] = input_df["Results"]
        input_df["Result"] = input_df["Result"].replace({"Pay/Won": "Credit"})

        input_df["Type"] = None
        input_df["Detail"] = None
        input_df["Credit"] = None
        select_cols = [
            "Date (AEST)",
            "Time (AEST)",
            "Type",
            "Description",
            "Detail",
            "Odds",
            "Result",
            "Debit",
            "Credit",
            "Running Balance",
            "odds_on",
            "return_price",
            "match_code",
        ]
        input_df = input_df[select_cols]
        return input_df

    def create_metadata_results(self, data_input: pd.DataFrame):

        # Save results to CSV
        sport_total_win_rate = self._calculate_win_ratio(
            data_input=data_input, group_by=[self.sport_genre_col]
        )
        sport_home_win_rate = self._calculate_home_diff(
            data_input=data_input, group_by=[self.sport_genre_col]
        )

        # Merge Data
        sport_home_win_rate = sport_home_win_rate.rename(
            {"percentage": "home_percentage", "group_total": "home_group_total"}, axis=1
        )
        sport_combined_rate = sport_total_win_rate.merge(
            sport_home_win_rate, on=[self.sport_genre_col], how="outer"
        )
        sport_combined_rate.to_csv(
            f"data/results/win_rate_{'_'.join([self.sport_genre_col])}.csv", index=False
        )

        # Comp results
        comp_group_by = [self.sport_genre_col, self.competition_name_col]
        comp_total_win_rate = self._calculate_win_ratio(
            data_input=data_input, group_by=comp_group_by
        )
        comp_home_win_rate = self._calculate_home_diff(
            data_input=data_input, group_by=comp_group_by
        )

        # Merge Data
        comp_home_win_rate = comp_home_win_rate.rename(
            {"percentage": "home_percentage", "group_total": "home_group_total"}, axis=1
        )
        combined_rate = comp_total_win_rate.merge(
            comp_home_win_rate, on=comp_group_by, how="outer"
        )
        combined_rate = combined_rate[
            [
                "sport_genre",
                "competition_name",
                "percentage",
                "group_total",
                "home_percentage",
                self.ColNames.won_odds_low_percentage_col,
                self.ColNames.total_odds_low_col,
                self.ColNames.won_odds_high_percentage_col,
                self.ColNames.total_odds_high_col,
                self.ColNames.won_odds_low_mean_col,
                self.ColNames.won_odds_high_mean_col,
                "won_probability",
                "lost_probability",
                "home_group_total",
            ]
        ]
        combined_rate.to_csv(
            f"data/results/win_rate_{'_'.join(comp_group_by)}.csv", index=False
        )

    def _calculate_home_diff(
        self, data_input: pd.DataFrame, group_by: list[str]
    ) -> pd.DataFrame:

        group_cols = group_by

        out = (
            data_input.groupby(group_cols + [self.home_result_col])
            .size()
            .unstack(fill_value=0)
            .reindex(columns=["win", "loss"], fill_value=0)
            .stack()
            .rename("count")
            .reset_index()
        )

        out["group_total"] = out.groupby(group_cols)["count"].transform("sum")
        out["percentage"] = (out["count"] / out["group_total"] * 100).round(2)

        out_wins: pd.DataFrame = out[out[self.home_result_col] == "win"]
        out_wins = out_wins.drop(columns=[self.home_result_col])
        out_wins = out_wins.sort_values(group_by, ascending=True)
        out_wins = out_wins[[*group_by, "percentage", "group_total"]]
        out_wins.to_csv(
            f"data/results/results_home_win_rate_{'_'.join(group_by)}.csv", index=False
        )
        return out_wins

    def _calculate_win_ratio(
        self, data_input: pd.DataFrame, group_by: list[str]
    ) -> pd.DataFrame:

        group_cols = group_by

        # Porbability Aggregration
        win_prob_mean = (
            data_input.loc[
                (data_input[self.result_col] == "Credit")
                & data_input["probability"].notna()
                & (data_input["probability"] != 0),
                group_cols + ["probability"],
            ]
            .groupby(group_cols, dropna=False)["probability"]
            .median()
            .round(4)
            .rename("won_probability")
            .reset_index()
        )

        lost_prob_mean = (
            data_input.loc[
                (data_input[self.result_col] == "Lost")
                & data_input["probability"].notna()
                & (data_input["probability"] != 0),
                group_cols + ["probability"],
            ]
            .groupby(group_cols, dropna=False)["probability"]
            .median()
            .round(4)
            .rename("lost_probability")
            .reset_index()
        )

        # ODDS Aggregration
        calc_col = "Odds"
        win_rate_low_odds_mean = (
            data_input.loc[
                (data_input[self.result_col] == "Credit")
                & (data_input[calc_col] <= 1.85),
                group_cols + [calc_col],
            ]
            .groupby(group_cols, dropna=False)[calc_col]
            .median()
            .round(4)
            .rename(self.ColNames.won_odds_low_mean_col)
            .reset_index()
        )

        win_rate_high_odds_mean = (
            data_input.loc[
                (data_input[self.result_col] == "Credit")
                & (data_input[calc_col] > 1.85),
                group_cols + [calc_col],
            ]
            .groupby(group_cols, dropna=False)[calc_col]
            .median()
            .round(4)
            .rename(self.ColNames.won_odds_high_mean_col)
            .reset_index()
        )

        # Win ratio below low odds
        bet_total_odds_low = self.ColNames.total_odds_low_col
        win_rate_low_odds_pct = (
            data_input.loc[(data_input[calc_col] <= 1.85), :]
            .groupby(group_cols + [self.result_col])
            .size()
            .unstack(fill_value=0)
            .reindex(columns=["Credit", "Lost"], fill_value=0)
            .stack()
            .rename("count_odds_low")
            .reset_index()
        )
        win_rate_low_odds_pct[bet_total_odds_low] = win_rate_low_odds_pct.groupby(
            group_cols
        )["count_odds_low"].transform("sum")
        win_rate_low_odds_pct[self.ColNames.won_odds_low_percentage_col] = (
            win_rate_low_odds_pct["count_odds_low"]
            / win_rate_low_odds_pct[bet_total_odds_low]
            * 100
        ).round(2)
        win_rate_low_odds_pct = win_rate_low_odds_pct[
            win_rate_low_odds_pct[self.result_col] == "Credit"
        ]
        win_rate_low_odds_pct = win_rate_low_odds_pct.drop(
            labels=["count_odds_low", self.result_col], axis=1
        )

        # Win ratio below above odds
        bet_total_odds_high = self.ColNames.total_odds_high_col
        count_odds_high = "count_odds_high"
        won_odds_high_percentage = self.ColNames.won_odds_high_percentage_col
        win_rate_high_odds_pct = (
            data_input.loc[(data_input[calc_col] > 1.85), :]
            .groupby(group_cols + [self.result_col])
            .size()
            .unstack(fill_value=0)
            .reindex(columns=["Credit", "Lost"], fill_value=0)
            .stack()
            .rename(count_odds_high)
            .reset_index()
        )
        win_rate_high_odds_pct[bet_total_odds_high] = win_rate_high_odds_pct.groupby(
            group_cols
        )[count_odds_high].transform("sum")
        win_rate_high_odds_pct[won_odds_high_percentage] = (
            win_rate_high_odds_pct[count_odds_high]
            / win_rate_high_odds_pct[bet_total_odds_high]
            * 100
        ).round(2)
        win_rate_high_odds_pct = win_rate_high_odds_pct[
            win_rate_high_odds_pct[self.result_col] == "Credit"
        ]
        win_rate_high_odds_pct = win_rate_high_odds_pct.drop(
            labels=[count_odds_high, self.result_col], axis=1
        )

        # Win Ratio
        out = (
            data_input.groupby(group_cols + [self.result_col])
            .size()
            .unstack(fill_value=0)
            .reindex(columns=["Credit", "Lost"], fill_value=0)
            .stack()
            .rename("count")
            .reset_index()
        )
        out["group_total"] = out.groupby(group_cols)["count"].transform("sum")
        out["percentage"] = (out["count"] / out["group_total"] * 100).round(2)

        out = out.merge(win_prob_mean, how="left", on=group_cols)
        out = out.merge(lost_prob_mean, how="left", on=group_cols)
        out = out.merge(win_rate_low_odds_mean, how="left", on=group_cols)
        out = out.merge(win_rate_high_odds_mean, how="left", on=group_cols)
        out = out.merge(win_rate_low_odds_pct, how="left", on=group_cols)
        out = out.merge(win_rate_high_odds_pct, how="left", on=group_cols)
        fillna_cols = [
            self.ColNames.won_odds_low_percentage_col,
            bet_total_odds_low,
            won_odds_high_percentage,
            bet_total_odds_high,
            self.ColNames.won_odds_low_mean_col,
            self.ColNames.won_odds_high_mean_col,
            "won_probability",
            "lost_probability",
        ]
        out = out.fillna(0.0)

        out_wins: pd.DataFrame = out[out[self.result_col] == "Credit"]
        out_wins = out_wins.drop(columns=[self.result_col])
        out_wins = out_wins.sort_values(group_by, ascending=True)
        out_wins = out_wins[[*group_by, "percentage", "group_total", *fillna_cols]]
        out_wins.to_csv(
            f"data/results/results_total_win_rate_{'_'.join(group_by)}.csv", index=False
        )
        return out_wins

    def add_home_results(self, data_input: pd.DataFrame) -> pd.DataFrame:
        data_input["odds_on_home"] = (
            data_input["odds_on"] == data_input["home_full_name"]
        )
        data_input[self.home_result_col] = np.where(
            data_input[self.result_col].eq("Refund"),
            "invalid",
            np.where(
                (
                    (
                        data_input["odds_on_home"]
                        & data_input[self.result_col].eq("Credit")
                    )
                    | (
                        ~data_input["odds_on_home"]
                        & data_input[self.result_col].eq("Lost")
                    )
                ),
                "win",
                "loss",
            ),
        )

        return data_input


if __name__ == "__main__":
    print("Hi.")
    ra = ResultsAnalysis()
    data_df = ra.read_and_cln_data()
    hist_df = ra.read_hist_data()
    ra.update_prob_data_rows(data_df)
    prob_df = ra.read_prob_data()

    results = ra.combine_metadata(data_df, hist_df, prob_df)
    results_2 = ra.add_home_results(data_input=results)
    # results_2 = results[
    #     [
    #         "Odds",
    #         "odds_on",
    #         "match_code",
    #         "home_full_name",
    #         "away_full_name",
    #         "match_shortName",
    #     ]
    # ]
    ra.save_results(results_2, "data/results/outcome_results.parquet")

    ra.create_metadata_results(data_input=results_2)

    print("Bye.")
