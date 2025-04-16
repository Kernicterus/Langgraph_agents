from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage, BaseMessage, AIMessage
from langchain_core.tools import tool

from typing import Annotated, List, Tuple, Dict
from typing_extensions import TypedDict
import os
from src.utils.utils_UI import get_files_and_context
from src.constants import DIR_MD_OUTPUT

prompt_functional_insight_agent = """
Role:
You are a Functional Insight Agent, specialized in analyzing product documentation and distilling it into actionable software functionalities. You serve as a bridge between detailed documentation and architectural design.

Objective:
Analyze a set of Markdown (.md) files, each describing a different page or section of a web application. Your goal is to infer and synthesize the main functional capabilities of the application based on this information.

Application Context:
{webapp_context}

Architecture requirements:
{architecture}

Constraints & Guidelines:
-Do not summarize each file individually. Instead, extract a global, cross-page understanding.
-Focus on identifying user-facing features, key interactions, system logic, and recurring patterns.
-Use your reasoning ability to group similar functionalities and detect implied behaviors or flows (e.g., authentication, dashboards, form submissions).
-Ignore low-level UI details unless they contribute to understanding a feature.
-you can use the architecture requirements to help you understand the application and the context.
-you can add some insights about the application architecture if you think it's relevant.

Output Format:
Provide a structured Markdown summary with the following format:

## Application General Description
### Description :
[General description of the application]
### Architecture 
[Architecture of the application]

## Core Functionalities Overview

### 1. [Functionality Name]
**Description**: [What it does, for whom, and in what context]  
**Related Pages**: [name of the related page(s)]  

### 2. [Another Functionality Name]
**Description**: [What it does, for whom, and in what context]  
**Related Pages**: [name of the related page(s)]  

### 3. ...

If you add a related page, write the name of the page without the extension and followed by 'page'
example 1: 'Home page'
example 2: 'Login page'

Optional: You may group features by modules, user roles, or use cases if patterns emerge naturally.

Purpose:
Your output will be sent to a Software Architect who will use it as input to define the application's software architecture manifest. Clarity, abstraction, and relevance are key.
If you receive a feedback from the user, you should update your output to reflect the feedback.
"""

class Functional_insight_state(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    files: List[Dict[str, str]]
    webapp_context: str
    error: bool
    architecture: str
    feedback: bool

class Functional_insight_agent:
    def __init__(self, model):
        graph = StateGraph(Functional_insight_state)
        graph.add_node("load_files", self.load_files)
        graph.add_node("functional_insight_node", self.functional_insight_node)
        graph.add_node("human_feedback_node", self.human_feedback_node)

        graph.set_entry_point("load_files")
        graph.add_conditional_edges(
            "load_files",
            lambda state: state.get("error", False),
            {True: END, False: "functional_insight_node"}
        )
        graph.add_edge("functional_insight_node", "human_feedback_node")
        graph.add_conditional_edges(
            "human_feedback_node",
            lambda state: state.get("feedback", False),
            {True: END, False: "functional_insight_node"}
        )
        
        self.model = model
        self.system_prompt = prompt_functional_insight_agent
        self.graph = graph.compile()

    def human_feedback_node(self, state: Functional_insight_state):
        pass

    def load_files(self, state: Functional_insight_state) -> dict:
        files, context, architecture = get_files_and_context(dir)
        if len(files) == 0:
            return {"error": True}
        return {"files": files, "webapp_context": context, "architecture": architecture}


    def functional_insight_node(self, state: Functional_insight_state):
        markdown_files = ["# " + file["name"].split('.')[0] + " page :\n" + file["content"] for file in state["files"]]
        print(markdown_files)
        system_prompt_with_context = self.system_prompt.replace("{webapp_context}", state["webapp_context"]).replace("{architecture}", state["architecture"])
        response = self.model.invoke(
            [SystemMessage(content=system_prompt_with_context)] + [HumanMessage(content=markdown_files)]
        )
        return {"messages": [AIMessage(content=response.content)]}
    

if __name__ == "__main__":
    from langchain_google_genai import ChatGoogleGenerativeAI
    import os
    from dotenv import load_dotenv

    load_dotenv()

    model = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0, google_api_key=os.getenv("GOOGLE_API_KEY"))
    functional_insight_agent_instance = Functional_insight_agent(model)
    result = functional_insight_agent_instance.graph.invoke({"files": [], "error": False, "feedback": False})
    if result['error']:
        print("Error: No files found")
        exit()
    md = result['messages'][-1].content
    filename = "functional_insight.md"
    dir = DIR_MD_OUTPUT
    with open(os.path.join(dir, filename), "w") as f:
        f.write(md)

    


