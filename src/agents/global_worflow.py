from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage, BaseMessage, AIMessage
from langchain_core.tools import tool

from typing import Annotated, List, Tuple, Dict
from typing_extensions import TypedDict
import os
from pydantic import BaseModel, Field
from src.constants import DIR_MD_OUTPUT, INPUT_ARCHI
from src.agents.prompts import PROMPT_ARCHITECT_AGENT, PROMPT_GDPR_AGENT, PROMPT_MANAGER_AGENT, PROMPT_SECURITY_AGENT
from src.utils.utils_agent import add_note, check_reviewing_process
from src.agents.architect_agent import Architect_agent
from src.agents.GDPR_agent import GDPR_agent
from src.utils.utils_agent import summarize_messages

class Global_worflow_state(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    note : Annotated[List[int], add_note]
    iteration : int
    architecture_manifest : str
    architect_messages : List[BaseMessage]
    gdpr_manifest : str
    gdpr_messages : List[BaseMessage]
    security_insight : str
    gdpr_insight : str


class Global_graph:
    def __init__(self, model):
        graph = StateGraph(Global_worflow_state)
        graph.add_node("architect_node", self.architect_node)
        graph.add_node("GDPR_node", self.GDPR_node)

        
        graph.set_entry_point("architect_node")
        graph.add_edge("architect_node", "GDPR_node")
        graph.add_conditional_edges(
            "GDPR_node",
            self.check_reviewing,
            {True: END, False: "architect_node"}
        )
        
        self.model = model
        
        self.graph = graph.compile()
        self.architect_agent = Architect_agent(self.model)
        self.gdpr_agent = GDPR_agent(self.model)


    def architect_node(self, state: Global_worflow_state):
        architect_response = self.architect_agent.graph.invoke({"messages": [HumanMessage(content=INPUT_ARCHI)], "iteration": 0})
        summary = summarize_messages(architect_response["messages"])
        return {"messages": [AIMessage(content=summary)], "architecture_manifest": architect_response["manifest"]}


    def gdpr_node(self, state: Global_worflow_state):
        gdpr_response = self.gdpr_agent.graph.invoke({"messages": [HumanMessage(content=state["architecture_manifest"])], "iteration": 0})
        summary = summarize_messages(gdpr_response["messages"])
        return {"messages": [AIMessage(content=summary)], "gdpr_manifest": gdpr_response["manifest"]}


    def security_node(self, state: Global_worflow_state):
        security_response = self.model.invoke([SystemMessage(content=PROMPT_SECURITY_AGENT) + HumanMessage(content=state["architecture_manifest"] + state["gdpr_manifest"])])
        return {"messages": [AIMessage(content=security_response)], "security_insight": security_response}


    def check_reviewing(self, state: Global_worflow_state):
        return check_reviewing_process(state["iteration"], state["note"], iteration_max=4, note_max=90, diff_notes_max=5)


if __name__ == "__main__":
    from langchain_google_genai import ChatGoogleGenerativeAI
    import os
    from dotenv import load_dotenv

    load_dotenv()

    model = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0, google_api_key=os.getenv("GOOGLE_API_KEY"))
    global_graph_instance = Global_graph(model)
