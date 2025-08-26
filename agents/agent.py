import os
import asyncio
from openai import AsyncOpenAI


class Agent:
    def __init__(self, system: str = "", model="gpt-4o") -> None:
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.system = system
        self.model = model
        self.messages: list = []
        if self.system:
            self.messages.append({"role": "system", "content": system})

    def __call__(self, message=""):
        if message:
            self.messages.append({"role": "user", "content": message})
        result = self._execute()
        self.messages.append({"role": "assistant", "content": result})
        return result

    async def _execute(self):
        response = self.client.responses.create(
            model=self.model, input=self.messages
        )
        return response.output_text