import os
import youtube_dl
import pafy
import discord
from discord.ext import commands

TOKEN = os.environ.get('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="/", intents=intents)

@bot.event
async def on_ready():
    print(f"{bot.user.name} está pronto.")
    print(TOKEN)


class Player(commands.Cog):
    def __init__(self, bot):
        self.bot = bot 
        self.song_queue = {}

        self.setup()

    def setup(self):
        for guild in self.bot.guilds:
            self.song_queue[guild.id] = []

    async def check_queue(self, ctx):
        if len(self.song_queue[ctx.guild.id]) > 0:
            await self.play_song(ctx, self.song_queue[ctx.guild.id][0])
            self.song_queue[ctx.guild.id].pop(0)

    async def search_song(self, amount, song, get_url=False):
        info = await self.bot.loop.run_in_executor(None, lambda: youtube_dl.YoutubeDL({"format" : "bestaudio", "quiet" : True}).extract_info(f"ytsearch{amount}:{song}", download=False, ie_key="YoutubeSearch"))
        if len(info["entries"]) == 0: return None

        return [entry["webpage_url"] for entry in info["entries"]] if get_url else info

    async def play_song(self, ctx, song):
        url = pafy.new(song).getbestaudio().url
        ctx.voice_client.play(discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(url)), after=lambda error: self.bot.loop.create_task(self.check_queue(ctx)))
        ctx.voice_client.source.volume = 0.5

    @commands.command()
    async def join(self, ctx):
        if ctx.author.voice is None:
            return await ctx.send("Você não está conectado em um servidor, por favor entre em um para colocar alguma música.")

        if ctx.voice_client is not None:
            await ctx.voice_client.disconnect()

        await ctx.author.voice.channel.connect()

    @commands.command()
    async def leave(self, ctx):
        if ctx.voice_client is not None:
            return await ctx.voice_client.disconnect()

        await ctx.send("Eu não estou em um canal.")

    @commands.command()
    async def play(self, ctx, *, song=None):
        if song is None:
            return await ctx.send("Você tem que colocar uma música para tocar.")

        if ctx.voice_client is None:
            return await ctx.send("Eu tenho que estar em um canal para tocar uma música.")

        # handle song where song isn't url
        if not ("youtube.com/watch?" in song or "https://youtu.be/" in song):
            await ctx.send("Procurando pela música, isso vai demorar uns segundos.")

            result = await self.search_song(1, song, get_url=True)

            if result is None:
                return await ctx.send("Foi mal, eu não consegui encontrar está música, tente colocar a url dela.")

            song = result[0]

        if ctx.voice_client.source is not None:
            queue_len = len(self.song_queue[ctx.guild.id])

            if queue_len < 10:
                self.song_queue[ctx.guild.id].append(song)
                return await ctx.send(f"Eu estou tocando uma música atualmente, sua música foi adicionada na lista: {queue_len+1}.")

            else:
                return await ctx.send("Perdão eu só posso ter no máximo 10 músicas na lista de uma vez.")

        await self.play_song(ctx, song)
        await ctx.send(f"Agora tocando: {song}")

    @commands.command()
    async def search(self, ctx, *, song=None):
        if song is None: return await ctx.send("Você esqueceu de escrever a música para pesquisar.")

        await ctx.send("Procurando pela música, isso vai demorar alguns segundos.")

        info = await self.search_song(5, song)

        embed = discord.Embed(title=f"Results for '{song}':", description="*Você pode colocar a URL da música se essa não for a que você queria.*\n", colour=discord.Colour.red())
        
        amount = 0
        for entry in info["entries"]:
            embed.description += f"[{entry['title']}]({entry['webpage_url']})\n"
            amount += 1

        embed.set_footer(text=f"Displaying the first {amount} results.")
        await ctx.send(embed=embed)

    @commands.command()
    async def queue(self, ctx): # display the current guilds queue
        if len(self.song_queue[ctx.guild.id]) == 0:
            return await ctx.send("Atualmente não há músicas na lista.")

        embed = discord.Embed(title="Lista", description="", colour=discord.Colour.dark_gold())
        i = 1
        for url in self.song_queue[ctx.guild.id]:
            embed.description += f"{i}) {url}\n"

            i += 1

        embed.set_footer(text="Valeu por usar meu bot!")
        await ctx.send(embed=embed)

    @commands.command()
    async def skip(self, ctx):
        if ctx.voice_client is None:
            return await ctx.send("Eu não estou tocando nenhuma música.")

        if ctx.author.voice is None:
            return await ctx.send("Você não está conectado em um servidor.")

        if ctx.author.voice.channel.id != ctx.voice_client.channel.id:
            return await ctx.send("Eu não estou tocando nenhuma música.")

        # poll = discord.Embed(title=f"Votar para skipar a música - {ctx.author.name}#{ctx.author.discriminator}", description="**80% of the voice channel must vote to skip for it to pass.**", colour=discord.Colour.blue())
        # poll.add_field(name="Skip", value=":white_check_mark:")
        # poll.add_field(name="Stay", value=":no_entry_sign:")
        # poll.set_footer(text="Voting ends in 15 seconds.")

        # poll_msg = await ctx.send(embed=poll) # only returns temporary message, we need to get the cached message to get the reactions
        # poll_id = poll_msg.id

        # await poll_msg.add_reaction(u"\u2705") # yes
        # await poll_msg.add_reaction(u"\U0001F6AB") # no
        
        # await asyncio.sleep(15) # 15 seconds to vote

        # poll_msg = await ctx.channel.fetch_message(poll_id)
        
        # votes = {u"\u2705": 0, u"\U0001F6AB": 0}
        # reacted = []

        # for reaction in poll_msg.reactions:
        #     if reaction.emoji in [u"\u2705", u"\U0001F6AB"]:
        #         async for user in reaction.users():
        #             if user.voice.channel.id == ctx.voice_client.channel.id and user.id not in reacted and not user.bot:
        #                 votes[reaction.emoji] += 1

        #                 reacted.append(user.id)

        skip = True

        # if votes[u"\u2705"] > 0:
        #     if votes[u"\U0001F6AB"] == 0 or votes[u"\u2705"] / (votes[u"\u2705"] + votes[u"\U0001F6AB"]) > 0: # 80% or higher
        #         skip = True
        #         embed = discord.Embed(title="Skip Successful", description="***Voting to skip the current song was succesful, skipping now.***", colour=discord.Colour.green())

        # if not skip:
        #     embed = discord.Embed(title="Skip Failed", description="*Voting to skip the current song has failed.*\n\n**Voting failed, the vote requires at least 80% of the members to skip.**", colour=discord.Colour.red())

        # embed.set_footer(text="Voting has ended.")

        # await poll_msg.clear_reactions()
        # await poll_msg.edit(embed=embed)

        if skip:
            ctx.voice_client.stop()


    @commands.command()
    async def pause(self, ctx):
        if ctx.voice_client.is_paused():
            return await ctx.send("Eu já estou pausado.")

        ctx.voice_client.pause()
        await ctx.send("A música atual está pausada.")

    @commands.command()
    async def resume(self, ctx):
        if ctx.voice_client is None:
            return await ctx.send("Não estou conectado em um servidor.")

        if not ctx.voice_client.is_paused():
            return await ctx.send("Eu já estou tocando uma música.")
        
        ctx.voice_client.resume()
        await ctx.send("Continuando a música atual.")

async def setup():
    await bot.wait_until_ready()
    bot.add_cog(Player(bot))

bot.loop.create_task(setup())

bot.run(TOKEN)