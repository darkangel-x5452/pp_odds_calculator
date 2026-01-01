def get_matches_comps(input_jn: dict):
    sports = input_jn['nextToGoMatches']['sports']

    competition_lists = []

    for _sport in sports:
        print(f"Sport: {_sport['name']}")
        sport_name = _sport['name']
        competitions = _sport['competitions']
        for _competition in competitions:
            competition_name = _competition['name']
            matches = _competition['matches']
            for _match in matches:
                match_name = _match['name']
                start_time = _match['startTime']
                contestants = _match['contestants']
                competitors = _match['competitors']
                betOptionPriority = _match['betOptionPriority']
                if "Head To Head" not in betOptionPriority:
                    raise Exception(f"Expected 'Head To Head' in betOptionPriority but got {json.dumps(betOptionPriority)}")

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
                    for _proposition in propositions:
                        prop_name = _proposition['name']
                        return_win = _proposition['returnWin']
                        prop_position = _proposition['position']
                        two_dollar_flag = True if return_win >= 2.0 and return_win <= 2.3 else False
                        print(f"  Competition: {competition_name}")
                        print(f"    Match: {match_name}")

def get_matches_matches(resp_jn: dict):
    return get_matches_comps(resp_jn)