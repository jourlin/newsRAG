# PATCHAT : a simple Retrieval-Augmented Generation AI System for news content Analysis

**(c) Pierre Jourlin**
__Avignon University__
__Laboratoire d’informatique d’Avignon (LIA)__
__September 22, 2024__

# Quick Start Document

## Overview
The proposed project aims to develop a Retrieval-Augmented Generation (RAG) AI system designed to simplify information extraction from RSS feeds. The system leverages :
- LLMs for entity extraction on titles, abstracts and image captions for initial query expansion
- The LlamaIndex Python framework and the various Large Language model (LLM) for natural language "understanding" and generation
- a document set composed of news feeds. As the original user's query can be short and somehow fuzzy, it can be expanded by searching for most relevant Wikipedia entities. At that 1st stage, the user has a chance to desambiguate query terms. 

The primary function of the system is to identify and present the most relevant news information that closely match the user's query. 
The secondary function of the system is to provide a chatbot to question the information contained in the selected news information. The chatbot can be used to ask open-ended questions in natural language, which can correspond to classic tasks such as automatic summarization, comparisons of several news from different angles, etc. The chatbot takes into account the history of the conversation, making it easier to refine the initial query.
(more information in [USER_GUIDE.md](/docs/USER_GUIDE.md))

## Installation
See [INSTALL.md](/docs/INSTALL.md)

## Test
See [USER_GUIDE.md](/docs/USER_GUIDE.md)

## Files short descriptions
See [FILES_DESC.md](/docs/FILES_DESC.md)



