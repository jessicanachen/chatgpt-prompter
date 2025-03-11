import discord
from discord.ext import commands
import os
import requests
from dotenv import load_dotenv
from services.redis_client import redis_client

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

BACKEND_URL = os.getenv("BACKEND_URL")

# Sample question sequence
questions = ["What is your goal?", "What output do you expect?", "Any background details?"]

@bot.command(name="new")
async def new(ctx):
    user_id = str(ctx.author.id)
    redis_client.set(f"{user_id}:state", "q0")
    redis_client.set(f"{user_id}:conversation_type", "new")
    await ctx.send(questions[0])

@bot.event
async def on_message(message):
    await bot.process_commands(message)
    if message.author == bot.user:
        return

    user_id = str(message.author.id)
    state = redis_client.get(f"{user_id}:state")

    if state and state.startswith("q"):
        index = int(state[1])
        redis_client.set(f"{user_id}:q{index}", message.content)

        if index + 1 < len(questions):
            redis_client.set(f"{user_id}:state", f"q{index+1}")
            await message.channel.send(questions[index + 1])
        else:
            # All questions answered, build raw prompt
            goal = redis_client.get(f"{user_id}:q0")
            output = redis_client.get(f"{user_id}:q1")
            background = redis_client.get(f"{user_id}:q2")
            raw_prompt = f"Goal: {goal}\nOutput: {output}\nBackground: {background}"

            # Send to backend for formatting
            response = requests.post(f"{BACKEND_URL}/format-prompt/", json={"raw_prompt": raw_prompt})
            formatted_prompt = response.json()["formatted_prompt"]
            redis_client.set(f"{user_id}:formatted_prompt", formatted_prompt)
            redis_client.set(f"{user_id}:state", "waiting_confirmation")

            await message.channel.send(f"Here’s the formatted prompt:\n```{formatted_prompt}```\nType `send` to use it or `modify` to edit.")

    elif state == "waiting_confirmation":
        if message.content.lower() == "send":
            prompt = redis_client.get(f"{user_id}:formatted_prompt")
            messages = [{"role": "user", "content": prompt}]
            response = requests.post(f"{BACKEND_URL}/send-prompt/", json={"messages": messages})
            reply = response.json()["reply"]
            redis_client.set(f"{user_id}:last_chat", reply)
            redis_client.set(f"{user_id}:state", "chatting")
            await message.channel.send(f"🤖 GPT Response:\n```{reply}```\nType `continue` to ask more, or `new` to start over.")
        elif message.content.lower() == "modify":
            await message.channel.send("Please type your modified prompt.")
            redis_client.set(f"{user_id}:state", "modifying")

    elif state == "modifying":
        redis_client.set(f"{user_id}:formatted_prompt", message.content)
        redis_client.set(f"{user_id}:state", "waiting_confirmation")
        await message.channel.send("Modified prompt saved. Type `send` to proceed.")

    elif state == "chatting" and message.content.lower() == "continue":
        await message.channel.send("Please type your follow-up question.")
        redis_client.set(f"{user_id}:state", "awaiting_followup")

    elif state == "awaiting_followup":
        last_reply = redis_client.get(f"{user_id}:last_chat")
        new_question = message.content
        messages = [
            {"role": "assistant", "content": last_reply},
            {"role": "user", "content": new_question}
        ]
        response = requests.post(f"{BACKEND_URL}/send-prompt/", json={"messages": messages})
        reply = response.json()["reply"]
        redis_client.set(f"{user_id}:last_chat", reply)
        await message.channel.send(f"🤖 GPT Response:\n```{reply}```\nType `continue` or `new`.")
