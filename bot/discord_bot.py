import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# simulated memory
# TODO: change to redis eventually
mock_state = {}
mock_answers = {}

questions = ["What is your goal?", "What output do you expect?", "Any background details?"]

@bot.event
async def on_ready():
    """_summary_
    Prints when the bot is succcessfully online and the username of the bot.
    """
    print(f"✅ Bot is ready. Logged in as {bot.user.name}")

@bot.command(name="new")
async def new(ctx):
    user_id = str(ctx.author.id)
    mock_state[user_id] = "q0"
    mock_answers[user_id] = {}
    print(f"[STATE] {user_id} → q0")
    await ctx.send(questions[0])

@bot.event
async def on_message(message):
    await bot.process_commands(message)
    
    if message.author == bot.user:
        return
    
    if message.author == bot.user:
        return

    if message.content.startswith("!"):
        return

    user_id = str(message.author.id)
    state = mock_state.get(user_id)

    if state and state.startswith("q"):
        index = int(state[1])
        mock_answers[user_id][f"q{index}"] = message.content
        print(f"[ANSWER] {user_id} → q{index}: {message.content}")

        if index + 1 < len(questions):
            mock_state[user_id] = f"q{index + 1}"
            print(f"[STATE] {user_id} → q{index + 1}")
            await message.channel.send(questions[index + 1])
        else:
            goal = mock_answers[user_id]["q0"]
            output = mock_answers[user_id]["q1"]
            background = mock_answers[user_id]["q2"]
            raw_prompt = f"Goal: {goal}\nOutput: {output}\nBackground: {background}"
            formatted_prompt = f"[MOCK FORMATTED PROMPT]\n{raw_prompt}"

            mock_state[user_id] = "waiting_confirmation"
            print(f"[PROMPT] Raw Prompt for {user_id}:\n{raw_prompt}")
            print(f"[STATE] {user_id} → waiting_confirmation")
            await message.channel.send(
                f"Here’s the formatted prompt:\n```{formatted_prompt}```\nType `send` to use it or `modify` to edit."
            )

    elif state == "waiting_confirmation":
        if message.content.lower() == "send":
            prompt = "[User's formatted prompt goes here]"  # We don't store it, just mock
            reply = f"[MOCK GPT REPLY] Based on your prompt: {prompt}"
            mock_state[user_id] = "chatting"
            print(f"[SEND] {user_id} → Sent prompt.")
            print(f"[REPLY] {user_id} → {reply}")
            print(f"[STATE] {user_id} → chatting")
            await message.channel.send(f"🤖 GPT Response:\n```{reply}```\nType `continue` to ask more, or `new` to start over.")

        elif message.content.lower() == "modify":
            mock_state[user_id] = "modifying"
            print(f"[STATE] {user_id} → modifying")
            await message.channel.send("Please type your modified prompt.")

    elif state == "modifying":
        # Accept the modified prompt and simulate saving
        print(f"[MODIFIED PROMPT] {user_id}: {message.content}")
        mock_state[user_id] = "waiting_confirmation"
        print(f"[STATE] {user_id} → waiting_confirmation")
        await message.channel.send("Modified prompt saved. Type `send` to proceed.")

    elif state == "chatting" and message.content.lower() == "continue":
        mock_state[user_id] = "awaiting_followup"
        print(f"[STATE] {user_id} → awaiting_followup")
        await message.channel.send("Please type your follow-up question.")

    elif state == "awaiting_followup":
        new_question = message.content
        reply = f"[MOCK GPT FOLLOW-UP] You asked: {new_question}"
        print(f"[FOLLOW-UP] {user_id}: {new_question}")
        print(f"[REPLY] {user_id} → {reply}")
        await message.channel.send(f"🤖 GPT Response:\n```{reply}```\nType `continue` to keep going or `new` to start over.")

@bot.command(name="end")
async def end_conversation(ctx):
    user_id = str(ctx.author.id)

    # Clear mock state and answers
    mock_state.pop(user_id, None)
    mock_answers.pop(user_id, None)

    print(f"[RESET] {user_id} → conversation state cleared.")
    await ctx.send("🛑 Conversation ended. You can start again with `!new`.")
