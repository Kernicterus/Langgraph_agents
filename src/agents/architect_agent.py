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
from src.agents.prompts import PROMPT_ARCHITECT_AGENT, PROMPT_ARCHITECT_REVIEWER_AGENT
from src.utils.utils_agent import add_note, check_reviewing_process
from src.utils.custom_messages import ArchitectMessage, ReviewerMessage

class Architect_state(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    note : Annotated[List[int], add_note]
    iteration : int
    manifest : str
    iteration_max : int
    note_max : int
    diff_notes_max : int


class reviewer_response(BaseModel):
    note : int = Field(description="The note of the review on a scale of 0 to 100")
    comment : str = Field(description="The comments and critiques about the reviewed software architecture manifest")


class Architect_agent:
    def __init__(self, model):
        graph = StateGraph(Architect_state)
        graph.add_node("architect_node", self.architect_node)
        graph.add_node("review_node", self.review_node)

        graph.set_entry_point("architect_node")
        graph.add_edge("architect_node", "review_node")
        graph.add_conditional_edges(
            "review_node",
            self.check_reviewing_process,
            {True: END, False: "architect_node"}
        )
        
        self.model = model
        self.system_prompt_architect = PROMPT_ARCHITECT_AGENT
        self.system_prompt_reviewer = PROMPT_ARCHITECT_REVIEWER_AGENT
        self.graph = graph.compile()


    def architect_node(self, state: Architect_state):
        response = self.model.invoke(
            [SystemMessage(content=self.system_prompt_architect)] + state["messages"]
        )
        print("=========== ARCHITECT RESPONSE ===========")
        print(f"Iteration {state['iteration']} : {response.content}")
        print("=========================================")
        return {"messages": [ArchitectMessage(content=response.content)], "manifest": response.content}


    def review_node(self, state: Architect_state):
        structured_response = self.model.with_structured_output(reviewer_response).invoke(
            [SystemMessage(content=self.system_prompt_reviewer)] + state["messages"]
        )
        print(f"=========== REVIEWER RESPONSE ==========={RED}")
        print(f"Iteration {state['iteration']} : Note {structured_response.note}")
        print(f"Comment : {structured_response.comment}")
        print(f"========================================={RESET}")
        return {"messages": [ReviewerMessage(content=structured_response.comment)], "note": structured_response.note, "iteration": state["iteration"] + 1}
    

    def check_reviewing_process(self, state: Architect_state):
        return check_reviewing_process(state["iteration"], state["note"], state["iteration_max"], state["note_max"], state["diff_notes_max"])


if __name__ == "__main__":
    from langchain_google_genai import ChatGoogleGenerativeAI
    import os
    from dotenv import load_dotenv

    load_dotenv()

    model = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0, google_api_key=os.getenv("GOOGLE_API_KEY"))
    architect_agent_instance = Architect_agent(model)
    print("===== INPUT======")
    print(INPUT_ARCHI)
    print("===========")
    result = architect_agent_instance.graph.invoke({"messages": [HumanMessage(content=INPUT_ARCHI)], "iteration": 0, "iteration_max": 4, "note_max": 90, "diff_notes_max": 5})
    md = result["manifest"]
    filename = "architecture_manifest.md"
    dir = DIR_MD_OUTPUT
    with open(os.path.join(dir, filename), "w") as f:
        f.write(md)


