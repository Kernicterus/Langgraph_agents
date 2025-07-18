from langchain_core.messages import BaseMessage, AIMessage
from typing import Literal, Any, Dict, List, Union


class ReviewerMessage(AIMessage):
    """Reviewer message"""
    
    type: Literal["reviewer"] = "reviewer"
    
    def __init__(
        self, 
        content: Union[str, List[Union[str, Dict]]], 
        **kwargs: Any
    ) -> None:
        super().__init__(content=content, **kwargs)

    def pretty_repr(self, html: bool = False) -> str:
        """Personalized representation of the message"""
        base = super().pretty_repr(html=html)
        review_info = f"\n Reviewer: {self.content}"
        return base + review_info
    
    def to_ai_message(self) -> AIMessage:
        """Convert to standard AIMessage for model compatibility"""
        return AIMessage(
            content=self.content,
            additional_kwargs=self.additional_kwargs,
            response_metadata=self.response_metadata,
            id=self.id
        )


class ArchitectMessage(AIMessage):
    """Architect message"""
    
    type: Literal["architect"] = "architect"
    
    def __init__(
        self, 
        content: Union[str, List[Union[str, Dict]]], 
        **kwargs: Any
    ) -> None:
        super().__init__(content=content, **kwargs)

    def pretty_repr(self, html: bool = False) -> str:
        """Personalized representation of the message"""
        base = super().pretty_repr(html=html)
        arch_info = f"\n Architecture: {self.content}"
        return base + arch_info
    
    def to_ai_message(self) -> AIMessage:
        """Convert to standard AIMessage for model compatibility"""
        return AIMessage(
            content=self.content,
            additional_kwargs=self.additional_kwargs,
            response_metadata=self.response_metadata,
            id=self.id
        )


class GDPRMessage(AIMessage):
    """GDPR message"""
    
    type: Literal["gdpr"] = "gdpr"
    
    def __init__(
        self, 
        content: Union[str, List[Union[str, Dict]]], 
        **kwargs: Any
    ) -> None:
        super().__init__(content=content, **kwargs)

    def pretty_repr(self, html: bool = False) -> str:
        """Personalized representation of the message"""
        base = super().pretty_repr(html=html)
        gdpr_info = f"\n GDPR: {self.content}"
        return base + gdpr_info
    
    def to_ai_message(self) -> AIMessage:
        """Convert to standard AIMessage for model compatibility"""
        return AIMessage(
            content=self.content,
            additional_kwargs=self.additional_kwargs,
            response_metadata=self.response_metadata,
            id=self.id
        )


class SecurityMessage(AIMessage):
    """Security message"""
    
    type: Literal["security"] = "security"
    
    def __init__(
        self, 
        content: Union[str, List[Union[str, Dict]]], 
        **kwargs: Any
    ) -> None:
        super().__init__(content=content, **kwargs)

    def pretty_repr(self, html: bool = False) -> str:
        """Personalized representation of the message"""
        base = super().pretty_repr(html=html)
        security_info = f"\n Security: {self.content}"
        return base + security_info
    
    def to_ai_message(self) -> AIMessage:
        """Convert to standard AIMessage for model compatibility"""
        return AIMessage(
            content=self.content,
            additional_kwargs=self.additional_kwargs,
            response_metadata=self.response_metadata,
            id=self.id
        )


def convert_messages_for_model(messages: List[BaseMessage]) -> List[BaseMessage]:
    """
    Convertit les messages personnalisés en messages standards pour compatibilité avec les modèles
    """
    converted_messages = []
    for message in messages:
        if hasattr(message, 'to_ai_message'):
            converted_messages.append(message.to_ai_message())
        else:
            converted_messages.append(message)
    return converted_messages