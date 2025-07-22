from typing import List, TYPE_CHECKING
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import os
from src.utils.constants import YELLOW, RESET, BLUE, RED, GREEN, ORANGE
from src.utils.custom_messages import ArchitectMessage, GDPRMessage, ReviewerMessage, SecurityMessage

if TYPE_CHECKING:
    from src.agents.arborescence_agent import ArborescenceDetails

def add_note(existing_notes: List[int], new_note: int) -> List[int]:
    if not existing_notes :
        return [new_note]
    return existing_notes + [new_note]

def summarize_messages(messages: List[BaseMessage]) -> str:
    load_dotenv()
        
    messages_to_summarize = ""
    model = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0, max_output_tokens=512, google_api_key=os.getenv("GOOGLE_API_KEY"))
    for message in messages:
        if isinstance(message, ArchitectMessage):
            author = "Architect"
        elif isinstance(message, GDPRMessage):
            author = "GDPR"
        elif isinstance(message, SecurityMessage):
            author = "Security"
        elif isinstance(message, ReviewerMessage):
            author = "Reviewer"
        else :
            continue
        messages_to_summarize += f"'{author} : {message.content}'\n"
    summary_prompt = f"""
    You are an assistant who summarizes technical work and analysis. 
    You will receive a list of messages from an agent and a reviewer.
    Create a concise and informative summary (2-3 paragraphs) that captures:
    - The main technical points and decisions made
    - The key findings and recommendations
    - The evolution of the work through the different iterations

    Here are the messages to summarize :
    """

    summary = model.invoke([SystemMessage(content=summary_prompt), HumanMessage(content=messages_to_summarize)]).content
    print(f"{YELLOW}Summary : {summary}{RESET}")
    return summary

def check_reviewing_process(iteration: int, note: List[int], iteration_max, note_max, diff_notes_max):
    print(f"check_reviewing_process : {iteration} : {note}")
    print(f"last note : {note[-1]}")
    if iteration >= iteration_max - 1:
        return True
    if note[-1] >= note_max:
        return True
    if iteration >= 2 :
        diff_notes = abs(note[-1] - note[-2])
        if diff_notes <= diff_notes_max:
            return True
    return False


def ask_user_create_files(arborescence_details: List["ArborescenceDetails"]):
    for detail in arborescence_details:
        print(f"{BLUE}File Path : {detail.file_path}{RESET}")
    print(f"{ORANGE}TOTAL FILES : {len(arborescence_details)}{RESET}")
    print(f"{ORANGE}DO YOU WANT TO CREATE THESE FILES ? (y/n){RESET}")
    answer = input()
    if answer == "y":
        return True
    else:
        return False