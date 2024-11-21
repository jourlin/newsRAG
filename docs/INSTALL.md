# INSTALL INSTRUCTIONS

## Warning : 
The following instructions were tested successfully with the followings specs :
- Ubuntu 24.04 LTS
- Nvidia GPU with at least 6Gb VRAM (A3000 & 3060)
You might need to adapt some parts to fit your computer and its operating system

## Step 1: Download latest release

* visit [my github repository](https://github.com/jourlin/newsRAG/releases) and download ```newsRAG-X.Y.zip``` where X and Y are respectively the version and subversion numbers of the latest release.

## Step 2: Install Flask server

- Commands to run in your linux terminal

1. ```cd newsRAG``` 
2. ```python -m venv .```
3. ```source bin/activate```
4. ```pip install -r requirements.txt``` for AMD64 systems or ```pip install -r requirements_arm64_noGPU.txt``` for ARM64 systems
5. Edit ```./src/.env``` to match your local system

## Step 3: Edit your RSS sources
6. Edit ```./resources/newslist.tsv``` to modify the list of RSS source url

## Step 4: Install and start ollama
7. Install Ollama and pull llama3:
- Without root privileges
```
wget https://github.com/ollama/ollama/releases/download/v0.3.9/ollama-linux-amd64.tgz
tar xvfz ollama-linux-amd64.tgz
./bin/ollama serve &
./bin/ollama pull llama3
```
- With root privileges
```
sudo curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3
```

## Step 5: Run the embedding indexer
```flask reindex BOTH```
- instead of "BOTH" you can speficy :
    - 1st stage "NEWS" : extract entities from RSS feeds and index RSS articles
    - 2nd stage "WIKI" : index entities that were extracted in stage 1
**WARNING** : Depending on the size of data to be indexed, the full process can take hours or even days.

## Step 6: How to run the web server
- ```flask run``` for execution as localhost, listening on port 5000
- ```flask run -h 0.0.0.0 -p <P>``` allows external access, listening on port ```<P>```

## Step 7: Use the retriever and chatbot
- Open [http://127.0.0.1:5000](http://127.0.0.1:5000) with a web browser

## Step 8: User guide
Have a look at [USER_GUIDE.md](./USER_GUIDE.md) for instructions and explanation of user's interface
