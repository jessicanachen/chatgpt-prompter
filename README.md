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
Install Discord, dotenv, redis
```sh 
python3 -m pip install discord dotenv redis
```

Go to Discord Developers and make a new app https://discord.com/developers/applications

## Redis

```sh
docker run -d -p 6379:6379 --name redis redis
```

## So I finall set up a docker compose

- make sure the Redis one is the one with redis, not local host

```sh
docker-compose up --build
docker-compose down
```


<!-- send this to your obsidian later -->