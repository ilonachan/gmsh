import asyncio

import discord
from discord import Client, RawReactionActionEvent, Message, Guild
import random

from discord.abc import Messageable

from gmsh.discord import discord_handler
from gmsh.discord.commands import gmsh_command, CommandContext

running_games = {}


@discord_handler(name='on_raw_reaction_add')
@discord_handler(name='on_raw_reaction_remove')
async def handle_crane_react(client: Client, payload: RawReactionActionEvent):
    if payload.message_id not in running_games:
        return
    guild: Guild = discord.utils.get(client.guilds, id=payload.guild_id)
    channel: Messageable = discord.utils.get(guild.text_channels, id=payload.channel_id)
    msg: Message = await channel.fetch_message(payload.message_id)  # do magic to find the message
    game = running_games[payload.message_id]
    if payload.user_id != game['player']:
        return
    emote = payload.emoji
    if not emote.is_unicode_emoji() or emote.name not in ['\u25c0', '\U0001f535', '\u25b6']:
        return
    if emote.name == '\u25c0':
        game['pos'] = max(game['pos']-1, 0)
    if emote.name == '\u25b6':
        game['pos'] = min(game['pos']+1, game['width']-1)
    if emote.name == '\U0001f535':
        del running_games[payload.message_id]
        game['state'] = 'selected'
        await msg.edit(content=make_crane_msg(game))
        await asyncio.sleep(2)
        game['state'] = 'won' if game['pos'] in game['prize'] else 'lost' if game['pos'] in game['punish'] else 'draw'

    await msg.edit(content=make_crane_msg(game))

emotes = {}


def make_crane_msg(game):
    crane_msg = ''
    for i in range(game['width']):
        if game['state'] in ['running', 'selected']:
            crane_msg += emotes['covered']
        else:
            if i in game['prize']:
                crane_msg += emotes['prize']
            elif i in game['punish']:
                crane_msg += emotes['punish']
            else:
                crane_msg += emotes['nothing']

    crane_msg += '\n'
    for i in range(game['width']):
        if i == game['pos']:
            if game['state'] == 'running':
                crane_msg += emotes['stand']
            elif game['state'] == 'selected':
                crane_msg += emotes['grab']
            elif game['state'] == 'won':
                crane_msg += emotes['welldone']
            elif game['state'] == 'draw':
                crane_msg += emotes['omeid']
            elif game['state'] == 'lost':
                crane_msg += emotes['tryagain']
        else:
            crane_msg += emotes['space']
    return crane_msg


def init_emotes(all_emotes):
    global emotes
    if len(emotes) > 0:
        return
    emotes = {'covered': str(discord.utils.find(lambda e: e.name == 'NagatoWhen', all_emotes)),
              'prize': str(discord.utils.find(lambda e: e.name == 'determination', all_emotes)),
              'punish': ':cactus:',
              'nothing': str(discord.utils.find(lambda e: e.name == 'bolgywolgy', all_emotes)),
              'stand': str(discord.utils.find(lambda e: e.name == 'Think', all_emotes)),
              'grab': str(discord.utils.find(lambda e: e.name == 'Yay', all_emotes)),
              'welldone': str(discord.utils.find(lambda e: e.name == 'MikuWave', all_emotes)),
              'omeid': str(discord.utils.find(lambda e: e.name == 'GetTheeHenceSugoi', all_emotes)),
              'tryagain': str(discord.utils.find(lambda e: e.name == 'NotLikeThis', all_emotes)),
              'space': ':heavy_minus_sign:'}


@gmsh_command('lucky-crane', mundane=True)
async def lucky_crane(ctx: CommandContext, args, metadata=None):
    init_emotes(ctx.message.guild.emojis)

    width = 5
    wincount = 2
    losscount = 1
    sel = random.sample(range(width), wincount+losscount)

    game = {
        'width': width,
        'prize': sel[:wincount],
        'punish': sel[wincount:],
        'pos': (width-1) // 2,
        'player': ctx.message.author.id,
        'state': 'running'
    }

    msg = await ctx.message.reply(make_crane_msg(game), mention_author=False)
    await msg.add_reaction('\u25c0')
    await msg.add_reaction('\U0001f535')
    await msg.add_reaction('\u25b6')

    running_games[msg.id] = game
