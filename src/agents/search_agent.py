from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage, BaseMessage, AIMessage
from typing import Annotated, List, Tuple
from typing_extensions import TypedDict
from functools import lru_cache

from langchain_community.tools import DuckDuckGoSearchResults
from langchain_core.tools import tool
from langchain_community.document_loaders import AsyncHtmlLoader
from bs4 import BeautifulSoup

MAX_TOOL_MSG_LENGTH = 8000 
MAX_SEARCH_MSG_LENGTH = 4000

duckduckgo_tool = DuckDuckGoSearchResults(
    max_results=10
)

@tool
def web_scraper_tool(urls_tuple: tuple[str, ...]) -> str:
    """
    Scrape the content of provided URLs (as a tuple) and return the content as a single string.
    Args:
        urls_tuple: Tuple of URLs to scrape.
    Returns:
        str: Text content extracted from web pages, separated by markers.
    """
    urls = list(urls_tuple)
    if not urls:
        return "The provided URL list is empty."

    print(f"--- Scraping URLs: {urls} ---")
    try:
        loader = AsyncHtmlLoader(urls)
        docs = loader.load()

        all_contents = []
        scraped_urls = []

        for i, doc in enumerate(docs):
            html_content = doc.page_content
            source_url = doc.metadata.get('source', urls[i])

            if not html_content:
                print(f"Warning: No HTML content for URL {source_url}")
                continue

            soup = BeautifulSoup(html_content, "html.parser")

            article = soup.find("article") or soup.find("main") or soup.body

            if not article:
                print(f"Warning: Unable to find main content tag for URL {source_url}")
                continue

            for tag in article.find_all(["script", "style", "header", "footer", "nav",
                                       "aside", "form", "noscript", "iframe", "img", "button"]):
                tag.decompose()

            content_tags = article.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p",
                                           "ul", "ol", "li", "blockquote", "td", "th"])
            cleaned_text = "".join([tag.get_text(separator=' ', strip=True) for tag in content_tags])
            cleaned_text = "".join(line for line in cleaned_text.splitlines() if line.strip())


            if cleaned_text.strip():
                all_contents.append(f"--- Content from {source_url} ---\n{cleaned_text}")
                scraped_urls.append(source_url)
            else:
                print(f"Warning: No useful text extracted from {source_url} after cleaning.")


        if not all_contents:
            return "No valid content could be extracted from the provided URLs."

        print(f"--- Scraping successful for {len(scraped_urls)} URLs ---")
        return "---\n".join(all_contents)

    except Exception as e:
        print(f"Error while scraping URLs: {urls}. Error: {e}")
        return f"Error while scraping URLs: {str(e)}"


@lru_cache(maxsize=30)
def cached_web_scraper(urls_tuple: tuple) -> str:
    """
    Cached version of the web scraper that uses a tuple of URLs as a key.
    """
    return web_scraper_tool.invoke({"urls_tuple": urls_tuple})


prompt_search_agent_v3 = """
You are a chat agent specialized in collecting information and searching the web. Your goal is to provide a comprehensive and well-sourced answer to the user's query.

Here is your work process:

1.  **Understanding the Query**: Carefully analyze the sub-queries. Use the `DuckDuckGoSearchResults` tool to find relevant information on the topic or sub-questions.
3.  **Analysis and Selection**: Examine the search results (titles, snippets). Identify a **maximum of 3 URLs** that seem most promising and relevant to provide detailed and reliable information addressing the initial query. If no results seem relevant, indicate it.
4.  **Targeted Scraping**: Among the relevant URLs, use the `web_scraper_tool` **ONLY** with the tuple of selected URLs (maximum 3) to extract detailed content. Only call this tool if you have valid and relevant URLs from the search. Make sure to pass the `urls_tuple` argument correctly.
5.  **Synthesis and Response**: Combine information from search snippets and scraped content (if available) to formulate a complete, coherent, and structured response to the user's initial query in markdown format.
6.  **Source Citation**: At the end of your response, clearly list all URLs you actually used via the `web_scraper_tool` to obtain information. If you only used search snippets, mention it, list the URLs, and explain why you didn't use the `web_scraper_tool`.
7.  **Limit Management**: If information is incomplete, if some URLs couldn't be scraped, or if you reach the scraper call limit, indicate it to the user. You can only use the `web_scraper_tool` 3 times per complete user query.

Be methodical, precise, and transparent about your process and sources. Don't hesitate to indicate if you lack information on certain points.
Don't extrapolate an answer that isn't in the sources.
Don't forget to format your answer in markdown.
Think step by step before answering.
"""

prompt_query_decomposer = """
You are an agent specialized in analyzing and decomposing complex queries. Your mission is to:

1. **Analyze the initial query** from the user to identify different aspects and angles that deserve to be explored.

2. **Decompose the query into sub-questions** that are more specific and targeted which, together, will allow building a complete answer.
   - Each sub-question must be autonomous and precise
   - Avoid redundancies between sub-questions
   - Limit yourself to a maximum of 3 sub-questions to remain efficient
   - Don't extrapolate too many sub-questions, you must stay focused on the initial query.

3. **Transmit everything** to the next node in the form of a structured list in markdown with numbered sub-questions


Example response format:

# Sub-questions:
1. First sub-question
2. Second sub-question
3. Third sub-question

"""

class SearchAgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]


class SearchAgent:
    def __init__(self, model):
        graph = StateGraph(SearchAgentState)
        graph.add_node("query_decomposer", self.call_query_decomposer)
        graph.add_node("researcher_node", self.call_researcher)
        graph.add_node("tool_node", self.call_tool)

        graph.set_entry_point("query_decomposer")
        graph.add_edge("query_decomposer", "researcher_node")
        graph.add_conditional_edges(
            "researcher_node",
            self.exists_action,
            {True: "tool_node", False: END}
        )
        graph.add_edge("tool_node", "researcher_node")

        self.system_researcher = prompt_search_agent_v3
        self.system_query_decomposer = prompt_query_decomposer
        self.model_query_decomposer = model
        self.model_researcher = model.bind_tools([duckduckgo_tool, web_scraper_tool])
        self.graph = graph.compile()
        self.web_scraper_calls = 0

    def _create_ai_message(self, response, sender, type_message):
        """Creates an AI message with appropriate metadata."""
        if type_message == "AIMessage":
            return AIMessage(
                content=response.content,
                tool_calls=getattr(response, 'tool_calls', []),
                response_metadata=getattr(response, 'response_metadata', {}),
                id=getattr(response, 'id', None),
                metadata={"sender_agent": sender}
            )
        elif type_message == "HumanMessage":
            return HumanMessage(
                content=response.content,
                tool_calls=getattr(response, 'tool_calls', []),
                response_metadata=getattr(response, 'response_metadata', {}),
                id=getattr(response, 'id', None),
                metadata={"sender_agent": sender}
                )
    
    def call_query_decomposer(self, state: SearchAgentState):
        """Calls the LLM model (query_decomposer)."""
        print("--- Calling query_decomposer ---")
        messages = state["messages"]
        if not isinstance(messages[0], SystemMessage):
            current_messages = [SystemMessage(content=self.system_query_decomposer)] + messages
        else:
            current_messages = messages

        original_response = self.model_query_decomposer.invoke(current_messages)

        response_with_metadata = self._create_ai_message(original_response, sender="DecomposerAgent", type_message="HumanMessage")
        print(f"Query_decomposer response: {response_with_metadata}")
        return {"messages": [response_with_metadata]}

    def call_researcher(self, state: SearchAgentState):
        """Calls the LLM model (researcher_node)."""
        print("--- Calling researcher_node ---")
        messages = state["messages"]
        # Add system prompt at the beginning if it's not already implicitly there
        # (Some models/frameworks handle this differently)
        # To be sure, we can check the first message.
        if not isinstance(messages[0], SystemMessage):
             current_messages = [SystemMessage(content=self.system_researcher)] + messages
        else:
             current_messages = messages

        original_response = self.model_researcher.invoke(current_messages)

        response_with_metadata = self._create_ai_message(original_response, sender="ResearcherAgent", type_message="AIMessage")
        return {"messages": [response_with_metadata]}

    def call_tool(self, state: SearchAgentState):
        """Executes tool calls requested by the researcher_node."""
        print("--- Calling Tool Node ---")
        last_message = state["messages"][-1]
        tool_calls = last_message.tool_calls
        print(f"Requested tool calls: {tool_calls}")

        results_messages = []
        for tool_call in tool_calls:
            tool_name = tool_call['name']
            args = tool_call['args']
            print(f"Executing tool: {tool_name} with args: {args}")

            result_content = ""

            try:
                if tool_name == web_scraper_tool.name:
                    self.web_scraper_calls += 1
                    if self.web_scraper_calls > 3:
                        print("Scraper call limit reached.")
                        result_content = "Call limit (3) to web_scraper_tool reached for this query."
                    else:
                        urls_arg = args.get('urls_tuple')
                        if urls_arg is None:
                             urls_arg = args.get('urls')

                        if not urls_arg or not isinstance(urls_arg, list) or len(urls_arg) == 0:
                            result_content = "Error: No valid URL was provided to the web_scraper_tool. Argument 'urls_tuple' missing or empty."
                            print(result_content)
                        else:
                            urls_tuple_for_cache = tuple(urls_arg)
                            print(f"Calling cached_web_scraper with key tuple: {urls_tuple_for_cache}")
                            raw_scraped_content = cached_web_scraper(urls_tuple_for_cache)
                            print(f"Raw scraping result (truncated): {raw_scraped_content[:200]}...")

                            if len(raw_scraped_content) > MAX_TOOL_MSG_LENGTH:
                                print(f"Scraped content too long ({len(raw_scraped_content)} chars), truncating to {MAX_TOOL_MSG_LENGTH}.")
                                result_content = raw_scraped_content[:MAX_TOOL_MSG_LENGTH] + f"\n\n[... Truncated content ({len(raw_scraped_content) - MAX_TOOL_MSG_LENGTH} characters omitted) ...]"
                            else:
                                result_content = raw_scraped_content
                            print(f"Final content for ToolMessage (truncated): {result_content[:500]}...")

                elif tool_name == duckduckgo_tool.name or tool_name == 'duckduckgo_results_json':
                    query_arg = args.get('query', '')
                    if not query_arg:
                         result_content = "Error: Search query ('query') missing for duckduckgo_tool."
                         print(result_content)
                    else:
                        raw_search_result = duckduckgo_tool.invoke(query_arg)
                        print(f"Raw search result (truncated): {raw_search_result[:200]}...")

                        if len(raw_search_result) > MAX_SEARCH_MSG_LENGTH:
                            print(f"Search result too long ({len(raw_search_result)} chars), truncating...")
                            result_content = raw_search_result[:MAX_SEARCH_MSG_LENGTH] + "\n[... Truncated results ...]"
                        else:
                            result_content = raw_search_result
                        print(f"Final search result for ToolMessage (truncated): {result_content[:500]}...")

                else:
                    result_content = f"Error: Unknown tool '{tool_name}' requested."
                    print(result_content)

            except Exception as e:
                 print(f"Error during execution of tool {tool_name}: {e}")
                 result_content = f"Internal error during tool call {tool_name}: {str(e)}"

            results_messages.append(ToolMessage(
                content=result_content,
                tool_call_id=tool_call['id']
            ))

        return {"messages": results_messages}


    def exists_action(self, state: SearchAgentState):
        """Checks if the last message contains tool calls."""
        print("--- Checking Tool Action ---")
        last_message = state["messages"][-1]
        has_tool_calls = hasattr(last_message, 'tool_calls') and len(last_message.tool_calls) > 0
        print(f"Tool calls present: {has_tool_calls}")
        return has_tool_calls


    def run(self, query: str, config=None) -> str:
        """
        Runs the search agent with a given query and returns the final response.
        """
        print(f"--- STARTING NEW SEARCH ---")
        print(f"Initial query: {query}")
        self.web_scraper_calls = 0
        initial_state = {"messages": [HumanMessage(content=query)]}

        # Invoke the graph
        # Using stream to see the steps can be useful for debugging:
        # for event in self.graph.stream(initial_state, config=config):
        #     print(event)
        # Or invoke to directly get the final state:
        final_state = self.graph.invoke(initial_state, config=config)

        print("--- SEARCH COMPLETED ---")
        final_message = final_state["messages"][-1]
        if isinstance(final_message, SystemMessage):
            for msg in reversed(final_state["messages"]):
                if msg.type not in ["system", "tool"]:
                    final_message = msg
                    break

        # return "No response generated."
        return final_message.content if final_message else "No response generated."


if __name__ == "__main__":
    from langchain_mistralai import ChatMistralAI
    from langchain_google_genai import ChatGoogleGenerativeAI
    import os
    from dotenv import load_dotenv

    load_dotenv()

    # Make sure the API key is available
    # if not os.getenv("MISTRAL_API_KEY"):
    #     print("Error: The MISTRAL_API_KEY environment variable is not defined.")
    if not os.getenv("GOOGLE_API_KEY"):
        print("Error: The GOOGLE_API_KEY environment variable is not defined.")
    else:
        # model = ChatMistralAI(model="mistral-large-latest", temperature=0)
        model = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0, google_api_key=os.getenv("GOOGLE_API_KEY"))
        search_agent_instance = SearchAgent(model)

        # Example query
        # query = "What are the advantages and disadvantages of LangGraph for building LLM agents compared to a simple sequential approach?"
        # query = "Give me the latest news on NASA's Artemis mission."
        # query = "Explain the concept of 'Retrieval-Augmented Generation' (RAG) and why it's important for LLMs."
        # query = "how does Google provide relevant results when typing a query"
        query = "how to create a projection matrix to view vectors in a vector space?"
        try:
            final_response = search_agent_instance.run(query)
            print("--- Final Agent Response ---")
            # Writing the response to a Markdown file
            print(final_response)
            filename = f"../../requetes_md/reponse_{query[:30].replace(' ', '_')}.md"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"# Response to query: {query}\n\n")
                for item in final_response:
                    f.write(item)
            print(f"The response has been saved to file: {filename}")
        except Exception as e:
            print(f"An error occurred while running the agent: {e}")

        # # Example with a second query to verify counter reset
        # print("--- TESTING SECOND QUERY ---")
        # query2 = "What is dark energy?"
        # try:
        #     final_response2 = search_agent_instance.run(query2)
        #     print("-- Final Agent Response (Query 2) ---")
        #     print(final_response2)
        # except Exception as e:
        #     print(f"An error occurred while running the agent's second query: {e}")


