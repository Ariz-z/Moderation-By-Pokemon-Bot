# Moderation Bot By Pokémon Bot (Discord)

Official Moderation Bot for [Pokemon Bot](https://pokemonbot.com) functional and based in the Discord Server (https://server.pokemonbot.com), the bot is written in Python using Discord.py

This bot is intended to be used only on Discord Servers, though one can self host it in personal servers for test and educational purposes. 
Installation guide down below--

## Credits

Special Thanks to [Wiper-R](https://github.com/Wiper-R) for helping me in completion and active maintainence of the bot.

## Dependancies

This bot requires [Discord.py v1.7.3+ library](https://discordpy.readthedocs.io/) as a base dependency which can be installed using the pip package manager by running `pip install -r requirements.txt` to install all the base dependancies stored in the `requirements.txt` file.

## Hosting and Running the Bot

1. Edit the config.py file as per your requirement `DISCORD_BOT_TOKEN = DISCORD_BOT_TOKEN`, `OWNERS = []`, `DATABASE_URL = DATABASE_URL`, `DATABASE_NAME = DATABASE_NAME` 
Note:- The bot uses MongoDB as database.

2. Run bot.py to start the bot!

3. If you need further help then join the [Support Server](https://server.pokemonbot.com) for assistance.

## Note

The bot requires Server Members Intent , Server Presence Intent and Message Intent so make sure to enable that by going to your Discord Application -> Bot -> Privilaged Gateway Intents and enabling Server Members Intent. Without this, bot won't be able to access the cache to get user names.

## Contribution

Pull Requests will be accepted on this repository. To create a pull request, go to : https://github.com/Ariz-z/Moderation-By-Pokemon-Bot/pulls. However, this repository will continue to be updated.

## Changelogs

13 December 2021:
  1. Added Tags system,
  2. Added mongodb database with support for tag system,
  3. Added general commands

## Upcoming Changes

1.) Auto Mod system fully functional.

2.) Custom blacklisted words can be added for auto moderation.

