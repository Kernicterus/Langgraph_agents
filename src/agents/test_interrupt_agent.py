from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage, BaseMessage, AIMessage
from langchain_core.tools import tool
from langgraph.types import interrupt, Command
from langgraph.checkpoint.memory import MemorySaver

from typing import Annotated, List, Tuple, Dict
from typing_extensions import TypedDict
import os


prompt_test_agent = """
fait moi un poeme a propos du sujet demande par l'utilisateur
"""

prompt_post_interrupt_node = """
transforme les lettre minuscules en majuscules dans le texte que tu recois.
"""

class Test_agent_state(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    subject: str
    approved: str

class Test_agent:
    def __init__(self, model):
        graph = StateGraph(Test_agent_state)
        graph.add_node("poem_node", self.poem_node)
        graph.add_node("human_feedback_node", self.human_feedback_node)
        graph.add_node("post_interrupt_node", self.post_interrupt_node)

        graph.set_entry_point("poem_node")
        graph.add_edge("poem_node", "human_feedback_node")
        graph.add_edge("human_feedback_node", "post_interrupt_node")
        graph.add_edge("post_interrupt_node", END)

        self.model = model
        self.memory = MemorySaver()
        self.graph = graph.compile(checkpointer=self.memory)


    def human_feedback_node(self, state: Test_agent_state):
        print("Waiting for human feedback...")
        value = interrupt(
            "Do you approve of the poem? (y/n): "
        )
        print(f"Human feedback: {value}")
        return {"approved": value}


    def poem_node(self, state: Test_agent_state):
        response = self.model.invoke(
            [SystemMessage(content=prompt_post_interrupt_node)] + [HumanMessage(content=state["subject"])]
        )
        print(f"========= step 1 done")
        return {"messages": [AIMessage(content=response.content)]}
    
    def post_interrupt_node(self, state: Test_agent_state):
        response = self.model.invoke(
            [SystemMessage(content=prompt_post_interrupt_node)] + [HumanMessage(content=state["messages"][-1].content)]
        )
        print(f"========= step 2 done")
        return {"messages": [AIMessage(content=response.content)]}      
    

if __name__ == "__main__":
    from langchain_google_genai import ChatGoogleGenerativeAI
    import os
    from dotenv import load_dotenv

    load_dotenv()

    model = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0, google_api_key=os.getenv("GOOGLE_API_KEY"))
    Test_agent_instance = Test_agent(model)
    thread = {"configurable": {"thread_id": "123"}}
    result = Test_agent_instance.graph.invoke({"subject": "la vie"}, thread)
    print(f"========= First result: {result}")

    result = Test_agent_instance.graph.invoke(Command(resume="sdfsdfsdf"), thread)
    print(f"========= Second result: {result}")
    


