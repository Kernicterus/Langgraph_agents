"""
Exemple d'utilisation des messages personnalisés dans le workflow
"""

from src.utils.custom_messages import ReviewerMessage, ArchitectMessage, GDPRMessage, AgentMessage, MetricMessage
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from typing import List, BaseMessage
import time


def exemple_workflow_avec_messages_personnalises():
    """Démontre l'utilisation des messages personnalisés"""
    
    # 1. Message initial de l'utilisateur
    user_message = HumanMessage(
        content="Je veux créer une application de e-commerce avec gestion des données personnelles"
    )
    
    # 2. Réponse de l'architecte avec métadonnées spécialisées
    start_time = time.time()
    architect_response = ArchitectMessage(
        content="Voici l'architecture recommandée pour votre application e-commerce...",
        architecture_type="hexagonale",
        technologies=["React", "Node.js", "PostgreSQL", "Redis"],
        complexity_level="élevée",
        processing_time=time.time() - start_time
    )
    
    # 3. Analyse GDPR avec informations spécialisées
    gdpr_analysis = GDPRMessage(
        content="Analyse de conformité GDPR pour l'application e-commerce...",
        compliance_level="partiellement conforme",
        identified_risks=[
            "Stockage des données de paiement",
            "Cookies de tracking",
            "Partage avec partenaires"
        ],
        recommendations=[
            "Implémenter l'anonymisation",
            "Ajouter gestion des consentements",
            "Créer API pour droit à l'effacement"
        ]
    )
    
    # 4. Révision avec note et commentaires
    review_message = ReviewerMessage(
        content="L'architecture proposée est solide mais nécessite quelques améliorations...",
        note=75,
        reviewer_name="Expert Sénior",
    )
    
    # 5. Message d'agent avec métriques
    agent_response = AgentMessage(
        content="Analyse terminée avec succès",
        agent_name="GlobalWorkflowAgent",
        agent_version="2.1",
        processing_time=2.345,
        confidence_score=0.87
    )
    
    # 6. Métriques de performance
    metrics = MetricMessage(
        content="Rapport de performance du workflow",
        tokens_used=1250,
        cost_estimate=0.0125,
        response_quality="excellent"
    )
    
    # Affichage des messages avec leurs représentations personnalisées
    messages = [
        user_message,
        architect_response,
        gdpr_analysis,
        review_message,
        agent_response,
        metrics
    ]
    
    print("=== EXEMPLE D'UTILISATION DES MESSAGES PERSONNALISÉS ===\n")
    
    for i, message in enumerate(messages, 1):
        print(f"📝 MESSAGE {i} ({message.type.upper()})")
        print(message.pretty_repr())
        print("\n" + "="*60 + "\n")


def integration_avec_workflow_existant():
    """Montre comment intégrer les messages personnalisés dans le workflow existant"""
    
    # Simulation d'une réponse d'architecte améliorée
    def architect_node_ameliore(state):
        # Logique existante...
        response_content = "Architecture hexagonale recommandée..."
        
        # Création d'un message personnalisé au lieu d'AIMessage
        architect_message = ArchitectMessage(
            content=response_content,
            architecture_type="hexagonale",
            technologies=["FastAPI", "PostgreSQL", "Redis", "React"],
            complexity_level="moyenne"
        )
        
        return {"messages": [architect_message]}
    
    # Simulation d'une révision améliorée
    def review_node_ameliore(state):
        # Logique existante de révision...
        note = 85
        comment = "Excellente architecture, quelques améliorations mineures suggérées"
        
        # Message de révision personnalisé
        review_message = ReviewerMessage(
            content=comment,
            note=note,
            reviewer_name="ArchitectReviewer"
        )
        
        return {"messages": [review_message], "note": note}
    
    print("=== INTÉGRATION DANS LE WORKFLOW EXISTANT ===\n")
    print("Les messages personnalisés peuvent remplacer les AIMessage standard")
    print("tout en conservant la compatibilité avec LangGraph.\n")


def avantages_messages_personnalises():
    """Explique les avantages des messages personnalisés"""
    
    print("=== AVANTAGES DES MESSAGES PERSONNALISÉS ===\n")
    
    avantages = [
        "🎯 **Typage fort** : Chaque type de message a ses propres propriétés",
        "📊 **Métadonnées riches** : Stockage d'informations contextuelles",
        "🔍 **Traçabilité** : Suivi détaillé des étapes du workflow",
        "📝 **Debugging facilité** : Représentations visuelles améliorées",
        "🔧 **Extensibilité** : Ajout facile de nouvelles propriétés",
        "📈 **Métriques** : Collecte automatique de données de performance",
        "🎨 **Personnalisation** : Affichage adapté à chaque type de message"
    ]
    
    for avantage in avantages:
        print(avantage)
    
    print("\n=== COMPATIBILITÉ ===")
    print("✅ Compatible avec tous les outils LangChain existants")
    print("✅ Fonctionne avec LangGraph sans modification")
    print("✅ Supporte la sérialisation/désérialisation")
    print("✅ Intégration transparente avec les LLMs")


if __name__ == "__main__":
    exemple_workflow_avec_messages_personnalises()
    integration_avec_workflow_existant()
    avantages_messages_personnalises() 