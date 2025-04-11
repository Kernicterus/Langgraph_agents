from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage, BaseMessage, AIMessage
from langchain_core.tools import tool

from typing import Annotated, List, Tuple, Dict
from typing_extensions import TypedDict
import os
from pydantic import BaseModel, Field
from src.constants import DIR_MD_OUTPUT, PROMPT_ARCHI


# def add_note(state: Dict, note: int) -> Dict:
#     if "note" not in state:
#         state["note"] = []
#     state["note"].append(note)
#     return state

def add_note(existing_notes: List[int], new_note: int) -> List[int]:
    if not isinstance(existing_notes, list):
        existing_notes = []
    return existing_notes + [new_note]

prompt_architect_agent = """
Role: You are a senior software architect. You receive a high-level description of a web application (webapp) from a user. Based on this, your mission is to produce a clear, structured, documented software architecture manifest ready to be used by other experts (including a GDPR specialist and a technical reviewer).

Objectives:
1. Analyze the information provided by the user about the webapp.

2. Generate a structured software architecture manifest including:

    A detailed list of required functionalities, each with:

        A clear and descriptive name

        A unique identifier (in the form: FUNCTIONALITY_NAME_[ID])

    A classification of functionalities:

        First into two main categories: Frontend vs Backend

        Then by section, according to the software architecture chosen by the user (for example: for a hexagonal architecture, include sections: Adapters, Ports, Use Cases, Domain, etc.)

    A brief description for each functionality, specifying its role, dependencies, and interactions with other modules or components.

    Take into account the type of API chosen by the user (RESTful, GraphQL, etc.) and adapt the architecture accordingly.

The manifest must be clear, structured, and easily readable by:

    A GDPR specialist, who will use the identifiers to create a GDPR manifest

    A technical reviewer, who will provide critical feedback

Once feedback from the reviewer is received, analyze the comments and propose an improved version of the manifest, justifying the modifications.

Expected manifest structure:# Software Architecture Manifest - [Project Name]

## Overview
Project summary, functional context, technological choices, type of architecture (e.g., hexagonal, microservices, modular monolithic, etc.)

## Required Functionalities

### Backend

#### [Section of the chosen architecture: example "Ports"]

- **Create a user** (`CREATE_USER_B001`)
  - Description: Allows a new user to register via the backend.
  - Dependencies: Authentication, User database
  - Interacts with: Frontend > Registration form

#### [Next section...]

- ...

### Frontend

#### [Section of the chosen architecture: example "User Interface"]

- **Login form** (`LOGIN_FORM_F001`)
  - Description: Allows a user to enter their credentials.
  - Dependencies: Auth API, UI Components
  - Interacts with: Backend > Authentication

#### [Next section...]

- ...

## Identifier Glossary

| Identifier | Name | Type | Section |
|-------------|-----|------|---------|
| CREATE_USER_B001 | Create a user | Backend | Ports |
| LOGIN_FORM_F001 | Login form | Frontend | UI Interface |
"""

class Architect_state(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    note : Annotated[List[int], add_note]
    iteration : int


class reviwer_response(BaseModel):
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
        self.system_prompt = prompt_architect_agent
        self.graph = graph.compile()


    def architect_node(self, state: Architect_state):
        response = self.model.invoke(
            [SystemMessage(content=self.system_prompt)] + state["messages"]
        )
        return {"messages": [AIMessage(content=response.content)]}


    def review_node(self, state: Architect_state):
        response = self.model.invoke(
            [SystemMessage(content=self.system_prompt)] + state["messages"]
        ).with_structured_output(reviwer_response)
        print(f"Iteration {state['iteration']} : Note {response.note}")
        return {"messages": [HumanMessage(content=response.comment)], "note": response.note, "iteration": state["iteration"] + 1}
    

    def check_reviewing_process(self, state: Architect_state):
        print(f"check_reviewing_process : {state['iteration']} : {state['note']}")
        if state["iteration"] >= 4:
            return True
        if state["note"][-1] >= 80:
            return True
        if state["iteration"] >= 2 :
            diff_notes = abs(state["note"][-1] - state["note"][-2])
            if diff_notes <= 7:
                return True
        return False


if __name__ == "__main__":
    from langchain_google_genai import ChatGoogleGenerativeAI
    import os
    from dotenv import load_dotenv

    load_dotenv()

    model = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0, google_api_key=os.getenv("GOOGLE_API_KEY"))
    architect_agent_instance = Architect_agent(model)
    print("===========")
    print(PROMPT_ARCHI)
    print("===========")
    result = architect_agent_instance.graph.invoke({"messages": [HumanMessage(content=PROMPT_ARCHI)], "note": [], "iteration": 0})

    filename = "architecture_manifest.md"
    dir = DIR_MD_OUTPUT
    with open(os.path.join(dir, filename), "w") as f:
        f.write(md)


