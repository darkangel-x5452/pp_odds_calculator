import json
from zoneinfo import ZoneInfo

from datetime import datetime

def get_matches_comps(input_jn: dict):
    sports = input_jn['nextToGoMatches']['sports']

    all_matches_ls = []

    match_result_options = [
        "Head To Head",
        "Result",
        "Winner",
        "Winner of Tie",
    ]
    ignore_options = [
        "Leading Point Scorer",
        "Total Points Odd/Even", "Home Team Points Odd/Even", "Away Team Points Odd/Even",
        ]
    
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

                if not any(item in betOptionPriority for item in match_result_options):
                    if not all(item in ignore_options for item in betOptionPriority):
                        print(f"Expected 'Head To Head' in {match_name} betOptionPriority but got {json.dumps(betOptionPriority)}")

                markets = _match['markets']

                for _market in markets:
                    betOption = _market['betOption']
                    if betOption not in match_result_options:
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
    all_matches_ls.sort(
        key=lambda x: datetime.fromisoformat(x["start_time_aest"])
    )
    print(f"Total matches with two dollar odds: {len(all_matches_ls)}")
    with open(f"data/results/matches_with_two_dollar_odds.json", "w") as f:
    # with open(f"data/results/matches_with_two_dollar_odds_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", "w") as f:
        json.dump(all_matches_ls, f, indent=4)

def get_matches_matches(input_jn: dict):
    pass