from openai import OpenAI
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
    client = OpenAI()
    prompt_path = "secrets/prompts.yml"
    # prompt_path = "secrets/prompts/baseball/main_baseball.yml"
    with open(prompt_path, "r") as _f:
        prompts = yaml.safe_load(_f)

    contents = prompts["2026-04-12"]
    # response = client.responses.create(
    response = client.responses.parse(
        # model="gpt-5",
        # model="gpt-5.4-mini",
        model="gpt-5.4-nano",
        tools=[{"type": "web_search"}],
        reasoning={
            # "effort": "low"
            "effort": "medium"
            # "effort": "high"
            },
        instructions="You are a smart sports analysis.",
        input=[
            {"role": "system", "content": contents},
            {
                "role": "user",
                "content": """
        "contestant_names": "Madhesh Province VERSES Nepal APF",
        "start_time_aest": "2026-04-13T13:15:00+10:00",
        "sport_name": "Cricket",
        "competition_name": "PM Cup 50-Over",
        "contestant_HOME": "Madhesh Province",
        "contestant_AWAY": "Nepal APF",
             """,
            },
        ],
        text_format=MatchWinnerLoserProbabilities,
    )
    print(response.output_parsed)
    print(response.output_text)
    print(datetime.datetime.now())
    # Base
    # April budget$0.77 / $50
    # After gpt-5.4-nano, reasoning medium
    # April budget$0.78 / $50
    # After gpt-5.4-nano, reasoning medium
    # April budget$0.80 / $50
    # After gpt-5.4-nano, reasoning medium
    # April budget$0.89 / $50
    # awaiting tofas, 2026-04-12 19:44:57.236351
    # April budget $0.91 / $50
    # April budget $0.92 / $50
    # end cost tofas, 2026-04-12 19:44:57.236351
    # awaiting Wigan, 2026-04-12 21:43:24.093675
    # April budget $0.99 / $50
    # 2026-04-13 12:29:40.621393, Madhesh Province
    # 2026-04-13 12:35:32.625037
    # April budget $1.01 / $50
    # end 2026-04-13 12:36:59.804023
    # April budget $1.05 / $50


if __name__ == "__main__":
    run_app()
    # try:
    # https://developers.openai.com/api/docs/guides/text#reusable-prompts
    # for cheaper batch processing
    # https://developers.openai.com/api/docs/guides/batch

    # Other pricing
    # https://modelstudio.console.alibabacloud.com/ap-southeast-1/?tab=doc#/doc/?type=model&url=prices
    # https://api-docs.deepseek.com/quick_start/pricing
    # https://platform.claude.com/docs/en/about-claude/pricing
    # https://ai.google.dev/gemini-api/docs/pricing