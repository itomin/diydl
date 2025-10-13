import re
import httpx
import logging
import json
from typing import Callable
import wikipediaapi
from enum import Enum, auto
from openai import OpenAI
import os
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from prompt import summary_template, reflection_template, coding_template

class Name(Enum):
    """Enumeration for tool names available to the agent."""
    WIKIPEDIA = auto()
    SUM = auto()
    CODING = auto()
    REFLECTION = auto()
    SUMMARIZER = auto()
    NONE = auto()
    INVIVO = auto()
    def __str__(self) -> str:
        return self.name.lower()

class Tool:
    def __init__(self, name: Name, func: Callable[[str], str], description: str, parameters: dict):
        self.name = name
        self.func = func
        self.description = description
        self.parameters = parameters

    def use(self, context: Dict[str, Any]) -> str:
        try:
            return self.func(context)
        except Exception as e:
            raise Exception(f"Error executing tool {self.name}: {e}")
            

# class WikipediaTool(Tool):
#     def __init__(self):
#         super().__init__(
#             Name.WIKIPEDIA, 
#             self.__call__,
#             """
#             Use this tool to search for specific facts or information from Wikipedia.
#             It's a reliable source for factual data such as birth dates, historical events,
#             or biographical details. You MUST use this tool to find information you don't already have.
#             Provide only one named entity, do not include any other text.‚
#             """,
#             {
#                 "type": "object",
#                 "properties": {"type": "string", "description": "PROVIDE ONLY ONE NAMED ENTITY, e.g Michael Jackson, Walmart, Sony, etc.‚"},
#             }
#         )
#         self.logger = logging.getLogger(__name__)
#         self.wiki = wikipediaapi.Wikipedia(
#             user_agent='ReAct Agents (hello@ivantomin.com)',
#             language='en'
#         )

#     def __call__(self, q):
#         try:
#             self.logger.info(f"Searching Wikipedia for: {q}")
#             page = self.wiki.page(q)

#             if page.exists():
#                 # Create a dictionary with query, title, and summary
#                 result = {
#                     "query": q,
#                     "title": page.title,
#                     "summary": page.summary
#                 }
#                 self.logger.info(f"Successfully retrieved summary for: {q}")
#                 return json.dumps(result, ensure_ascii=False, indent=2)
#             else:
#                 self.logger.info(f"No results found for query: {q}")
#                 return None

#         except Exception as e:
#             self.logger.exception(f"An error occurred while processing the Wikipedia query: {e}")
#             return None


# class SumTool(Tool):
#     def __init__(self):
#         super().__init__(
#             Name.SUM, 
#             self.__call__,
#             """
#             Use this tool to calculate the sum of any numbers.
#             It's a reliable tool for calculating sums of numbers.
#             You MUST use this tool to calculate sums of numbers you don't already have.
#             """,
#             {
#                 "type": "object",
#                 "properties": {"type": "list[int]", "description": "The numbers to sum"},
#             }
#         )
#     def __call__(self, numbers) -> int:
#         if isinstance(numbers, list):
#             # Parse every string in the list to a number and sum
#             return sum(float(str(num)) for num in numbers)
#         elif isinstance(numbers, str):
#             # Handle string input like "[1998, 1995]"
#             try:
#                 parsed = json.loads(numbers)
#                 if isinstance(parsed, list):
#                     return sum(float(str(num)) for num in parsed)
#             except:
#                 return 0
#         return 0



class Reflection(BaseModel):
    reflection: str = Field(..., description="The reflection of the results of the qualitative research conducting coding of interview data.")
    suggestions: str = Field(..., description="The suggestions for the results of the qualitative research conducting coding of interview data.")


class ReflectionTool(Tool):
    def __init__(self):
        super().__init__(
            Name.REFLECTION, 
            self.__call__,
            """
            Use this tool to reflect on the results of the qualitative research conducting coding of interview data.
            """,
            {
                "type": "object",
                "properties": {"type": "Reflection", "description": "The reflection of the results of the qualitative research conducting coding of interview data."},
            }
        )
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-5"
        
    def __call__(self, ctx):
        prompt = reflection_template.format(
            codes=ctx["codes"],
            research_question=ctx["research_question"],
            question=ctx["question"],
            hypothesis=ctx["hypothesis"],
            intention=ctx["intention"],
            answer=ctx["answer"],
            summary=ctx["summary"],
            history=ctx["history"]  
        )
        # print("--------------- Reflection Prompt -----------------")
        # print("Prompt:", prompt)
        # print("--------------------------------")
        response = self.client.responses.parse(
            model=self.model, 
            input=prompt,
            text_format=Reflection)
        
        return response.output_parsed

class Codes(BaseModel):
    invivo: Optional[List[str]] = Field(None, description="The codes to search for.")
    descriptive: Optional[List[str]] = Field(None, description="The codes to search for.")
    process: Optional[List[str]] = Field(None, description="The codes to search for.")

class CodingTool(Tool):
    def __init__(self):
        super().__init__(
            Name.CODING, 
            self.__call__,
            """
            Use this tool to perform qualitative research conducting first-cycle coding of interview data.
            """,
            {
                "type": "object",
                "properties": {"type": "Coding", "description": "The codes to search for."}
            }
        )
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-5"
        
    def __call__(self, ctx):
        prompt = coding_template.format(
            research_question=ctx["research_question"],
            question=ctx["question"],
            answer=ctx["answer"],
            intention=ctx["intention"],
            hypothesis=ctx["hypothesis"],
            summary=ctx["summary"],
            history=ctx["history"],
            codes=ctx["codes"]
            )
        print("--------------- Coding Prompt -----------------")
        print("Prompt:", prompt)
        print("--------------------------------")
        response = self.client.responses.parse(
            model=self.model, 
            input=prompt,
            text_format=Codes)
        
        return response.output_parsed

class Summary(BaseModel):
    summary: str = Field(..., description="The summary of the answer.")
    hypothesis: str = Field(..., description="How the answer relates to or contrasts with the hypothesis.")

class SummarizerTool(Tool):
    def __init__(self):
        super().__init__(
            Name.SUMMARIZER, 
            self.__call__,
            """
            Use this tool to perform qualitative research conducting first, hermeneutic-interpretive phase of qualitative data analysis.
            Read the text to gain an initial, holistic understanding without theorizing. Produce a concise, factual Case Summary (2–3 sentences) 
            reflecting the respondent’s expressed meaning, not your interpretation.
            """,
            {
                "type": "object",
                "properties": {"type": "Summary", "description": "The summary of the text."},
            }
        )

        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-5"
        

    def __call__(self, ctx):
        prompt = summary_template.format(
            research_question=ctx["research_question"],
            question=ctx["question"],
            answer=ctx["answer"],
            intention=ctx["intention"],
            hypothesis=ctx["hypothesis"]
        )
        # print("--------------- Summarizer Prompt -----------------")
        # print("Prompt:", prompt)
        # print("--------------------------------")
        response = self.client.responses.parse(
            model=self.model, 
            input=prompt,
            text_format=Summary)
        

        return response.output_parsed