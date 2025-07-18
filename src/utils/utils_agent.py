from typing import List
from langchain_core.messages import BaseMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import os

def add_note(existing_notes: List[int], new_note: int) -> List[int]:
    if not existing_notes :
        return [new_note]
    return existing_notes + [new_note]

def summarize_messages(messages: List[BaseMessage]) -> str:
    load_dotenv()
    model = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0, google_api_key=os.getenv("GOOGLE_API_KEY"))
    system_prompt = """
    You are an assistant who summarizes conversations between agents and reviewers. 
    Create a balanced summary (4-5 paragraphs) that captures:
    - The main points of the evaluations performed
    - The improvements made following feedback
    - The evolution of work quality
    Do not mention the created manifests, focus on the revision process.
    """
    summary = model.invoke([SystemMessage(content=system_prompt)] + messages).content
    
    return summary

def check_reviewing_process(iteration: int, note: List[int], iteration_max: int = 4, note_max: int = 90, diff_notes_max: int = 5):
    print(f"check_reviewing_process : {iteration} : {note}")
    print(f"last note : {note[-1]}")
    if iteration >= iteration_max:
        return True
    if note[-1] >= note_max:
        return True
    if iteration >= 2 :
        diff_notes = abs(note[-1] - note[-2])
        if diff_notes <= diff_notes_max:
            return True
    return False