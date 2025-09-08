import re
import httpx
import logging
import json
from typing import Callable
import wikipediaapi
from enum import Enum, auto

class Name(Enum):
    """Enumeration for tool names available to the agent."""
    WIKIPEDIA = auto()
    SUM = auto()
    NONE = auto()
    def __str__(self) -> str:
        return self.name.lower()

class Tool:
    def __init__(self, name: Name, func: Callable[[str], str], description: str, parameters: dict):
        self.name = name
        self.func = func
        self.description = description
        self.parameters = parameters

    def use(self, query: str) -> str:
        try:
            return self.func(query)
        except Exception as e:
            raise Exception(f"Error executing tool {self.name}: {e}")
            

class WikipediaTool(Tool):
    def __init__(self):
        super().__init__(
            Name.WIKIPEDIA, 
            self.__call__,
            """
            Use this tool to search for specific facts or information from Wikipedia.
            It's a reliable source for factual data such as birth dates, historical events,
            or biographical details. You MUST use this tool to find information you don't already have.
            Provide only one named entity, do not include any other text.‚
            """,
            {
                "type": "object",
                "properties": {"type": "string", "description": "PROVIDE ONLY ONE NAMED ENTITY, e.g Michael Jackson, Walmart, Sony, etc.‚"},
            }
        )
        self.logger = logging.getLogger(__name__)
        self.wiki = wikipediaapi.Wikipedia(
            user_agent='ReAct Agents (hello@ivantomin.com)',
            language='en'
        )

    def __call__(self, q):
        try:
            self.logger.info(f"Searching Wikipedia for: {q}")
            page = self.wiki.page(q)

            if page.exists():
                # Create a dictionary with query, title, and summary
                result = {
                    "query": q,
                    "title": page.title,
                    "summary": page.summary
                }
                self.logger.info(f"Successfully retrieved summary for: {q}")
                return json.dumps(result, ensure_ascii=False, indent=2)
            else:
                self.logger.info(f"No results found for query: {q}")
                return None

        except Exception as e:
            self.logger.exception(f"An error occurred while processing the Wikipedia query: {e}")
            return None


class SumTool(Tool):
    def __init__(self):
        super().__init__(
            Name.SUM, 
            self.__call__,
            """
            Use this tool to calculate the sum of any numbers.
            It's a reliable tool for calculating sums of numbers.
            You MUST use this tool to calculate sums of numbers you don't already have.
            """,
            {
                "type": "object",
                "properties": {"type": "list[int]", "description": "The numbers to sum"},
            }
        )
    def __call__(self, numbers) -> int:
        if isinstance(numbers, list):
            # Parse every string in the list to a number and sum
            return sum(float(str(num)) for num in numbers)
        elif isinstance(numbers, str):
            # Handle string input like "[1998, 1995]"
            try:
                parsed = json.loads(numbers)
                if isinstance(parsed, list):
                    return sum(float(str(num)) for num in parsed)
            except:
                return 0
        return 0