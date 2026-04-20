from openai import OpenAI

class ChatGpt:
    def __init__(self):
        pass


    def run_prompt():
        client = OpenAI()

        response = client.responses.create(
            model="gpt-5.4",
            input="Write a one-sentence bedtime story about a unicorn."
        )

        print(response.output_text)