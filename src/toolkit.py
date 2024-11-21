""" toolkit.py : NewsRAG main code

    Copyright (C) 2024 Pierre Jourlin

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as
    published by the Free Software Foundation, either version 3 of the
    License, or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
import os 
import sys
import re
from tqdm import tqdm
from markdown import markdown
import feedparser
import xmltodict
import base64 
from urllib.parse import urlparse
import json
from json2html import json2html

import deeplake
import lxml.etree as ET
from html2text import html2text
from llama_index.core import Settings, SimpleDirectoryReader, VectorStoreIndex, StorageContext
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.ollama import Ollama
from llama_index.core.llms import ChatMessage
from llama_index.vector_stores.deeplake import DeepLakeVectorStore
from llama_index.core.memory import ChatMemoryBuffer

# pattern for matching ENT IDs
concept_pattern = re.compile("^c[0-9]+$")
# pattern for SQL-formatted dates
date_pattern = re.compile("^[0-9]{8}$")
# Ai generated field names and associated prompts
ai_generated_prompts = {
    "entities" : ["Entités", "Extrait un objet JSON contenant la liste (champ 'entités') des entitées nommées (champ 'Nom') associées à leur description (champ 'Description').  : "]
}
# XML field and how to access them
xml_extraction_data = [
    {
        "name": "title",                         # Title
        "display": "Titre",
        "path": "/article/title/text()",
        "position": 0,
    },
    {
        "name": "day",                          # day
        "path": "/article/published_parsed/text()",
        "position": 2,
    },
    {
        "name": "month",                          # month
        "path": "/article/published_parsed/text()",
        "position": 1,
    },
    {
        "name": "year",                          # year
        "path": "/article/published_parsed/text()",
        "position": 0,
    },
    {
        "name": "summary",                          # summary
        "display": "Résumé",
        "path": "/article/summary/text()",
        "position": 0,
    },
    {
        "name": "link",                          # link
        "path": "/article/link/text()",
        "position": 0,
    },
    {
        "name": "caption",                          # image caption
        "display": "Illustration",
        "path": "/article/content/value/text()",
        "position": 0,
    }
]

class Toolkit:
    """
    Toolkit is the main structure for handling HF embeddings, 
    Ollama, Deeplake & LlamaIndex
    Note : Docstrings are formatted for pdoc3
    """
    def __init__(self, read_only=False, index_name="BOTH"):
        """
        Initialise a Toolkit object

        Parameters
        ----------
            read_only : bool
                Should we open the indexes only for search or for creating and populating
            index_name : str
                "EP" stands for full-text patents, "ENT" stands for ENT entities, "BOTH" stands for both indexes
        Returns
        -------
            Toolkit
                A Toolkit object
        """
        # import all configuration values from .env file
        self.query=os.getenv('SEARCH_TERM')
        self.model_name=os.getenv('MODEL_NAME')
        self.doc_limit=int(os.getenv('DOC_LIMIT'))
        self.llm=os.getenv('LLM')
        self.llm_req_timeout=float(os.getenv('LLM_REQ_TIMEOUT'))
        self.token_limit=int(os.getenv('TOKEN_LIMIT'))
        self.url_list=os.getenv('URL_LIST')
        self.document_dir=os.getenv('DOC_DIR')
        self.vector_dir=os.getenv('VEC_DIR')
        self.ent_document_dir=os.getenv('ENT_DOC_DIR')
        self.ent_vector_dir=os.getenv('ENT_VEC_DIR')
        self.table_cells_maxchars=int(os.getenv('TABLE_CELLS_MAXCHARS'))
        self.span_top_k = int(os.getenv('SPAN_TOPK'))
        self.accepted_names = ["NEWS", "WIKI", "BOTH"]

        print("Initializing toolkit...",file=sys.stderr)
        # Get embedding model (used to build vectors from queries and document spans) from HF
        self.embed_model = HuggingFaceEmbedding(
            model_name=self.model_name, trust_remote_code=True
        )
        Settings.embed_model = self.embed_model
        # Tell LlamaIndex to call Ollama for interacting with LLM (e.g. Llama3)
        self.llm_settings = Ollama(model=self.llm, request_timeout=self.llm_req_timeout)
        Settings.llm = self.llm_settings
        # Select one of the available index
        # Check index name validity
        if index_name not in self.accepted_names:
            print(f"Error: '{index_name}' is not a valid index name. Accepted values : {self.accepted_names}", file=sys.stderr)
            sys.exit(-1)
        # Select entities
        if index_name=="WIKI" or index_name=="BOTH":
            # Configure deeplake for entities
            self.ent_vector_store = DeepLakeVectorStore(dataset_path=self.ent_vector_dir)
            self.ent_index = VectorStoreIndex.from_vector_store(vector_store=self.ent_vector_store, streaming=True, read_only=read_only)
            self.ent_storage_context = StorageContext.from_defaults(vector_store=self.ent_vector_store)
        if index_name=="NEWS" or index_name=="BOTH": 
            # Configure deeplake for documents
            self.vector_store = DeepLakeVectorStore(dataset_path=self.vector_dir)
            self.index = VectorStoreIndex.from_vector_store(vector_store=self.vector_store, streaming=True, read_only=read_only)
            self.storage_context = StorageContext.from_defaults(vector_store=self.vector_store)
            self.memory = ChatMemoryBuffer.from_defaults(token_limit=self.token_limit)
            # Here is the prompt :
            self.chat_engine = self.index.as_chat_engine(
            chat_mode="context",
            memory=self.memory,
            system_prompt=(
                "Tu est un chatbot, capable d'avoir des interactions normales et de discuter"
                " d'actualités. Répond en français."
            ),
        )
        # If needed, makes data directories
        os.system("mkdir -p "+self.document_dir)
        os.system("mkdir -p "+self.vector_dir)
        os.system("mkdir -p "+self.ent_document_dir)
        os.system("mkdir -p "+self.ent_vector_dir)
        print("Initialization completed...",file=sys.stderr)

    def get_ai_generated_field(self,text, field):
        """
        Extract a brief description of major strengths of the invention

        Parameters
        ----------
            text : str
                The text to be processed
            field : str
                output's field name (e.g. "strength", see ai_generated_prompts global variable)
        Returns
        -------
            str
                the generated text
        """
        llm = Ollama(model=self.llm, request_timeout=self.llm_req_timeout)
        messages=[
            ChatMessage(role="assistant", content="Tu es un assistant. Réponds correctement aux questions de l'utilisateur."),
            ChatMessage(role="user", content=ai_generated_prompts[field][1]+text)
        ]
        # start llm inference
        resp = llm.chat(messages)
        content = None
        # parse the LLM output
        for item in resp:
            if isinstance(item, tuple) and item[0] == 'message':
                content = item[1].content
                break
        # return LLM output
        return content
    
    def retrieve(self, query, query_is_file=False):
        """
        Retrieve patents by performing a K Nearest Neighbours,
        based on query and patents embeddings 

        Parameters
        ----------
            query : str
                input text for query search or document similarity search
            query_is_file : bool
                Toggle between query search / similarity search
        Returns
        -------
            str
                a string containing the ranked list 
                of retrieved documents as a HTML table 
        """
        if not query_is_file:
            # First expand all ENT concepts contained in the query
            query = self.expand_query(query)
        # LLama Index does not provide the search() method for its embedded Deeplake stores, so : 
        store = deeplake.core.vectorstore.deeplake_vectorstore.DeepLakeVectorStore(path=self.vector_dir)
        result = store.search(embedding_data=query, embedding_function=self.embed_model.get_text_embedding, k=self.span_top_k)
        # Get retrieved filenames from Deeplake results
        docname_list ={result['metadata'][offset]['file_path'] for offset in range(0, len(result['metadata']))}
        print(docname_list)
        # Render results as a HTML table
        output="<table><tr><th>Sélection</th>"
        # Column names for XML fields
        for field in xml_extraction_data:
            if "display" in field:
                output+=f"<th>{field['display']}</th>"
                if field['name']=="title":
                    output+=f"<th>Date</th>"
                if field['name']=="summary":
                    output+=f"<th>Source</th>"
        # Column names for AI generated fields    
        for field in ai_generated_prompts.keys():
            output+=f"<th>✨{ai_generated_prompts[field][0]} (généré par IA)</th>"
        output+="</tr>\n"
        # Parse all retrieved XML document to extract relevant information
        for doc in docname_list:
            try:
                root=ET.parse(doc).getroot()
            except:
                continue
            # extract XML fields values
            for field in xml_extraction_data:
                # Value is a parameter value within the Nth result of a xpath query
                if "position" in field and "parameter" in field:
                    field["value"]=root.xpath(field["path"])[field["position"]].get(field["parameter"])
                # Value is the Nth result of a xpath query
                elif "position" in field:
                    tag=root.xpath(field["path"])
                    if len(tag)>field["position"]:
                        field["value"]=root.xpath(field["path"])[field["position"]]
                    else:
                        field["value"]="..."
            id=os.path.basename(doc).strip(".xml")          
            output+='<tr>'
            output+="<td>"+'<input type="checkbox" id="'+id+'" onchange="append_docs(this)" ></td>'
            # output of XML fields
            for field in xml_extraction_data:
                if "display" in field:
                    output+=f"<td>{field["value"]}</td>"
                else:
                    match field["name"]:
                        case "day":
                            date = field["value"]
                        case "month":
                            date += "/"+field["value"]
                        case "year":
                            date += "/"+field["value"]
                            output+=f"<td>{date}</td>"
                        case "link":
                            domain=urlparse(field["value"]).netloc
                            output+=f'<td><a href="{field["value"]}">{domain}</a></td>'
            # output of AI generated fields
            for field in ai_generated_prompts.keys():
                with open(doc.strip(".xml")+"."+field+'.html', "r") as file:
                    content = file.read()
                    output+=f"<td>{content}</td>"
            output+="</tr>\n"
        output+="</table>\n"
        return output

    def extend(self, query):
        """
        Retrieve entities by performing a K Nearest Neighbours, 
        based on query and entity embeddings 
        
        Parameters
        ----------
            query : str
                query text to be expanded
        Returns
        -------
            str
                a string that contains an ordered list of 
                retrieved entities as a HTML table
        """
        store = deeplake.core.vectorstore.deeplake_vectorstore.DeepLakeVectorStore(path=self.ent_vector_dir)
        result = store.search(embedding_data=query, embedding_function=self.embed_model.get_text_embedding, k=self.span_top_k)
        # Get retrieved concept IDs and their contents
        concept_list = [result['metadata'][offset]['file_name'] for offset in range(0, len(result['metadata']))]
        # print(result['text'])
        content_list = [result['text'][offset] for offset in range(0, len(result['text']))]
        output="<table><tr><th>sélection</th><th>entité</th><th>description</th></tr>\n"
        num_lines=0
        for offset in range(0, len(result['text'])):
            num_lines+=1
            # As some concepts might be empty, we need to retrieve more than needed,
            # So stop once enough 
            if num_lines > int(os.getenv('MAXNUM_DISPLAYED_CONCEPTS'))+1:
                break
            # Don't display long descriptions
            forms= [html2text(x) for x in content_list[offset].split("\n") if x !="" and len(x)<int(os.getenv('MAX_LEN_FOR_CONCEPT_DESC'))]
            # Don't display spurious forms
            #forms = sorted(list(filter(lambda f: len(f)>3, forms)))
            if len(forms)<=0: # skip if concept has no form
                continue
            # HTML for the row of selectable concept
            concept_id = concept_list[offset].strip(".txt")
            output+="<tr>"
            output+="<td>"+'<input type="checkbox" id="'+concept_id+'" onchange="append_query(this)" ></td>'
            output+='<td><b>'+forms[0]+"</b></td><td>"+" ; ".join(forms)+"</td>"
            output+="</tr>"
        output+="</table>\n"
        return output
    
    def filter_query(self, query):
        """
        remove concept IDs from query 

        Parameters
        ----------
            query : str
                input query text that might contain entities IDs
        Returns
        -------
            str
                the filtered query
        """
        terms=query.split()
        filtered = list(filter(lambda t: not concept_pattern.match(t), terms))
        return " ".join(filtered)
    
    def expand_query(self, query):
        """
        Replace concept IDs in query by their contents

        Parameters
        ----------
            query : str
                unexpanded query text
        Returns
        -------
            str
                the expanded query text
        """
        terms=query.split()
        # get entities from query
        concepts = list(filter(lambda t: concept_pattern.match(t), terms))
        # remove entities from query
        filtered = list(filter(lambda t: not concept_pattern.match(t), terms))
        query = " ".join(filtered)
        # do query expansion
        for concept in concepts:
            with open(self.ent_document_dir+"/"+concept[:4]+"/"+concept+".txt") as f:
                content = f.readlines()
            query+=" "+html2text(" ".join(content)).replace('\n', ' ')
        return query

    def get_json(self, input_text):
        output=""
        inside=False
        for line in input_text.split('\n'):
            if line[:3]=="```":
                inside = not inside
                continue
            if inside:
                output+=line
        try:
            output = json.loads(output)
            if type(output) is list:
                output = {"entités": output}
            if "entités" not in output:
                field_name = output.keys()[0]
                output = {"entités": output[field_name]}
            return output          
        except:
            return {"entités": []}
            
    def reindex(self, index_name):
        """
        Load, store, index data as vectors of text spans embedding

        Parameters
        ----------
            index_name : str
                "NEWS" stands for news feeds, "WIKI" stands for Wikipedia entities, "BOTH" stands for both indexes
        Returns
        -------
            None
                nothing
        """
        # Indexing news
        if index_name in ["NEWS", "BOTH"]:
            print(f"Reindexing News feeds...")
            # Find all news feed URLs
            with open(self.url_list) as file:
                urls = [line.rstrip() for line in file]
                nb_docs=0
            for url in urls:
                f=feedparser.parse(url)
                for post in f.entries:
                    # make a directory structure from published date and hour
                    # e.g. "/2024/11/09/17"
                    path=["/"]
                    path.append(str(post.published_parsed.tm_year))
                    path.append(str(post.published_parsed.tm_mon))
                    path.append(str(post.published_parsed.tm_mday))
                    path.append(str(post.published_parsed.tm_hour))
                    path=self.document_dir+'/'.join(path)
                    article = {
                        "article": post 
                    }
                    # make filename from url
                    content=xmltodict.unparse(article, pretty=True)
                    url = post.id.encode('UTF-8')
                    filename=base64.urlsafe_b64encode(url).decode('UTF-8')[-30:]+".xml"
                    try:
                        os.system("mkdir -p "+path)
                        with open(path+filename, "x") as file:
                            # Make directory
                            file.write(content)
                            nb_docs+=1
                    except:
                        pass
            print(f"Storing {nb_docs} news embeddings to disk...")
            # Load documents and build index
            print("loading data...")
            documents = SimpleDirectoryReader(self.document_dir, recursive=True).load_data(num_workers=int(os.getenv('NUM_WORKERS')))
            print("Extract AI generated fields...")
            entity_desc=dict()
            doc_limit=int(os.getenv("DOC_LIMIT"))
            if doc_limit>0:
                documents=documents[:doc_limit]
            for doc in tqdm(documents):
                if len(doc.text) == 0:
                    continue
                # parse xml file
                try:
                    root=ET.fromstring(bytes(doc.text, encoding='utf8'))
                except:
                    continue
                # Add title to deeplake index
                title=root.xpath("/article/title/text()")
                doc.metadata["title"]=str(title)
                # Extract AI generated files
                for field in ai_generated_prompts.keys():
                    filename = doc.metadata["file_path"].strip(".xml")+'.'+field+'.html'
                    with open(filename, "w") as file:
                        generated_text=self.get_ai_generated_field("\n".join(root.xpath('//text()'))[:self.token_limit], field)
                        generated_entities = self.get_json(generated_text)
                        #print(generated_entities)
                        entity_list = generated_entities['entités']
                        for entity in entity_list:
                            if "Description" in entity and type(entity["Description"]) is str:
                                if entity["Nom"] in entity_desc:
                                    entity_desc[entity["Nom"]]+=entity["Description"]+'\n'
                                else:
                                    entity_desc[entity["Nom"]]=entity["Description"]+'\n'
                        file.write(json2html.convert(json = generated_entities))
                        #file.write("# None")
            # Write entities and their descriptions to files
            ent_id=0
            for ent in tqdm(entity_desc):
                filename=ent.replace(" ", "_").replace("/", " ")+".txt"
                if len(filename)>50:
                    continue
                path = self.ent_document_dir + str(ent_id)[:6].replace("",'/')
                os.makedirs(path, exist_ok=True)
                with open(path+filename, "a+") as file:
                    file.write(ent+'\n'+entity_desc[ent])
                ent_id+=1
            # embedding model
            Settings.embed_model = self.embed_model
            # ollama
            Settings.llm = self.llm_settings
            print("Indexing articles can take some time...")
            os.system("mkdir -p"+self.vector_dir)
            self.index = VectorStoreIndex.from_documents(
                documents, show_progress=True, storage_context=self.storage_context
            )
            print("Indexing articles completed...")
        # Indexing Wikipedia concepts and their forms
        if index_name in ["WIKI", "BOTH"]:
            print(f"Reindexing WIKI...")
            os.system("mkdir -p "+self.ent_vector_dir)
            # Load documents and build index
            concepts = SimpleDirectoryReader(self.ent_document_dir, recursive=True).load_data(num_workers=int(os.getenv('NUM_WORKERS')))
            # embedding model
            Settings.embed_model = self.embed_model
            # ollama
            Settings.llm = self.llm_settings
            print("Indexing concepts can take some time...")
            self.ent_index = VectorStoreIndex.from_documents(
                concepts, show_progress=True, storage_context=self.ent_storage_context
            )
            print("Indexing concepts completed...")
        if index_name not in ["WIKI", "NEWS", "BOTH"]:
            print("Error : Invalid index name. Choose 'NEWS' for patents or 'ENT' for entities", file=sys.stderr)

    def patchat(self, question):
        """
        Start the chatbot in streaming mode

        Parameters
        -----------
            question : str
                current prompt
        Returns
        -------
            StreamingAgentChatResponse
                a stream where token are directed as they are inferred
                the StreamingAgentChatResponse class is defined in LlamaIndex module
        """
        # remove concept IDs as their are not helpfull here
        question = self.filter_query(question)
        print(f"Answering '{question}'", file=sys.stderr)
        streaming_response = self.chat_engine.stream_chat(question)
        print(streaming_response.__class__.__name__)
        return streaming_response

if __name__ == "main":
    print("This toolkit should be called by app.py")