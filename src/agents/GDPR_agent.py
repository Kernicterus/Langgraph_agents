from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage, BaseMessage, AIMessage
from langchain_core.tools import tool

from typing import Annotated, List, Tuple, Dict
from typing_extensions import TypedDict
import os
from pydantic import BaseModel, Field
from src.constants import DIR_MD_OUTPUT, INPUT_GDPR
from src.agents.prompts import PROMPT_GDPR_AGENT, PROMPT_GDPR_REVIEWER_AGENT
from src.agents.search_agent import SearchAgent

def add_note(existing_notes: List[int], new_note: int) -> List[int]:
    if not existing_notes :
        return [new_note]
    return existing_notes + [new_note]

@tool
def get_search_agent_response(query: str) -> str:
    """Use this tool to get the response from the search agent."""
    search_agent = SearchAgent(model)
    response = search_agent.run(query)
    return response


class GDPR_state(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    note : Annotated[List[int], add_note]
    iteration : int
    manifest : str
    comment_architecture : str

class reviewer_response(BaseModel):
    note : int = Field(description="The note of the review on a scale of 0 to 100")
    comment : str = Field(description="The comments and critiques about the reviewed GDPR manifest")
    comment_architecture : str = Field(description="The comments and critiques about the architecture manifest")

class GDPR_agent:
    def __init__(self, model):
        graph = StateGraph(GDPR_state)
        graph.add_node("GDPR_node", self.GDPR_node)
        graph.add_node("review_node", self.review_node)
        graph.add_node("search_node", self.search_node)

        graph.set_entry_point("GDPR_node")
        graph.add_edge("GDPR_node", "review_node")
        graph.add_conditional_edges(
            "review_node",
            self.check_reviewing_process,
            {True: END, False: "GDPR_node"}
        )
        graph.add_conditional_edges(
            "GDPR_node",
            self.exists_action,
            {True: "search_node", False: "review_node"}
        )
        graph.add_edge("search_node", "GDPR_node")

        self.model = model
        self.system_prompt_GDPR = PROMPT_GDPR_AGENT
        self.system_prompt_GDPR_reviewer = PROMPT_GDPR_REVIEWER_AGENT
        self.graph = graph.compile()


    def GDPR_node(self, state: GDPR_state):
        response = self.model.bind_tools([get_search_agent_response]).invoke(
            [SystemMessage(content=self.system_prompt_GDPR)] + state["messages"]
        )
        print("=========== GDPR RESPONSE ===========")
        print(f"Iteration {state['iteration']} : {response.content}")
        print("=========================================")
        return {"messages": [AIMessage(content=response.content)], "manifest": response.content}


    def review_node(self, state: GDPR_state):
        structured_response = self.model.with_structured_output(reviewer_response).invoke(
            [SystemMessage(content=self.system_prompt_GDPR_reviewer)] + state["messages"]
        )
        print("=========== REVIEWER RESPONSE ===========")
        print(f"Iteration {state['iteration']} : Note {structured_response.note}")
        print(f"Comment : {structured_response.comment}")
        print("=========================================")
        return {"messages": [HumanMessage(content=structured_response.comment)], "note": structured_response.note, "iteration": state["iteration"] + 1, "comment_architecture": structured_response.comment_architecture}
    

    def check_reviewing_process(self, state: GDPR_state):
        print(f"check_reviewing_process : {state['iteration']} : {state['note']}")
        print(f"last note : {state['note'][-1]}")
        if state["iteration"] >= 4:
            return True
        if state["note"][-1] >= 85:
            return True
        if state["iteration"] >= 2 :
            diff_notes = abs(state["note"][-1] - state["note"][-2])
            if diff_notes <= 5:
                return True
        return False
    
    def exists_action(self, state: GDPR_state):
        """Checks if the last message contains tool calls."""
        print("--- Checking Tool Action ---")
        last_message = state["messages"][-1]
        has_tool_calls = hasattr(last_message, 'tool_calls') and len(last_message.tool_calls) > 0
        print(f"Tool calls present: {last_message.tool_calls}")
        if len(last_message.tool_calls) > 1:
            print("Error: Only one tool call is allowed at a time.")
            print("Tool calls: ", last_message.tool_calls)
            has_tool_calls = False
        return has_tool_calls
        
    def search_node(self, state: GDPR_state):
        """Executes tool calls requested by the GDPR_node."""
        print("============ Calling Tool Node =============")
        last_message = state["messages"][-1]
        tool_calls = last_message.tool_calls
        print(f"Requested tool calls: {tool_calls}")

        results_messages = []
        if len(tool_calls) != 1:
            return {"messages": []}
        elif tool_calls[0]['name'] != "search_agent":
            print(f"Error: Tool call {tool_calls[0]['name']} not found.")
            return {"messages": []}
        else:
            tool_call = tool_calls[0]
            tool_name = tool_call['name']
            args = tool_call['args']
            print(f"Executing tool: {tool_name} with args: {args}")
            result_content = ""
            
            try:
                result_content = get_search_agent_response(args['query'])
            except Exception as e:
                print(f"Error during execution of search agent: {e}")
                result_content = f"Internal error during tool call {tool_name}: {str(e)}"

            results_messages.append(ToolMessage(
                content=result_content,
                tool_call_id=tool_call['id']
            ))
        return {"messages": results_messages}


if __name__ == "__main__":
    from langchain_google_genai import ChatGoogleGenerativeAI
    import os
    from dotenv import load_dotenv

    load_dotenv()

    model = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0, google_api_key=os.getenv("GOOGLE_API_KEY"))
    gdpr_agent_instance = GDPR_agent(model)
    print("===== INPUT======")
    print(INPUT_GDPR)
    print("===========")
    result = gdpr_agent_instance.graph.invoke({"messages": [HumanMessage(content=INPUT_GDPR)], "iteration": 0})
    md = result["manifest"]
    filename = "gdpr_manifest.md"
    dir = DIR_MD_OUTPUT
    with open(os.path.join(dir, filename), "w") as f:
        f.write(md)


