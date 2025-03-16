import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import redis

load_dotenv()

redis_client = redis.Redis.from_url(os.getenv("REDIS_URL"), decode_responses=True)

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

questions = ["What is your goal?", "What output do you expect?", "Any background details?"]

@bot.event
async def on_ready():
    """_summary_
    Prints when the bot is succcessfully online and the username of the bot.
    """
    print(f"✅ Bot is ready. Logged in as {bot.user.name}")

@bot.command(name="new")
async def new(ctx):
    """_summary_
    Handles the initiation of a new interaction with the bot.
    This function resets all memory (sets up a new chat for this bot as well as for the 
    chatgpt conversation.
    
    Thus it clears the users answers and state, and sets the state to the first question.
    
    Args:
        ctx (Context): The context of the command invocation, which includes information about the author and the channel.
    Returns:
        None
    """
    
    user_id = str(ctx.author.id)
    
    redis_client.set(f"{user_id}:state", "q0")
    for i in range(len(questions)):
        redis_client.delete(f"{user_id}:q{i}")
    print(f"[STATE] {user_id} → q0")
    
    # send the first question
    await ctx.send(questions[0])

@bot.event
async def on_message(message):
    """
    Handles the conversation flow of the bot.
    
    This function is called whenever a message is sent in the chat where the bot is active.
    It checks the state of the conversation and processes the message accordingly.

    Args:
        message (discord.Message): The message object containing details about the message sent in the chat.
    
    Returns:
        None
    """
    
    # basically this one checks if its a command to be triggered
    # don't delete this otherwise all cxommands won't work and then life will be sad.
    await bot.process_commands(message)
    
    # don't double message
    # essentially don't try to answer the bot or count a command as a separate message 
    # (since the commands are prosessed themselves)
    if message.author == bot.user or message.content.startswith("!"):
        return

    # -- Now: handle conversation flow based on user and its current state ))
    user_id = str(message.author.id)
    state = redis_client.get(f"{user_id}:state")

    # if it is a question ask the next question and store it
    if state and state.startswith("q"):
        index = int(state[1])
        redis_client.set(f"{user_id}:q{index}", message.content)
        print(f"[ANSWER] {user_id} → q{index}: {message.content}")

        if index + 1 < len(questions):
            redis_client.set(f"{user_id}:state", f"q{index + 1}")
            print(f"[STATE] {user_id} → q{index + 1}")
            await message.channel.send(questions[index + 1])
        # if index + 1 = len(questions) asked all the questions so now format it
        else:
            goal = redis_client.get(f"{user_id}:q0")
            output = redis_client.get(f"{user_id}:q1")
            background = redis_client.get(f"{user_id}:q2")
            raw_prompt = f"Goal: {goal}\nOutput: {output}\nBackground: {background}"
            formatted_prompt = f"[MOCK FORMATTED PROMPT]\n{raw_prompt}"

            redis_client.set(f"{user_id}:formatted_prompt", formatted_prompt)
            redis_client.set(f"{user_id}:state", "waiting_confirmation")
            print(f"[PROMPT] Raw Prompt for {user_id}:\n{raw_prompt}")
            print(f"[STATE] {user_id} → waiting_confirmation")

            await message.channel.send(
                f"Here’s the formatted prompt:\n```{formatted_prompt}```\nType `send` to use it or `modify` to edit."
            )

    # this is if the state is wating confirmation from formated rpompt
    elif state == "waiting_confirmation":
        # if usur message is send then send the prompt to chatgot 
        if message.content.lower() == "send":
            prompt = redis_client.get(f"{user_id}:formatted_prompt")
            reply = f"[MOCK GPT REPLY] Based on your prompt: {prompt}"
            redis_client.set(f"{user_id}:last_chat", reply)
            redis_client.set(f"{user_id}:state", "chatting")

            print(f"[SEND] {user_id} → Sent prompt.")
            print(f"[REPLY] {user_id} → {reply}")
            print(f"[STATE] {user_id} → chatting")

            await message.channel.send(
                f"🤖 GPT Response:\n```{reply}```\nType `continue` to ask more, or `new` to start over."
            )

            # TODO: make new also one because this isn't the !new new, so it should function like
            # the countiue command except the new chat is on a new chatting window
            # should keep history? from the last convo and then reset it once done with the first chat
            # need to flesh this part out

        # if the user wants to modify the prompt
        elif message.content.lower() == "modify":
            redis_client.set(f"{user_id}:state", "modifying")
            print(f"[STATE] {user_id} → modifying")
            await message.channel.send("Please type your modified prompt.")
            
        # TODO: probably an error message if it not send on modify

    # user sends in whole modified ppropt and now just has the option to send.
    elif state == "modifying":
        redis_client.set(f"{user_id}:formatted_prompt", message.content)
        redis_client.set(f"{user_id}:state", "waiting_confirmation")
        print(f"[MODIFIED PROMPT] {user_id}: {message.content}")
        print(f"[STATE] {user_id} → waiting_confirmation")
        await message.channel.send("Modified prompt saved. Type `send` to proceed.")

    # from chattting if you send continue do follow up
    elif state == "chatting" and message.content.lower() == "continue":
        redis_client.set(f"{user_id}:state", "awaiting_followup")
        print(f"[STATE] {user_id} → awaiting_followup")
        await message.channel.send("Please type your follow-up question.")

    # TODO: make follow up reprompt the user with all the question wiht the otpion of filling in from history
    # and modifying that prompt as well
    elif state == "awaiting_followup":
        new_question = message.content
        last_reply = redis_client.get(f"{user_id}:last_chat")
        reply = f"[MOCK GPT FOLLOW-UP] You asked: {new_question}\n(Previous: {last_reply})"
        redis_client.set(f"{user_id}:last_chat", reply)

        print(f"[FOLLOW-UP] {user_id}: {new_question}")
        print(f"[REPLY] {user_id} → {reply}")

        await message.channel.send(
            f"🤖 GPT Response:\n```{reply}```\nType `continue` to keep going or `new` to start over."
        )

# end just clears all data
@bot.command(name="end")
async def end_conversation(ctx):
    user_id = str(ctx.author.id)

    # Clear all Redis keys related to this user
    redis_client.delete(f"{user_id}:state")
    redis_client.delete(f"{user_id}:formatted_prompt")
    redis_client.delete(f"{user_id}:last_chat")
    for i in range(len(questions)):
        redis_client.delete(f"{user_id}:q{i}") 

    print(f"[RESET] {user_id} → conversation state cleared.")
    await ctx.send("🛑 Conversation ended. You can start again with `!new`.")
