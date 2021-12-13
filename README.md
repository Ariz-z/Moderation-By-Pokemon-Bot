# Moderation Bot By Pokémon Bot Discord

Official Bot for the [Pokemon Bot](https://pokemonbot.com) Discord Server written in Python using Discord.py

Though this bot is intended to be used only on the Discord Server, you can self host it in your server to test it out. Installation guide down below.

## Credits

Special Thanks to [Wiper-R](https://github.com/Wiper-R) for helping me to make this bot.

## Dependancies

This bot requires the [Discord.py v1.7.3+ library](https://discordpy.readthedocs.io/) which can be installed using pip package manager and you need to run `pip install -r requirements.txt` to install all the dependancies.

## How to host the bot and run

1. Edit the config.py file as required `DISCORD_BOT_TOKEN = DISCORD_BOT_TOKEN`, `OWNERS = []`, `DATABASE_URL = DATABASE_URL`, `DATABASE_NAME = DATABASE_NAME`.

2. Run bot.py to start the bot!

## Note

This bot requires Server Members Intent , Server Presence Intent and Message Intent so make sure to enable that by going to your Discord Application -> Bot -> Privilaged Gateway Intents and enabling Server Members Intent. Without this, bot won't be able to access the cache to get user names.

## Contribution

Pull Requests will be accepted on this repository. To create a pull request, go to : https://github.com/Ariz-z/Pokemon-Support/pulls. However, this repository will continue to be updated.

## Changelogs

13 December 2021:
  1. Added Tags system,
  2. Added mongodb database with support for tag system,
  3. Added general commands

## Upcoming Changes

1.) Auto Mod system fully function.

2.) Some custom blacklisted words system for auto mod.

