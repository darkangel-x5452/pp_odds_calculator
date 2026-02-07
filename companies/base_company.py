from abc import abstractmethod
from utils.entities_map import MatchesEntity
from utils.tools import load_api


class BaseCompany:
    def __init__(self, company_id: str):
        self.company_map = load_api(company_id)
        self.company_url = self.company_map["url"]
        self.company_name = self.company_map["name"]
        
        self.payload = {}
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": "PostmanRuntime/7.51.0",
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br",
        }
        
        self.high_odds = 3.0
        self.min_odds = 2.0

    @abstractmethod
    def get_matches_matches(self, input_jn: dict) -> list[MatchesEntity]:

        return []