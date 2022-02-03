# IMPORTS
import asyncio
import datetime
import discord
import random
import sqlite3
from discord.ext import commands, tasks
from config import settings, dbname

# set bot commands prefix
bot = commands.Bot(command_prefix=settings['prefix'])

# db part
# TODO: make log system more common (not just print command)
conn = sqlite3.connect(dbname)
cursor = conn.cursor()
sql = "SELECT COUNT(joke_id) FROM jokes;"
number_of_jokes = 1


# EVENTS
# on connect actions
@bot.event
async def on_connect():
    # log connection info
    print(datetime.datetime.now(), 'INFO', 'Bot connected')


# on ready actions
@bot.event
async def on_ready():
    # log ready info
    print(datetime.datetime.now(), 'INFO', 'Bot ready')
    # log connected guilds number
    print(datetime.datetime.now(), 'INFO', 'Number of servers connected to:', len(bot.guilds))
    await asyncio.sleep(3)
    # start status update loop
    update_status.start()
    # start number of jokes update loop
    update_jokes.start()


# wrong commands handler
@bot.event
async def on_command_error(ctx, error):
    author = ctx.message.author
    if isinstance(error, commands.CommandNotFound):
        await ctx.send(f'{author.mention}, command not found.\n'
                       f'Please, use the "?help" command to get full list of commands.')


# LOOPS
# status update loop
@tasks.loop(hours=1)
async def update_status():
    print(datetime.datetime.now(), 'INFO', 'Bot status updated, current number:', len(bot.guilds))
    await bot.change_presence(activity=discord.Game(name=f"{len(bot.guilds)} servers"))


# number of jokes update loop
@tasks.loop(hours=1)
async def update_jokes():
    cursor.execute(sql)
    global number_of_jokes
    number_of_jokes = cursor.fetchone()[0]
    print(datetime.datetime.now(), 'INFO', 'Jokes number updated, current number:', number_of_jokes)
    return number_of_jokes


# COMMANDS
# hello command, lets introduce our bot and functions
@bot.command()
async def hello(ctx):
    """
    Basic information
    """

    author = ctx.message.author
    await ctx.send(f'Hello, {author.mention}.\n'
                   f'My name is Dice Roller. '
                   f'I am here to help you with rolling dices. '
                   f'Please, ask "?help" for more info about commands.')


# joke command, it should post random DnD or another role-play game joke
@bot.command()
async def joke(ctx):
    """
    Get a joke
    """

    random_joke_number = random.randint(1, number_of_jokes)
    sql_joke = "SELECT joke_text FROM jokes WHERE joke_id=?;"
    cursor.execute(sql_joke, [random_joke_number])
    joke_text = cursor.fetchone()[0]
    await ctx.send('Today joke is:\n' + joke_text)


# command for display info about creator and some links
@bot.command()
async def creator(ctx):
    """
    Info about creator
    """

    embed = discord.Embed(title="My creator", url="https://www.facebook.com/lulukreicer",
                          description="He is just a flesh bag but I was created by his will. \
                          Also, he allows me to rest sometimes, so... few words about him.",
                          color=0xff0000)
    embed.add_field(name="alias", value="kreicer", inline=True)
    embed.add_field(name="github repo", value="https://github.com/kreicer/dice-roller-bot", inline=True)
    embed.set_footer(text="You can support him on paypal.me/kreicer")
    await ctx.send(embed=embed)


# command for rolling dices
# TODO: add more checks, optimize current checks
@bot.command()
async def roll(ctx, *arg):
    """
    Roll the dices
    """

    # get rolls list from text after bot command
    rolls = list(arg)
    # start our result from empty string
    result = ''

    # for each roll do some checks and preparations
    for dice_roll in rolls:
        # lets split our dice roll into number of dices and number of edges
        # 2d20: 2 - number of dices, 20 - number of edges, d - separator
        # TODO: maybe better create class for dices?
        numbers = dice_roll.split('d')

        # convert '' into number of dices, count as 1, ex: d20 == 1d20
        dice_count = numbers[0]
        if dice_count == '':
            dice_count = '1'

        # check if number of edges is existed
        try:
            dice_edge = numbers[1]
        except Exception:
            raise commands.BadArgument

        # check on count of separated parts to fix constructions like 2d20d20
        if len(numbers) != 2:
            raise commands.BadArgument

        # check on dice count and edges can be converted into integer
        try:
            int(dice_count)
            int(dice_edge)
        except Exception:
            raise commands.BadArgument

        # if dice count or edge less than 1 then ignore this roll
        if int(dice_count) < 1 or int(dice_edge) < 1:
            continue

        # if roll should be done lets add text section for it
        result += '\nD' + dice_edge + ':'

        # roll each dice of current edge
        for counts in range(1, int(dice_count) + 1):
            # get result of current roll dice and convert into string
            sub_result = str(random.randint(1, int(dice_edge)))
            # add sub result with some formatting into result
            result += '  **' + sub_result + '**'

    # create embed object from result for discord chat
    embed = discord.Embed(color=0xff0000, title=result)
    # send it into chat
    await ctx.send(embed=embed)


# bad argument exception
@roll.error
async def roll_error(ctx, error):
    author = ctx.message.author
    if isinstance(error, commands.BadArgument):
        await ctx.send(f'{author.mention}, wrong dice.\n'
                       f'Try something like d20, 5d4, 1d100.')


# bot start
bot.run(settings['token'])

# close sqlite connection
conn.close()
