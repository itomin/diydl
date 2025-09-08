import os
import logging
from typing import Optional, Callable, Any
from openai import OpenAI

from pydantic import BaseModel, Field
from tools import Tool, Name
from prompt import template
# https://medium.com/google-cloud/building-react-agents-from-scratch-a-hands-on-guide-using-gemini-ffe4621d90ae

class Message(BaseModel):
    role: str = Field(..., description="The role of the message sender.")
    content: str = Field(..., description="The content of the message.")

class Choice(BaseModel):
    tool_name: Optional[str] = Field(None, description="The name of the tool chosen.")
    answer: Optional[str] = Field(None, description="The answer to the query.")
    input: Optional[str] = Field(None, description="The input for the tool.")
    reason: str = Field(..., description="The reason for choosing this tool.")


class Agent:
    def __init__(self, system: str = "", model="gpt-4o-mini") -> None:
        print("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY"))
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.system = system
        self.model = model
        self.messages: list[Message] = []
        self.tools: dict[Name, Tool] = {}
        self.max_iterations = 5
        self.current_iteration = 0
        self.query = ""
        self.template = template
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    def __call__(self, message=""):
        if message:
            self.messages.append(Message(role="user", content=message))
        result = self.execute(message)
        self.messages.append(Message(role="assistant", content=result))
        return result


    def register(self, name: Name, tool: Tool) -> None:
        self.tools[name] = tool


    def _ask(self, prompt: str) -> Choice:
        response = self.client.responses.parse(
            model=self.model, 
            input=prompt,  # Use the formatted prompt string, not self.messages
            text_format=Choice)
        return response.output_parsed
    

    def think(self) -> None:
        self.current_iteration += 1
        self.logger.info(f"THINK: Starting iteration {self.current_iteration}/{self.max_iterations}")
        
        if self.current_iteration > self.max_iterations:
            self.logger.warning("THINK: Maximum iterations reached, stopping")
            return
            
        prompt = self.template.format(
            query=self.query, 
            history=self.get_history(),
            tools="".join([
                "Tool Name: " + str(tool.name).lower() + "\n" +
                "Description: " + tool.description + "\n" +
                "Parameters: " + str(tool.parameters) + "\n\n"
                "--------------------------------" + "\n"
                for tool in self.tools.values()
            ])
        )
        
        choice = self._ask(prompt)
        self.logger.info(f"THINK: Received choice: tool_name={choice.tool_name}, 
        reason={choice.reason}, answer={choice.answer}")
        
        self.trace("assistant", f"Thought: {choice}")
        self.decide(choice)


    def decide(self, choice: Choice) -> None:
        self.logger.info(f"DECIDE: Deciding with choice: {choice}")
        try:
            # Prioritize answer over tool_name if both are present
            if choice.answer:
                self.logger.info(f"DECIDE: Final answer provided: {choice.answer}")
                self.trace("assistant", f"Final Answer: {choice.answer}")
            elif choice.tool_name:
                # Find the tool by name
                tool_name_enum = Name[choice.tool_name.upper()]
                tool = self.tools.get(tool_name_enum)
                if tool:
                    self.act(tool, choice.input or self.query)
                else:
                    self.trace("system", f"Tool {choice.tool_name} not found")
                    self.think()
            else:
                raise ValueError("Invalid response format")
        except Exception as e:
            self.trace("system", f"Error in decision: {e}")
            self.think()

    def act(self, tool: Tool, input: Any) -> None:
        self.logger.info(f"ACT: Executing tool {tool.name} with input: {input}")
        
        if tool:
            try:
                result = tool.use(input)
                observation = f"Observation from {tool.name}: {result}"
                self.trace("system", observation)
                self.think()
            except Exception as e:
                self.logger.error(f"ACT: Error executing tool {tool.name}: {e}")
                self.trace("system", f"Error executing tool {tool.name}: {e}")
                self.think()
        else:
            self.logger.warning("ACT: No tool provided, continuing to think")
            self.think()

    def trace(self, role: str, content: str) -> None:
        self.messages.append(Message(role=role, content=content))
        
        with open("trace.txt", 'a', encoding='utf-8') as file:
            content += "\n--------------------------------\n"
            file.write(content)
        
    def execute(self, query: str) -> str:
        """
        Executes the agent's query-processing workflow.

        Args:
            query (str): The query to be processed.

        Returns:
            str: The final answer or last recorded message content.
        """
        self.logger.info(f"EXECUTE: Starting execution with query: {query[:100]}...")
        self.query = query
        self.trace(role="user", content=query)
        self.think()
        
        result = self.messages[-1].content
        self.logger.info(f"EXECUTE: Execution completed, result: {result[:100]}...")
        return result

    
    def get_history(self) -> str:
        history = ""
        for message in self.messages:
            history += f"{message.role}: {message.content}\n"
            history += "--------------------------------\n"
            # self.logger.info(f"GET_HISTORY: {history}")
        return history




if __name__ == "__main__":
    from tools import WikipediaTool, SumTool
    agent = Agent()
    agent.register(Name.WIKIPEDIA, WikipediaTool())
    agent.register(Name.SUM, SumTool())
    print(agent.execute("Was ist die Summe der Geburtsjahre von Aryna Sabalenka und Anett Kontaveit?"))