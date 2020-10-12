import discord
import random
import logging

from gmsh_terminal.features.dpyserver import discord_handler

logger = logging.getLogger(__name__)


def load_feature(old_module=None):
    pass


def unload_feature():
    pass


@discord_handler
async def on_message(client, message):
    if hasattr(message.author, 'roles') and discord.utils.find(lambda r: r.name == 'Stabby Stabby Yandere', message.author.roles):
        previous_message = (await message.channel.history(limit=1, before=message).flatten())[0]
        if previous_message.author.id == message.author.id:
            await previous_message.remove_reaction('🔪', client.user)
        await message.add_reaction('🔪')

    if discord.utils.find(lambda r: r.name == 'someone', message.role_mentions):
        target = random.choice([m for m in message.channel.members
                                if m.status in [discord.Status.online, discord.Status.idle] and not m.bot])
        ghostping = await message.channel.send(f'<@{target.id}>')
        await ghostping.delete()
        return

    if message.guild is not None:
        dt_emoji = discord.utils.find(lambda e: e.name == 'determination', message.guild.emojis)
        ayakosuffer_emoji = discord.utils.find(lambda e: e.name == 'BeingAyakoisSuffering', message.guild.emojis)
        if message.content == f'<:{dt_emoji.name}:{dt_emoji.id}>':
            await message.channel.send('```\nFILE SAVED\n```')
        if 'DETERMINATION' in message.content or 'DETERMINED' in message.content:
            await message.add_reaction(dt_emoji)
        if 'MURDER' in message.content:
            await message.add_reaction('🔪')
        if 'KINDNESS' in message.content:
            await message.add_reaction('💚')
        if 'Ayakaa-sama' in message.content:
            await message.add_reaction(ayakosuffer_emoji)
    return


@discord_handler
async def on_reaction_add(client, reaction, user):
    if user.bot:
        return

    yandere_role = discord.utils.find(lambda r: r.name == 'Stabby Stabby Yandere', user.guild.roles)
    if reaction.emoji == '🔪':
        await user.add_roles(yandere_role)
    if reaction.emoji == '💚' and user.id != 751499881683615784:
        await user.remove_roles(yandere_role)
