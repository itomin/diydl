import os
import logging
from typing import Optional, Callable, Any, Dict
from openai import OpenAI

from pydantic import BaseModel, Field
from tools import Tool, Name, SummarizerTool, CodingTool, ReflectionTool, Reflection    
from prompt import template
# https://medium.com/google-cloud/building-react-agents-from-scratch-a-hands-on-guide-using-gemini-ffe4621d90ae

class AgentCoder:
    def __init__(self, system: str = "", model="gpt-4o-mini") -> None:
        self.feedback: list[Reflection] = []
        self.max_iterations = 3
        self.current_iteration = 0
        self.logger = logging.getLogger(__name__)
        self.summarizer = SummarizerTool()
        self.coding = CodingTool()
        self.reflection = ReflectionTool()



    def _summarize(self, context: Dict[str, Any]) -> Dict:
        summary = self.summarizer.use(context)
        print("Summary:", summary)
        context["summary"] = summary    
        return context

    def _code(self, context: Dict[str, Any]) -> Dict:
        codes = self.coding.use(context)
        print("Codes:", codes)
        context["codes"] = codes
        return context

    def _reflect(self, context: Dict[str, Any]) -> Dict:
        reflection = self.reflection.use(context)
        print("Reflection:", reflection)
        self.feedback.append(reflection)
        context["history"] = self.feedback
        return context

    def _isComplete(self) -> bool:
        return self.feedback[-1].reflection == "COMPLETE"

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        context["history"] = self.feedback
        context["codes"] = ""
        context = self._summarize(context)
        for i in range(self.max_iterations):
            print("--------------------Iteration ", i, "----------------")
            context = self._code(context)
            context = self._reflect(context)
            if self._isComplete():
                print("--------------------Complete------------------------")
                break
        return context
    



# "research_question": "Wie nehmen Discount-Kund:innen den Einkauf von Kleidung wahr, und welche Rolle spielen Preis, Markenbewusstsein und Einkaufserlebnis bei ihren Kaufentscheidungen?",
# 1
# "question": "Woran denken sie, wenn sie an den Einkauf von Mode/ Kleidung denken?",
# "intention": "Einkaufsmotivationen von Discount Käufern verstehen",
# "hypothesis": "Discount Kunden empfinden Kleidung Einkaufen als notwendiges Übel",

# 2
# "question": "Wann entscheiden sie sich bewusst für einen günstigen Anbieter, wann bewusst gegen einen günstigen Anbieter in Bezug auf Mode und Kleidung?"
# "intention": "Verstehen, in welchen Situationen Preis eine unter- oder übergeordnete Rolle spielt."
# "hypothesis": "Discount Shopping Kunden interessieren sich wenig für Design und Marke."


# 3
# question: Was ist Ihnen beim Einkaufen von Kleidung besonders wichtig – und was kann Ihnen den Spaß daran schnell verderben?
# intention: Erkennen, was Kund:innen motiviert oder demotiviert beim Einkaufserlebnis.
# hypothesis: Discount Kleidung muss vor allem billig und einfach verfügbar sein.




if __name__ == "__main__":
    agent = AgentCoder()
    context = {
        "answer": "Günstige Preise, schöne modische Accessoires, was Neues entdecken. Ja, ich würd mich auf jeden Fall erst mal erkundigen, ob's Rabatte gibt?",
        "research_question": "Wie nehmen Discount-Kund:innen den Einkauf von Kleidung wahr, und welche Rolle spielen Preis, Markenbewusstsein und Einkaufserlebnis bei ihren Kaufentscheidungen?",
        "question": "Woran denken sie, wenn sie an den Einkauf von Mode/ Kleidung denken?",
        "intention": "Einkaufsmotivationen von Discount Käufern verstehen",
        "hypothesis": "Discount Kunden empfinden Kleidung Einkaufen als notwendiges Übel",
    }
    print(context)
    agent.run(context)