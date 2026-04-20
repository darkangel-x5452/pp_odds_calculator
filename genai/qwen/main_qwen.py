from openai import OpenAI
from dotenv import load_dotenv
import yaml
from pydantic import BaseModel
import datetime

load_dotenv()  # loads .env from current directory


def run_app():
    print(datetime.datetime.now())
    import os
    from openai import OpenAI

    prompt_path = "secrets/prompts.yml"
    # prompt_path = "secrets/prompts/baseball/main_baseball.yml"
    with open(prompt_path, "r") as _f:
        prompts = yaml.safe_load(_f)

    contents = prompts["2026-04-12"]

    client = OpenAI(
        # If the environment variable is not set, replace the following line with: api_key="sk-xxx"
        api_key=os.getenv("DASHSCOPE_API_KEY"),
        # The following is the base_url for the Singapore region.
        base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
    )

    completion = client.chat.completions.create(
    # completion = client.responses.create(
        # model="qwen-plus",  # Model list: https://www.alibabacloud.com/help/en/model-studio/getting-started/models
        model="qwen3.5-flash",  # Model list: https://www.alibabacloud.com/help/en/model-studio/getting-started/models
        # input=[
        messages=[
            {"role": "system", "content": contents},
            {
                "role": "user",
                "content": """
        "start_time_aest": "2026-04-15T01:30:00+10:00",
        "sport_name": "Volleyball",
        "competition_name": "Finland Womens SM-Liiga",
        "contestant_HOME": "Polkky Kuusamo",
        "contestant_AWAY": "Puijo",
             """,
            },
        ],
        extra_body={
            "enable_thinking": True,
            "enable_search": True,
            # "search_options": {
            #     # Web search strategy; only agent is supported
            #     "search_strategy": "agent"
            # },
        },
        # temperature=1.30, # Strongly believed in Puijo winning
        temperature=0.8, # Switches between believed in Polkky Kuusamo winning
        # top_p=1.0,
        # tools=[
        #     {"type": "web_search"},
        #     {"type": "web_extractor"},
        #     {"type": "code_interpreter"},
        # ],
        response_format={"type": "json_object"},  # Specify JSON format return
    )
    # print(completion.model_dump_json())
    print(completion.choices[0].message.content)
    print(datetime.datetime.now())
    # Remaining 985,815 / Total 1,000,000
    # Chennai
    # Remaining 979,976 / Total 1,000,000
    # Seggerman/Shelton CHATGPT 57%, QWEN 51%
    # ACS Targu Jiu CHATGPT 54%, QWEN 58%
    # Kraus/Teichmann CHATGPT 56%, QWEN 62%
    # QWEN: CHATGPT 61%
    #     {
    #     "winner_name": "Peli-Karhut",
    #     "winner_probability": "56%",
    #     "loser_name": "Torpan Pojat Hel",
    #     "loser_probability": "44%"
    # }
    # QWEN: CHATGPT 55%
    # {
    #     "winner_name": "hba-marsky",
    #     "winner_probability": 57,
    #     "loser_name": "bc nokia",
    #     "loser_probability": 43
    # }
    # QWEN: CHATGPT 39%
    # **Calculated Odds:**
    # - **Puijo (W):** 58% (1.72)
    # - **Polkky Kuusamo (W):** 42% (2.38)

if __name__ == "__main__":
    run_app()
    # try:
    # https://www.alibabacloud.com/help/en/model-studio/first-api-call-to-qwen
    # https://www.alibabacloud.com/help/en/model-studio/qwen-api-via-openai-responses?spm=a2c63.p38356.0.i2
    # https://www.alibabacloud.com/help/en/model-studio/web-search
    # https://www.alibabacloud.com/help/en/model-studio/qwen-function-calling
    # https://www.alibabacloud.com/help/en/model-studio/qwen-structured-output?spm=a2c63.p38356.0.i2

    # Usage
    # https://modelstudio.console.alibabacloud.com/ap-southeast-1?spm=a2c63.p38356.0.0.22a44db04byAqW&tab=model#/model-usage/free-quota

    # Pricing
    # https://www.alibabacloud.com/help/en/model-studio/model-pricing
