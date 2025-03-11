# chatgpt-prompter

Run project root with 
```sh 
docker-compose up --build
```

To stop run 
```sh 
docker-compose down
```

After stoping can rebuild with changes using the first --build instruction

Run backend only with 
```sh 
uvicorn backend.main:app --reload
````


## Set up 

Create new venv 
```sh
python3 -m venv venv && source venv/bin/activate
````

### Setting Up Discord Bot 
Install Discord, dotenv
```sh 
python3 -m pip install discord 
pip install dotenv
```

Go to Discord Developers and make a new app https://discord.com/developers/applications


<!-- send this to your obsidian later -->