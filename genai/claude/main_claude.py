import anthropic

from dotenv import load_dotenv
import yaml
from pydantic import BaseModel
import datetime

load_dotenv()  # loads .env from current directory


class MatchWinnerLoserProbabilities(BaseModel):
    winner_name: str
    winner_probability: str
    loser_name: str
    loser_probability: str


def run_app():
    print(datetime.datetime.now())
    prompt_path = "secrets/prompts.yml"
    # prompt_path = "secrets/prompts/baseball/main_baseball.yml"
    with open(prompt_path, "r") as _f:
        prompts = yaml.safe_load(_f)

    contents = prompts["2026-04-12"]

    client = anthropic.Anthropic()

    message = client.messages.create(
        # model="claude-haiku-4-5", # no search
        model="claude-sonnet-4-6",
        max_tokens=4096,
        thinking={"type": "enabled", "budget_tokens": 1024},
        system=contents,
        messages=[
            {
                "role": "user",
                "content": """
        "contestant_names": "Lokomotiv Plovdi VERSES Spartak Pleven",
        "start_time_aest": "2026-04-21T02:15:00+10:00",
        "sport_name": "Basketball",
        "competition_name": "Bulgaria NBL",
        "contestant_HOME": "Lokomotiv Plovdi",
        "contestant_AWAY": "Spartak Pleven",
                """,
            }
        ],
         tools=[{"type": "web_search_20260209", "name": "web_search"}],
        output_config={
            "format": {
                "type": "json_schema",
                "schema": {
                    "type": "object",
                    "properties": {
                        "winner_name": {"type": "string"},
                        "winner_probability": {"type": "string"},
                        "loser_name": {"type": "string"},
                        "loser_probability": {"type": "string"},
                    },
                    "required": ["winner_name", "loser_name", "winner_probability", "loser_probability"],
                    "additionalProperties": False,
                },
            }
        },
    )
    print(message.content)
    # model="claude-sonnet-4-6",
    # $0.80 each prompt

    print(datetime.datetime.now())


if __name__ == "__main__":
    run_app()

    # https://platform.claude.com/docs/en/api/messages/create
    # https://platform.claude.com/docs/en/about-claude/models/overview
    # https://platform.claude.com/settings/billing