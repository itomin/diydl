import re
import httpx


class WikipediaTool:
    def __init__(self):
        self.name = "wikipedia"
        self.description = "Search Wikipedia for information"
        self.parameters = {
            "type": "object",
            "properties": {"q": {"type": "string", "description": "The search query"}},
        }

    def __call__(self, q):
        return httpx.get("https://en.wikipedia.org/w/api.php", params={
        "action": "query",
        "list": "search",
        "srsearch": q,
        "format": "json"
    }).json()["query"]["search"][0]["snippet"]


class CalculatorTool:
    def __init__(self):
        self.name = "calculator"
        self.description = "Calculate the result of an arithmetic operation"
        self.parameters = {
            "type": "object",
            "properties": {"operation": {"type": "string", "description": "The arithmetic operation to perform"}},
        }
    def __call__(self, operation: str) -> float:
        return eval(operation)