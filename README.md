# NewsRAG: A simple retrieval and retrieval-augmented generative AI chatbot for multilingual RSS content analysis
(c) *Pierre Jourlin*, 2024, _Avignon Université_, _Laboratoire d'informatique d'Avignon (LIA)_

November, 2024

***

Documentation :
* **quick installation or use**, see [QUICK_START.md](/docs/QUICK_START.md).
* **local installation**, see [INSTALL.md](/docs/INSTALL.md).
* **user instructions**, see [USER_GUIDE.md](/docs/USER_GUIDE.md).
* **developper documentation**, see [DEVELOPPER_GUIDE.md](/docs/DEVELOPPER_GUIDE.md).
* **files description**, see [FILES_DESC.md](/docs/FILES_DESC.md).
* **Licence**, see [LICENSE.md](/docs/LICENSE.md).
***

# Functionalities 

The proposed project aims to develop a Retrieval-Augmented Generation (RAG) AI system designed to simplify information extraction from RSS feeds. The system leverages :
- LLMs for entity extraction on titles, abstracts and image captions for initial query expansion
- The LlamaIndex Python framework and the various Large Language model (LLM) for natural language "understanding" and generation
- a document set composed of news feeds. As the original user's query can be short and somehow fuzzy, it can be expanded by searching for most relevant Wikipedia entities. At that 1st stage, the user has a chance to desambiguate query terms. 

The primary function of the system is to identify and present the most relevant news information that closely match the user's query. 
The secondary function of the system is to provide a chatbot to question the information contained in the selected news information. The chatbot can be used to ask open-ended questions in natural language, which can correspond to classic tasks such as automatic summarization, comparisons of several news from different angles, etc. The chatbot takes into account the history of the conversation, making it easier to refine the initial query.
(more information in [USER_GUIDE.md](/docs/USER_GUIDE.md))

# Justification of technical choices

The choice of _language models_ significantly determines the quality of the vector representation (word embeddings) of text frames, in their context of occurrence, and therefore the quality of the prediction of new _tokens_ (words or their morphological components). In fact, this vector representation is much closer to a _semantic_ representation than much older but still predominant natural language processing approaches for information retrieval, such as boolean models for keyword matching or even the slightly more recent _probabilistic models_ (TF/IDF, BM25/Okapi). Nevertheless, they rely entirely on a _learning_ stage on a pre-defined text corpus. We can therefore expect a _general_ model to perform less well on a specific domain, and vice versa: a model that has been fine-tuned on a specific domain will perform less well than a general model on domains other than the one targeted by the fine-tuning. This version make use of a general, multilingual model for word emmbedding.

## An easy thematic generalization

**newsRAG** can easily be adapted to other domains. All you need to do is to choose a suitable model (see [HuggingFace](https://huggingface.co/blog/getting-started-with-embeddings)) by modifying the environment variable ``MODEL_NAME`` in the file [.env](/src/.env)

## Low energy consumption, low carbon impact

All software functionalities have been successfully tested on a __orange pi 5 pro__ device, with the following specifications :
- Rockchip RK3588S 8-core 64-bit CPU, max 2.4GHz
- No GPU
- LPDDR5 RAM: 16GB
- NVMe SSD: 250Gb
- max power consumption: 9W

![Minimal setup](docs/images/SetupOPI.jpeg)

With such a configuration, response times are admittedly too slow to offer a good quality user experience, but the software remains functional.

## A software designed for educational purposes

This is a small, highly demonstrative, yet reasonably simple system that could be used in an educational context. Indeed, by opting for the use of open-source software architectures (Python, Deeplake, Huggingface, Lllama3, Ollama, LlamaIndex, Flask, etc.) and a high level of abstraction, I was able to keep to a minimum the number of lines of code needed to obtain a **complete**, **high-performance** and **efficient** application, and above all one that was easily **transferable**, **easy to develop** and maintain.

Furthermore, the **efficiency** is such that the software was developped and tested on a mid-range laptop computer with 1Tb SSD, 32Gb RAM and 6Gb VRAM GPU. With such a configuration, response times are short enough to deliver a high-quality user experience. In some applications were **security** and **confidentality** is a major issue, it is worth noting that the software can **run offline** and smoothly on a entry-level **gaming computer**. So even for the longuest stages such as indexing, the **electrical consumption** and **ecological impact** is mitigated. 

73% of code is written in Python using the Flask module. It's a language that is now widely taught, including in continuing education and in disciplines other than computer science. Other languages, even if justified by the presence of a web interface or, to a lesser extent, the pre-processing of raw data, account for a small proportion of the code:
- JavaScript 19%
- HTML 4%
- CSS 3.5%

Finally, the algorithms involved are complex, but it is possible to explain them simply, although this is not the purpose of this document:
- tokenization
- word/sentence/document embbedings
- k-nearest neighbor search
- artificial neural networks
- transformers & attention masks
- predictive and generative models

## A streamlined interface

I've opted for a clean, intuitive interface. 

It has only 2 possible entries:
- a text field for queries
- a _file_ field for similarity searches

There is only 3 possible actions that take into account the history of use of the web application:

- Query extension by adding automatically extracted concepts to compensate for the user's implicit intentions
- News search, with display of meta-data present in the document, as well as AI-generated fields
- Chatbot, with _streaming_ display, minimizing user waiting time, and _a posteriori_ formatting, facilitating export (by copy-paste) of Llama3 responses.
