import logging

import discord
from gmsh.discord import discord_handler

from ezconf import cfg

logger = logging.getLogger(__name__)


@discord_handler('on_message')
async def k_name_handler(client, message):
    if cfg.k_real_name.exists() and cfg.k_real_name() in message.content.lower():
        await message.delete()
        puro = discord.utils.find(lambda m: m.id == 480160612022747136, message.guild.members)
        msg = await message.channel.send(f'Congrats {message.author.mention}, you did it!' +
                                         (f'\n{puro.mention}, you have been summoned!' if puro is not None else ''))
        await msg.add_reaction('\U0001F973')  # party-face