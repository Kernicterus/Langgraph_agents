# LangGraph Agents Project

## Project Overview

This project demonstrates the implementation of intelligent agents using LangGraph and LangChain frameworks. The system consists of three specialized agents:

1. **Search Agent**: Decomposes complex queries into sub-questions, performs online searches using DuckDuckGo, and scrapes relevant web content to provide comprehensive, well-sourced answers.

2. **Functional Insight Agent**: Analyzes website mockup files (in Markdown format) along with context and architectural requirements provided by users through a Tkinter interface to generate functional specifications for web applications. Includes a Markdown Viewer component for validating outputs.

3. **Architect Agent**: Transforms functional specifications into detailed technical architecture plans, including component structure, data models, and API definitions.

## Features

### Search Agent
- Query decomposition into targeted sub-questions
- Web search integration using DuckDuckGo
- Selective web scraping with BeautifulSoup
- Result synthesis and source citation
- Response caching for performance optimization

### Functional Insight Agent
- Markdown file analysis for web application mockups
- Interactive UI for collecting project context and architectural requirements
- Generation of structured functional specifications
- Export to Markdown for software architecture planning
- Built-in Markdown Viewer for validating and reviewing outputs:
  - Real-time rendering of Markdown documents
  - Interactive navigation between document sections
  - Support for embedded diagrams and code snippets
  - Validation tools for reviewing specification completeness

### Architect Agent
- Analysis of functional specifications
- Generation of technical architecture components
- Design of data models and database schema
- Definition of API endpoints and service interactions
- Integration with existing system components

## Skills Demonstrated

- **Agent Architecture Design**: Implementation of multi-node computational graphs with LangGraph
- **Prompt Engineering**: Creation of specialized system prompts for different agent roles
- **Tool Integration**: Connecting LLMs with external tools for search and web scraping
- **State Management**: Proper handling of agent state through TypedDict
- **Error Handling**: Implementing conditional branches for error cases
- **UI Integration**: Basic Tkinter interface for user input collection and markdown visualization
- **Type Annotations**: Strong typing with Python's typing module
- **File System Operations**: Handling file I/O for various formats
- **API Integration**: Using external AI services (Google Gemini API)
- **Documentation Generation**: Creation of structured technical documentation

## Technical Stack

- Python
- LangGraph / LangChain
- Google Gemini AI API
- BeautifulSoup (web scraping)
- Tkinter (UI)
- DuckDuckGo Search API
- Markdown rendering libraries

