import os
import json
import requests
from discord.ext import commands
import discord
from datetime import datetime, timezone
import re

try:
    import discord
    import requests
except ModuleNotFoundError:
    os.system("pip install discord requests")

# Load configuration file
config_path = "./config.json"
if not os.path.exists(config_path):
    print("Config file not loaded.")
    exit(1)
else:
    print("Config file loaded.")
    with open(config_path, "r") as f:
        config = json.load(f)

bot = commands.Bot(command_prefix=config['BOT_PREFIX'], intents=discord.Intents.all())

@bot.command(name="lang")
async def languages(ctx):
    url = "https://onecompiler.com/api/v1/languages"

    try:
        res = requests.get(url)
        res.raise_for_status()

        languages = res.json()
        if isinstance(languages, list):
            em = discord.Embed(title="Supported Languages 🌐", color=discord.Color.green())
            
            # Create a list of strings to join together, not a single string
            description = []
            for lang in languages:
                description.append(f"***Id - Name - Type\n{lang['id']} - {lang['name']}*** - {lang.get('languageType', 'Unknown')}")
            
            em.description = "\n".join(description)

            em.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.avatar.url)
            
            await ctx.send(embed=em)
        else:
            await ctx.send("Unexpected response format from the API.")
    except requests.RequestException as e:
        await ctx.send(f"An error occurred while fetching languages: {e}")    

@bot.command(name="compile")
async def compile(ctx, *, arg):
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    url = "https://onecompiler-apis.p.rapidapi.com/api/v1/run"

    headers = {
        "x-rapidapi-key": config['API_KEY'],
        "x-rapidapi-host": "onecompiler-apis.p.rapidapi.com",
        "Content-Type": "application/json"
    }

    # Check if arg starts with the language name followed by a code block
    match = re.match(r"^(\w+)\s*```([\w\W]+?)```$", arg, re.DOTALL)
    if match:
        lang_id = match.group(1)
        code = match.group(2)
    else:
        # If no code block is found, treat the whole arg as plain text codes
        lang_id, code = arg.split(maxsplit=1)

    payload = {
        "language": lang_id,
        "files": [
            {
                "name": f"main.{lang_id}",
                "content": code.strip()  # Trim leading/trailing whitespace
            }
        ],
    }

    try:
        res = requests.post(url, headers=headers, json=payload)
        res.raise_for_status()

        data = res.json()

        stdout = data.get('stdout', 'No output')
        execution_time = data.get('executionTime', 'Unknown')
        limit_remaining = data.get('limitRemaining', 'Unknown')

        em = discord.Embed(title=f":gear: {lang_id} compiler", description=f"```{stdout}```", color=discord.Color.green())
        em.add_field(name="Compile time", value=f"```{execution_time}```", inline=False)
        em.add_field(name="Limit remaining", value=f"```{limit_remaining}```", inline=False)
        em.set_footer(text=timestamp)

        await ctx.send(embed=em)

    except requests.RequestException as e:
        await ctx.send(f"An error occurred while compiling code: {e}")

    except KeyError as e:
        await ctx.send(f"An error occurred while parsing API response: {e}")

    except Exception as e:
        await ctx.send(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    try:
        bot.run(config['BOT_TOKEN'])
    except Exception as e:
        print(e)
