import discord
from discord.ext import commands
import bot

cogs = [bot]

client = commands.Bot(command_prefix='?', intents = discord.Intents.all())

for i in range(len(cogs)):
    cogs[i].setup(client)


client.run("ODk0OTEzNzA2MDI1MTYwNzE1.YVw7Vg.ORxixReu2PubXRl8akI7ca99NiE")