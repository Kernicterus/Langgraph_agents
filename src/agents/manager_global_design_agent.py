from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage, BaseMessage, AIMessage
from langchain_core.tools import tool

from typing import Annotated, List, Tuple, Dict
from typing_extensions import TypedDict
import os
from pydantic import BaseModel, Field
from src.constants import DIR_MD_OUTPUT, INPUT_ARCHI
from src.agents.prompts import PROMPT_ARCHITECT_AGENT, PROMPT_ARCHITECT_REVIEWER_AGENT


def add_note(existing_notes: List[int], new_note: int) -> List[int]:
    if not existing_notes :
        return [new_note]
    return existing_notes + [new_note]

class Manager_conception_state(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    note : Annotated[List[int], add_note]
    iteration : int
    architecture_manifest : str
    gdpr_manifest : str
    security_insight : str
    gdpr_insight : str


class Manager_global_design_agent:
    def __init__(self, model):
        graph = StateGraph(Manager_conception_state)
        graph.set_entry_point("architect_node")
        graph.add_edge("architect_node", "review_node")
        graph.add_conditional_edges(
            "review_node",
            self.check_reviewing_process,
            {True: END, False: "architect_node"}
        )
        
        self.model = model
        self.system_prompt_architect = PROMPT_ARCHITECT_AGENT
        self.graph = graph.compile()


    def architect_node(self, state: Manager_conception_state):
        response = self.model.invoke(
            [SystemMessage(content=self.system_prompt_architect)] + state["messages"]
        )
        print("=========== ARCHITECT RESPONSE ===========")
        print(f"Iteration {state['iteration']} : {response.content}")
        print("=========================================")
        return {"messages": [AIMessage(content=response.content)], "manifest": response.content}


    def check_reviewing_process(self, state: Manager_conception_state):
        print(f"check_reviewing_process : {state['iteration']} : {state['note']}")
        print(f"last note : {state['note'][-1]}")
        if state["iteration"] >= 4:
            return True
        if state["note"][-1] >= 90:
            return True
        if state["iteration"] >= 2 :
            diff_notes = abs(state["note"][-1] - state["note"][-2])
            if diff_notes <= 5:
                return True
        return False


if __name__ == "__main__":
    from langchain_google_genai import ChatGoogleGenerativeAI
    import os
    from dotenv import load_dotenv

    load_dotenv()

    model = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0, google_api_key=os.getenv("GOOGLE_API_KEY"))
    manager_global_design_agent_instance = Manager_global_design_agent(model)
    print("===== INPUT======")
    print(INPUT_ARCHI)
    print("===========")
    result = manager_global_design_agent_instance.graph.invoke({"messages": [HumanMessage(content=PROMPT_ARCHITECT_AGENT)], "iteration": 0})
    md = result["manifest"]
    filename = "architecture_manifest.md"
    dir = DIR_MD_OUTPUT
    with open(os.path.join(dir, filename), "w") as f:
        f.write(md)


