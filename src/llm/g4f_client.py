from g4f.client import Client as g4f

from src.config import Config

class GPT4FREE:
    def __init__(self):
        config = Config()
        self.client = g4f()

    def inference(self, model_id: str, temperature: int, prompt: str) -> str:
        model_id = model_id.replace("g4f-", "")
        chat_completion = self.client.chat.completions.create(
            model=model_id,
            messages=[
                {
                    "role": "user",
                    "content": prompt.strip(),
                }
            ],
            temperature=temperature
        )
        return chat_completion.choices[0].message.content