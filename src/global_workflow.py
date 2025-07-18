from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage, BaseMessage, AIMessage
from langchain_core.tools import tool

from typing import Annotated, List, Tuple, Dict
from typing_extensions import TypedDict
import os
from pydantic import BaseModel, Field
from src.constants import DIR_MD_OUTPUT, RED, BLUE, YELLOW, GREEN, RESET
from src.inputs import INPUT_ARCHI  
from src.agents.prompts import PROMPT_ARCHITECT_AGENT, PROMPT_GDPR_AGENT, PROMPT_MANAGER_AGENT, PROMPT_SECURITY_AGENT, PROMPT_GLOBAL_REVIEWER_AGENT
from src.utils.utils_agent import add_note, check_reviewing_process
from src.agents.architect_agent import Architect_agent
from src.agents.GDPR_agent import GDPR_agent
from src.utils.utils_agent import summarize_messages
from src.utils.custom_messages import ArchitectMessage, GDPRMessage, ReviewerMessage, SecurityMessage

class global_review_response(BaseModel):
    note : int = Field(description="The note of the review on a scale of 0 to 100")
    comment : str = Field(description="The comments and critiques about the global project")


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
    global_review_comment : str


class Global_graph:
    def __init__(self, model):
        graph = StateGraph(Global_worflow_state)
        graph.add_node("architect_node", self.architect_node)
        graph.add_node("GDPR_node", self.gdpr_node)
        graph.add_node("security_node", self.security_node)
        graph.add_node("global_reviewer_node", self.global_reviewer_node)
        
        graph.set_entry_point("architect_node")
        graph.add_edge("architect_node", "GDPR_node")
        graph.add_edge("GDPR_node", "security_node")
        graph.add_edge("security_node", "global_reviewer_node")
        graph.add_conditional_edges(
            "global_reviewer_node",
            self.check_reviewing,
            {True: END, False: "architect_node"}
        )
        
        self.model = model
        
        self.graph = graph.compile()
        self.architect_agent = Architect_agent(self.model)
        self.gdpr_agent = GDPR_agent(self.model)


    def architect_node(self, state: Global_worflow_state):
        if state["iteration"] == 0:
            architect_response = self.architect_agent.graph.invoke({"messages": [HumanMessage(content=INPUT_ARCHI)], "iteration": 0, "iteration_max": 4, "note_max": 90, "diff_notes_max": 5})
        else:
            input = state['architect_messages'] + [HumanMessage(content=state['global_review_comment'])]    
            architect_response = self.architect_agent.graph.invoke({"messages": input, "iteration": 0, "iteration_max": 3, "note_max": 90, "diff_notes_max": 5})
        summary = summarize_messages(architect_response["messages"])
        return {"messages": [ArchitectMessage(content=summary)], "architecture_manifest": architect_response["manifest"]}


    def gdpr_node(self, state: Global_worflow_state):
        gdpr_response = self.gdpr_agent.graph.invoke({"messages": [HumanMessage(content=state["architecture_manifest"])], "iteration": 0, "iteration_max": 3, "note_max": 85, "diff_notes_max": 5})
        summary = summarize_messages(gdpr_response["messages"])
        return {"messages": [GDPRMessage(content=summary)], "gdpr_manifest": gdpr_response["manifest"]}


    def security_node(self, state: Global_worflow_state):
        security_response = self.model.invoke([SystemMessage(content=PROMPT_SECURITY_AGENT), 
                                               HumanMessage(content="architecture manifest : " + state["architecture_manifest"] + "\n" + "gdpr manifest : " + state["gdpr_manifest"])])
        print(f"{RED}=========== SECURITY RESPONSE ==========={RESET}")
        print(f"Security insight : {security_response.content}")
        print(f"=========================================")
        return {"messages": [SecurityMessage(content=security_response.content)], "security_insight": security_response.content}


    def global_reviewer_node(self, state: Global_worflow_state):
        data_for_review = ("architecture manifest : " + "\n" + state["architecture_manifest"] 
        + "\n" + "gdpr manifest : " + "\n" + state["gdpr_manifest"])

        structured_output = self.model.with_structured_output(global_review_response).invoke([SystemMessage(content=PROMPT_GLOBAL_REVIEWER_AGENT),
                                                                                    *state['messages'],
                                                                                    HumanMessage(content=data_for_review)])
        print(f"=========== GLOBAL REVIEWER RESPONSE ==========={RED}")
        print(f"Iteration {state['iteration']} : Note {structured_output.note}")
        print(f"Comment : {structured_output.comment}")
        print(f"========================================={RESET}")
        return {"messages": [ReviewerMessage(content=structured_output.comment)], "note": structured_output.note, "iteration": state["iteration"] + 1, "global_review_comment": structured_output.comment }


    def check_reviewing(self, state: Global_worflow_state):
        return check_reviewing_process(state["iteration"], state["note"], iteration_max=3, note_max=90, diff_notes_max=5)


if __name__ == "__main__":
    from langchain_google_genai import ChatGoogleGenerativeAI
    import os
    from dotenv import load_dotenv

    load_dotenv()

    model = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0, max_output_tokens=4000, google_api_key=os.getenv("GOOGLE_API_KEY"))
    global_graph_instance = Global_graph(model)
    result = global_graph_instance.graph.invoke({"messages": [HumanMessage(content=INPUT_ARCHI)], "iteration": 0, "iteration_max": 4, "note_max": 90, "diff_notes_max": 5})
    global_agent_messages = result['messages']
    manifest_architecture = result['architecture_manifest']
    manifest_gdpr = result['gdpr_manifest']

    with open(os.path.join(DIR_MD_OUTPUT, "global_agent_messages.md"), "w") as f:
        f.write(global_agent_messages)
    with open(os.path.join(DIR_MD_OUTPUT, "manifest_architecture.md"), "w") as f:
        f.write(manifest_architecture)
    with open(os.path.join(DIR_MD_OUTPUT, "manifest_gdpr.md"), "w") as f:
        f.write(manifest_gdpr)