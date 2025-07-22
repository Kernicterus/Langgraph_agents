from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, SystemMessage, BaseMessage, AIMessage

from typing import Annotated, List
from typing_extensions import TypedDict
import os
from pydantic import BaseModel, Field
from src.utils.constants import DIR_MD_OUTPUT, RED, BLUE, YELLOW, GREEN, RESET, ORANGE
from src.prompts.arborescence_prompts import ARBORESCENCE_PROMPT, ARBORESCENCE_REVIEWER_PROMPT, build_arborescence_prompt
from src.utils.utils_agent import add_note, check_reviewing_process, ask_user_create_files

class ArborescenceDetails(BaseModel):
    file_path: str = Field(description="The path to the file")
    file_interfaces: str = Field(description="A description of the interfaces needed and provided by the file")
    file_dependencies: str = Field(description="A description of the dependencies of the file")
    file_objectives: str = Field(description="A description of the objectives of the file")
    feature_ids: List[str] = Field(description="The list of feature identifiers from the manifest that this file implements or contributes to")
    gdpr_ids: List[str] = Field(description="The list of GDPR identifiers from the manifest that this file implements or contributes to")

class ArborescenceOutput(BaseModel):
    arborescence_md: str = Field(description="The Markdown diagram of the project's folder and file structure")
    arborescence_details: List[ArborescenceDetails]

class reviewer_response(BaseModel):
    note : int = Field(description="The note of the review on a scale of 0 to 100")
    comment : str = Field(description="The comments and critiques about the reviewed arborescence")

class Arborescence_state(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    note : Annotated[List[int], add_note]
    iteration : int
    arborescence_md : str
    arborescence_details : List[ArborescenceDetails]
    iteration_max : int
    note_max : int
    diff_notes_max : int
    gdpr_manifest : str
    architecture_manifest : str


class Arborescence_agent:
    def __init__(self, model):
        graph = StateGraph(Arborescence_state)
        graph.add_node("arborescence_node", self.arborescence_node)
        graph.add_node("review_node", self.review_node)

        graph.set_entry_point("arborescence_node")
        graph.add_edge("arborescence_node", "review_node")
        graph.add_conditional_edges(
            "review_node",
            self.check_reviewing_process,
            {True: END, False: "arborescence_node"}
        )
        
        self.model = model
        self.system_prompt_arborescence = ARBORESCENCE_PROMPT
        self.system_prompt_reviewer = ARBORESCENCE_REVIEWER_PROMPT
        self.graph = graph.compile()


    def arborescence_node(self, state: Arborescence_state):
        structured_response = self.model.with_structured_output(ArborescenceOutput).invoke(
            [SystemMessage(content=self.system_prompt_arborescence)] + state["messages"]
        )
        print(f"{GREEN}=========== Arborescence RESPONSE ==========={RESET}")
        print(f"Iteration {state['iteration']} :")
        print(f"{structured_response.arborescence_md}")
        print("--------------------------------")

        for detail in structured_response.arborescence_details:
            print(f"File Path : {detail.file_path}")
            print(f"File Interfaces : {detail.file_interfaces}")
            print(f"File Dependencies : {detail.file_dependencies}")
            print(f"File Objectives : {detail.file_objectives}")
            print(f"Feature IDs : {detail.feature_ids}")
            print(f"GDPR IDs : {detail.gdpr_ids}")
            print("--------------------------------")
        print("=========================================")
        return {"messages": [AIMessage(content=structured_response.arborescence_md)], "arborescence_md": structured_response.arborescence_md, "arborescence_details": structured_response.arborescence_details}


    def review_node(self, state: Arborescence_state):
        structured_response = self.model.with_structured_output(reviewer_response).invoke(
            [SystemMessage(content=self.system_prompt_reviewer)] + state["messages"]
        )
        print(f"{RED}=========== REVIEWER RESPONSE ==========={RESET}")
        print(f"Iteration {state['iteration']} : Note {structured_response.note}")
        print(f"Comment : {structured_response.comment}")
        print(f"========================================={RESET}")
        if state["iteration"] > 0:
            if state["note"][-1] - structured_response.note > 0:
                return {"messages": [HumanMessage(content=structured_response.comment)], "note": structured_response.note, "iteration": state["iteration"]}
        return {"messages": [HumanMessage(content=structured_response.comment)], "note": structured_response.note, "iteration": state["iteration"] + 1}
    

    def check_reviewing_process(self, state: Arborescence_state):
        return check_reviewing_process(state["iteration"], state["note"], state["iteration_max"], state["note_max"], state["diff_notes_max"])


if __name__ == "__main__":
    from langchain_google_genai import ChatGoogleGenerativeAI
    import os
    from dotenv import load_dotenv

    load_dotenv()

    model = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0, google_api_key=os.getenv("GOOGLE_API_KEY"))
    arborescence_agent_instance = Arborescence_agent(model)
    with open(os.path.join(DIR_MD_OUTPUT, "manifest_architecture.md"), "r") as f:
        architecture_manifest = f.read()
    with open(os.path.join(DIR_MD_OUTPUT, "manifest_gdpr.md"), "r") as f:
        gdpr_manifest = f.read()
    result = arborescence_agent_instance.graph.invoke({
        "messages": [HumanMessage(content=build_arborescence_prompt(architecture_manifest, gdpr_manifest))], 
        "iteration": 0, 
        "iteration_max": 4, 
        "note_max": 90, 
        "diff_notes_max": 5, 
        "architecture_manifest": architecture_manifest, 
        "gdpr_manifest": gdpr_manifest
        })
    
    print(f"{BLUE}Saving arborescence_md.md{RESET}")
    with open(os.path.join(DIR_MD_OUTPUT, "arborescence_md.md"), "w", encoding='utf-8') as f:
        f.write(result["arborescence_md"])

    if ask_user_create_files(result["arborescence_details"]) is False:
        exit()

    for i, detail in enumerate(result["arborescence_details"]):
        print(f"{BLUE}Saving arborescence_details for {detail.file_path}{RESET}")
        filename = f"arborescence_details_{i}.txt"
        with open(os.path.join(f"{DIR_MD_OUTPUT}/arborescence_details", filename), "w", encoding='utf-8') as f:
            f.write(f"File Path : {detail.file_path}\n")
            f.write(f"File Interfaces : {detail.file_interfaces}\n")
            f.write(f"File Dependencies : {detail.file_dependencies}\n")
            f.write(f"File Objectives : {detail.file_objectives}\n")
            f.write(f"Feature IDs : {detail.feature_ids}\n")
            f.write(f"GDPR IDs : {detail.gdpr_ids}\n")


