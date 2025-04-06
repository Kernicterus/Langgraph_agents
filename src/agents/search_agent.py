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
    Scrape le contenu des URLs fournies (sous forme de tuple) et retourne le contenu sous forme de chaîne unique.
    Args:
        urls_tuple: Tuple d'URLs à scraper.
    Returns:
        str: Contenu textuel extrait des pages web, séparé par des marqueurs.
    """
    urls = list(urls_tuple)
    if not urls:
        return "La liste d'URLs fournie est vide."

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
                print(f"Avertissement: Aucun contenu HTML pour l'URL {source_url}")
                continue

            soup = BeautifulSoup(html_content, "html.parser")

            article = soup.find("article") or soup.find("main") or soup.body

            if not article:
                print(f"Avertissement: Impossible de trouver la balise de contenu principal pour l'URL {source_url}")
                continue

            for tag in article.find_all(["script", "style", "header", "footer", "nav",
                                       "aside", "form", "noscript", "iframe", "img", "button"]):
                tag.decompose()

            content_tags = article.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p",
                                           "ul", "ol", "li", "blockquote", "td", "th"])
            cleaned_text = "".join([tag.get_text(separator=' ', strip=True) for tag in content_tags])
            cleaned_text = "".join(line for line in cleaned_text.splitlines() if line.strip())


            if cleaned_text.strip():
                all_contents.append(f"--- Contenu de {source_url} ---\n{cleaned_text}")
                scraped_urls.append(source_url)
            else:
                print(f"Avertissement: Aucun texte utile extrait de {source_url} après nettoyage.")


        if not all_contents:
            return "Aucun contenu valide n'a pu être extrait des URLs fournies."

        print(f"--- Scraping réussi pour {len(scraped_urls)} URLs ---")
        return "---\n".join(all_contents)

    except Exception as e:
        print(f"Erreur lors du scraping des URLs: {urls}. Erreur: {e}")
        return f"Erreur lors du scraping des URLs: {str(e)}"


@lru_cache(maxsize=30)
def cached_web_scraper(urls_tuple: tuple) -> str:
    """
    Version mise en cache du web scraper qui utilise un tuple d'URLs comme clé.
    """
    return web_scraper_tool.invoke({"urls_tuple": urls_tuple})


prompt_search_agent_v3 = """
Tu es un agent de chat spécialisé dans la collecte d'informations et la recherche sur le web. Ton objectif est de fournir une réponse complète et bien sourcée à la requête de l'utilisateur.

Voici ton processus de travail :

1.  **Comprendre la Requête** : Analyse attentivement les sous requetes. Utilise l'outil `DuckDuckGoSearchResults` pour trouver des informations pertinentes sur le sujet ou les sous-questions.
3.  **Analyse et Sélection** : Examine les résultats de la recherche (titres, snippets). Identifie les **3 URLs maximum** qui semblent les plus prometteuses et pertinentes pour fournir une information détaillée et fiable répondant à la requête initiale. Si aucun résultat ne semble pertinent, indique-le.
4.  **Scraping Ciblé** : Parmi les URLs pertinentes, utilise l'outil `web_scraper_tool` **UNIQUEMENT** avec le tuple de ces URLs sélectionnées (maximum 3) pour en extraire le contenu détaillé. N'appelle cet outil que si tu as des URLs valides et pertinentes issues de la recherche. Assure-toi de passer l'argument `urls_tuple` correctement.
5.  **Synthèse et Réponse** : Combine les informations issues des snippets de recherche et du contenu scrapé (si disponible) pour formuler une réponse complète, cohérente et structurée à la requête initiale de l'utilisateur sous format markdown.
6.  **Citation des Sources** : À la fin de ta réponse, liste clairement toutes les URLs que tu as effectivement utilisées via l'outil `web_scraper_tool` pour obtenir l'information. Si tu n'as utilisé que les snippets de recherche, mentionne-le, liste les urls et explique pourquoi tu n'as pas utilisé l'outil `web_scraper_tool`.
7.  **Gestion des Limites** : Si l'information est incomplète, si certaines URLs n'ont pas pu être scrapées, ou si tu atteins la limite d'appels au scraper, signale-le à l'utilisateur. Tu ne peux utiliser l'outil `web_scraper_tool` que 3 fois par requête utilisateur complète.

Sois méthodique, précis et transparent sur ton processus et tes sources. N'hésite pas à indiquer si tu manques d'informations sur certains points. 
N'extrapole pas de réponse qui n'est pas dans les sources.
N'oublie pas de mettre en forme ta réponse en markdown.
Reflechis étape par étape avant de répondre.
"""

prompt_query_decomposer = """
Tu es un agent spécialisé dans l'analyse et la décomposition de requêtes complexes. Ta mission est de :

1. **Analyser la requête initiale** de l'utilisateur pour identifier les différents aspects et angles qui méritent d'être explorés.

2. **Décomposer la requête en sous-questions** plus spécifiques et ciblées qui, ensemble, permettront de construire une réponse complète.
   - Chaque sous-question doit être autonome et précise
   - Évite les redondances entre les sous-questions
   - Limite-toi à 3 sous-questions maximum pour rester efficace
   - N'extrapole pas trop de sous-questions, tu dois rester concentré sur la requête initiale.

3. **Transmettre le tout** au node suivant sous forme d'une liste structurée en markdown avec les sous-questions numérotées


Exemple de format de réponse :

# Sous-questions :
1. Première sous-question
2. Deuxième sous-question
3. Troisième sous-question

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
        """Crée un message AI avec les métadonnées appropriées."""
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
        """Appelle le modèle LLM (query_decomposer)."""
        print("--- Appel query_decomposer ---")
        messages = state["messages"]
        if not isinstance(messages[0], SystemMessage):
            current_messages = [SystemMessage(content=self.system_query_decomposer)] + messages
        else:
            current_messages = messages

        original_response = self.model_query_decomposer.invoke(current_messages)

        response_with_metadata = self._create_ai_message(original_response, sender="DecomposerAgent", type_message="HumanMessage")
        print(f"Réponse du query_decomposer: {response_with_metadata}")
        return {"messages": [response_with_metadata]}

    def call_researcher(self, state: SearchAgentState):
        """Appelle le modèle LLM (researcher_node)."""
        print("--- Appel researcher_node ---")
        messages = state["messages"]
        # Ajoute le prompt système au début s'il n'y est pas déjà implicitement
        # (Certains modèles/frameworks le gèrent différemment)
        # Pour être sûr, on peut vérifier le premier message.
        if not isinstance(messages[0], SystemMessage):
             current_messages = [SystemMessage(content=self.system_researcher)] + messages
        else:
             current_messages = messages

        original_response = self.model_researcher.invoke(current_messages)

        response_with_metadata = self._create_ai_message(original_response, sender="ResearcherAgent", type_message="AIMessage")
        return {"messages": [response_with_metadata]}

    def call_tool(self, state: SearchAgentState):
        """Exécute les appels aux outils demandés par le researcher_node."""
        print("--- Appel Noeud Outil ---")
        last_message = state["messages"][-1]
        tool_calls = last_message.tool_calls
        print(f"Appels outils demandés: {tool_calls}")

        results_messages = []
        for tool_call in tool_calls:
            tool_name = tool_call['name']
            args = tool_call['args']
            print(f"Exécution outil: {tool_name} avec args: {args}")

            result_content = ""

            try:
                if tool_name == web_scraper_tool.name:
                    self.web_scraper_calls += 1
                    if self.web_scraper_calls > 3:
                        print("Limite d'appels au scraper atteinte.")
                        result_content = "Limite d'appels (3) à l'outil web_scraper_tool atteinte pour cette requête."
                    else:
                        urls_arg = args.get('urls_tuple')
                        if urls_arg is None:
                             urls_arg = args.get('urls')

                        if not urls_arg or not isinstance(urls_arg, list) or len(urls_arg) == 0:
                            result_content = "Erreur: Aucune URL valide n'a été fournie à l'outil web_scraper_tool. Argument 'urls_tuple' manquant ou vide."
                            print(result_content)
                        else:
                            urls_tuple_for_cache = tuple(urls_arg)
                            print(f"Appel cached_web_scraper avec tuple clé: {urls_tuple_for_cache}")
                            raw_scraped_content = cached_web_scraper(urls_tuple_for_cache)
                            print(f"Résultat scraping brut (tronqué): {raw_scraped_content[:200]}...")

                            if len(raw_scraped_content) > MAX_TOOL_MSG_LENGTH:
                                print(f"Contenu scrapé trop long ({len(raw_scraped_content)} chars), troncation à {MAX_TOOL_MSG_LENGTH}.")
                                result_content = raw_scraped_content[:MAX_TOOL_MSG_LENGTH] + f"\n\n[... Contenu tronqué ({len(raw_scraped_content) - MAX_TOOL_MSG_LENGTH} caractères omis) ...]"
                            else:
                                result_content = raw_scraped_content
                            print(f"Contenu final pour ToolMessage (tronqué): {result_content[:500]}...")

                elif tool_name == duckduckgo_tool.name or tool_name == 'duckduckgo_results_json':
                    query_arg = args.get('query', '')
                    if not query_arg:
                         result_content = "Erreur: Requête de recherche ('query') manquante pour duckduckgo_tool."
                         print(result_content)
                    else:
                        raw_search_result = duckduckgo_tool.invoke(query_arg)
                        print(f"Résultat recherche brut (tronqué): {raw_search_result[:200]}...")

                        if len(raw_search_result) > MAX_SEARCH_MSG_LENGTH:
                            print(f"Résultat recherche trop long ({len(raw_search_result)} chars), troncation...")
                            result_content = raw_search_result[:MAX_SEARCH_MSG_LENGTH] + "\n[... Résultats tronqués ...]"
                        else:
                            result_content = raw_search_result
                        print(f"Résultat recherche final pour ToolMessage (tronqué): {result_content[:500]}...")

                else:
                    result_content = f"Erreur: Outil inconnu '{tool_name}' demandé."
                    print(result_content)

            except Exception as e:
                 print(f"Erreur lors de l'exécution de l'outil {tool_name}: {e}")
                 result_content = f"Erreur interne lors de l'appel de l'outil {tool_name}: {str(e)}"

            results_messages.append(ToolMessage(
                content=result_content,
                tool_call_id=tool_call['id']
            ))

        return {"messages": results_messages}


    def exists_action(self, state: SearchAgentState):
        """Vérifie si le dernier message contient des appels d'outils."""
        print("--- Vérification Action Outil ---")
        last_message = state["messages"][-1]
        has_tool_calls = hasattr(last_message, 'tool_calls') and len(last_message.tool_calls) > 0
        print(f"Appels outils présents: {has_tool_calls}")
        return has_tool_calls


    def run(self, query: str, config=None) -> str:
        """
        Exécute l'agent de recherche avec une requête donnée et retourne la réponse finale.
        """
        print(f"--- DÉMARRAGE NOUVELLE RECHERCHE ---")
        print(f"Requête initiale: {query}")
        self.web_scraper_calls = 0
        initial_state = {"messages": [HumanMessage(content=query)]}

        # Invoque le graphe
        # Utiliser stream pour voir les étapes peut être utile pour le débogage:
        # for event in self.graph.stream(initial_state, config=config):
        #     print(event)
        # Ou invoke pour obtenir directement l'état final:
        final_state = self.graph.invoke(initial_state, config=config)

        print("--- RECHERCHE TERMINÉE ---")
        final_message = final_state["messages"][-1]
        if isinstance(final_message, SystemMessage):
            for msg in reversed(final_state["messages"]):
                if msg.type not in ["system", "tool"]:
                    final_message = msg
                    break

        # return "Aucune réponse générée."
        return final_message.content if final_message else "Aucune réponse générée."


if __name__ == "__main__":
    from langchain_mistralai import ChatMistralAI
    from langchain_google_genai import ChatGoogleGenerativeAI
    import os
    from dotenv import load_dotenv

    load_dotenv()

    # Assure-toi que la clé API est disponible
    # if not os.getenv("MISTRAL_API_KEY"):
    #     print("Erreur: La variable d'environnement MISTRAL_API_KEY n'est pas définie.")
    if not os.getenv("GOOGLE_API_KEY"):
        print("Erreur: La variable d'environnement GOOGLE_API_KEY n'est pas définie.")
    else:
        # model = ChatMistralAI(model="mistral-large-latest", temperature=0)
        model = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0, google_api_key=os.getenv("GOOGLE_API_KEY"))
        search_agent_instance = SearchAgent(model)

        # Requête d'exemple
        # query = "Quels sont les avantages et inconvénients de LangGraph pour construire des agents LLM comparé à une approche séquentielle simple ?"
        # query = "Donne-moi les dernières nouvelles sur la mission Artemis de la NASA."
        # query = "Explique le concept de 'Retrieval-Augmented Generation' (RAG) et pourquoi c'est important pour les LLMs."
        # query = "comment fait google pour proposer des resultats pertinents lorsque l'on tape une requête"
        query = "comment faire une matrice de projection pour voir des vecteurs dans un espace vectoriel ?"
        try:
            final_response = search_agent_instance.run(query)
            print("--- Réponse Finale de l'Agent ---")
            # Écriture de la réponse dans un fichier Markdown
            print(final_response)
            filename = f"../../requetes_md/reponse_{query[:30].replace(' ', '_')}.md"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"# Réponse à la requête: {query}\n\n")
                for item in final_response:
                    f.write(item)
            print(f"La réponse a été sauvegardée dans le fichier: {filename}")
        except Exception as e:
            print(f"Une erreur est survenue lors de l'exécution de l'agent: {e}")

        # # Exemple avec une deuxième requête pour vérifier la réinitialisation du compteur
        # print("--- TEST SECONDE REQUÊTE ---")
        # query2 = "Qu'est-ce que l'énergie sombre ?"
        # try:
        #     final_response2 = search_agent_instance.run(query2)
        #     print("-- Réponse Finale de l'Agent (Requête 2) ---")
        #     print(final_response2)
        # except Exception as e:
        #     print(f"Une erreur est survenue lors de l'exécution de la seconde requête de l'agent: {e}")


