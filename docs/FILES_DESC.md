# Directories
* [/docs](/docs): project documentation
* [/docs/images](/docs/images): required images for project documentation
* [/src](/src): code source and scripts
* [/resources](/resources): Downloaded data + generated data + vector stores

# Files :
* Documentation
    * [/README.md](/README.md): General information
    * [/requirements.txt](/requirements.txt): List of open source python modules needed for execution, along with their version
    * [/docs/LICENSE.md](/docs/LICENSE.md): Licence information (GNU GPL Afero)
    * [/docs/INSTALL.md](/docs/INSTALL.md): Installation Instructions
    * [/docs/USER_GUIDE.md](/docs/USER_GUIDE.md): How to use the web UI
    * [/docs/TODO.md](/docs/TODO.md): Things that could be improved
* Resources
    * [/resources/documents](/resources/documents): Location of downloaded RSS feeds
    * [/resources/entities](/resources/entities): Location of extrated entities
    * [/resources/my_docs](/resources/my_docs): Location of user's documents
* Source code
    * [/src/.env](/src/.env): Environement variables (configuration) that are automatically loaded by Flask.
    * [/src/app.py](/src/app.py): Flask's main file. API routes are defined here.
    * [/src/toolkit.py](/src/toolkit.py): Main python code for langage processing, retrieval and RAG chatbot based on open source models
    * [/src/static/favicon.ico](/src/static/favicon.ico): a small decoration for browser's tabs.
    * [/src/static/newsrag.css](/src/static/newsrag.css): a very light styling for web pages
    * [/src/static/newsrag.js](/src/static/newsrag.css): main Javascript code
    * [/src/templates/index.html](/src/templates/index.html): Flask template to be rendered
    
    




    
