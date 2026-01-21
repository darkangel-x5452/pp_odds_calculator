import os
import yaml
import re
from utils.entities_map import MatchesEntity


def load_api(company_id: str) -> str:
    """Load API keys from a YAML file."""
    companies = os.environ["COMPANY_MAP_FP"]
    with open(companies, "r") as f:
        api_keys = yaml.safe_load(f)

    return api_keys[company_id]

def compare_matches(c1a_matches: list[MatchesEntity], c2a_matches: list[MatchesEntity]) -> None:
    for c1a_match in c1a_matches:
        c1a_contestant_0_full_name = c1a_match.contestants[0].full_name
        c1a_contestant_0_odds = c1a_match.contestants[0].odds
        c1a_contestant_0_full_name = re.sub(r"[^a-zA-Z0-9]", "", c1a_contestant_0_full_name).lower()
        c1a_contestant_1_full_name = c1a_match.contestants[1].full_name
        c1a_contestant_1_full_name = re.sub(r"[^a-zA-Z0-9]", "", c1a_contestant_1_full_name).lower()
        c1a_contestant_1_odds = c1a_match.contestants[1].odds
        for c2a_match in c2a_matches:
            c2a_contestant_0_full_name = c2a_match.contestants[0].full_name
            c2a_contestant_0_full_name = re.sub(r"[^a-zA-Z0-9]", "", c2a_contestant_0_full_name).lower()
            c2a_contestant_0_odds = c2a_match.contestants[0].odds
            c2a_contestant_1_full_name = c2a_match.contestants[1].full_name
            c2a_contestant_1_full_name = re.sub(r"[^a-zA-Z0-9]", "", c2a_contestant_1_full_name).lower()
            c2a_contestant_1_odds = c2a_match.contestants[1].odds
            # if "xintong" in c1a_contestant_0_full_name:
            #     print("fdfsf")
            # if "xintong" in c2a_contestant_1_full_name or "xintong" in c2a_contestant_0_full_name:
            #     print("fdfsf")
            # print(f"Matched: {c1a_contestant_0_full_name}  ===  {c2a_contestant_0_full_name}")
            if c1a_contestant_0_full_name in c2a_contestant_0_full_name:
                print(f"Matched: {c1a_contestant_0_full_name}, {c1a_contestant_0_odds}  ===  {c2a_contestant_1_full_name}, {c2a_contestant_1_odds}")
                print(f"Matched: {c1a_contestant_1_full_name}, {c1a_contestant_1_odds}  ===  {c2a_contestant_0_full_name}, {c2a_contestant_0_odds}")