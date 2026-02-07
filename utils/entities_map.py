from dataclasses import dataclass


@dataclass
class ContestantsEntity:
    short_name: str
    full_name: str
    odds: float
    location: str


@dataclass
class MatchesEntity:
    contestants: list[ContestantsEntity]
    sport: str
    competition: str
    start_time_aest: str
    match_name: str
    bet_option: str
