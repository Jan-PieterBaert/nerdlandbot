# nerdlandbot
This is a Python-based discord bot developed by the nerdland fan community.

# Roadmap
This bot was setup mostly as an experiment, and there is no clearly defined goal so far.
If you have any suggestions feel free to log an issue in this repository, any new ideas or challenges are much appreciated.

# Setting up your development environment
To get this project up and running, make sure you have the following installed:
- Python 3
- PIP
- [Poetry](https://python-poetry.org/docs/#installation)
- Use your favourite ide and git to clone the nerdlandbot to your local machine

Once you have these installed (you can check by running 'python --version', 'pip -V' and 'poetry -V' in a commandline), add the required packages (see requirements.txt) using pip:
```
pip install -r requirements.txt
```
Then run the following command in the root directory of the clone (eg. ~/Documents/python/nerdlandbot) to install the required packages:
```
poetry install
```

# Creating your own test bot
When trying out things, it's best to create your own bot and use that one to test your code. To create your test version of the nerdlandbot:
- Go to discord.com https://discord.com/login?redirect_to=%2Fdevelopers%2Fapplications and log in.
- Create a new application eg. "bob-testbot"
- Switch to the 'Bot' configuration (select 'Bot' on the left panel)
- Create a bot and give it a name "bob-testbot" for example
- Make sure you set both 'Presence intent' and 'Server members intent' under 'Privileged Gateway Intents'

# Get your bot invited to servers
To get your bot invited onto a server, you need to create an invitation URL.
- Go to your application (see creating your own test bot above)
- Copy the "client id" from your application (! NOT your bot token !)
- The URL to invite your bot to a server is: https://discord.com/api/oauth2/authorize?client_id=<APPLICATION_CLIENT_ID>&permissions=0&scope=bot

When visiting that page, you'll see a list of servers you have administration rights for. If you have your own server, it will be listed here. 
If you want to test on the NerdlandBottest server, provide this URL in the #helpdesk channel and kindly ask somebody to accept your bot and create a test channel.
Alternatively, you will need to acquire a `DISCORD_TOKEN`. It is possible to obtain one with a developer account on Discord.

# Create your .env file
You need a file to keep your bot token safely. You'll do this by creating a file with name ".env" which must contain following lines:
```
# .env
DISCORD_TOKEN=<BOT_TOKEN>
PREFIX=?
```
Make sure this file is listed in the .gitignore file, so your bot token isn't uploaded to github for everyone to see (and use).

# Using YouTube functionality 

For using the YouTube notifications functionality you'll need to set the `YOUTUBE TOKEN` in your `.env` file. Follow the instructions [here](https://developers.google.com/youtube/registering_an_application) to create an API key.


# Running the bot on your local machine
You can now run the bot by running the following command in the root of your nerdlandbot folder:
```
python -m nerdlandbot
```



# Running this bot with docker

```
docker run -itd --restart="unless-stopped" --name nerdlandbot \
 -e PREFIX=<Your prefix here> \
 -e DISCORD_TOKEN=<Your discord token here> \
 -v <Your bind mount path for guild configs>:/GuildConfigs \
 nerdlandfansunofficial/nerdlandbot:latest
```

# Links
* [Nerdland website](https://nerdland.be)
* [Nerdland merch](https://www.mistert.be/nerdland)
