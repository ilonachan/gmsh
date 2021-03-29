import logging

from discord import Client, Message, ChannelType, Reaction, User

from gmsh.discord import commands
from gmsh.discord import discord_handler
from gmsh.discord.tep.script import get_endpoint

log = logging.getLogger(__name__)


async def request_answer(user, channel, client, statement):
    async with channel.typing():
        request = await user.send('```\nReceived unknown KNIFE request:\n' + statement +
                                  '\nPlease type your answer as a single message.```')
        msg = await client.wait_for('message', check=lambda m: m.channel == request.channel and
                                                               m.author == user)
        log.info(msg.content)
        await channel.send('```\n' + msg.content + '\n```')


@discord_handler
async def on_message(client, message):
    msg, lang = commands.parse_command(message.content.strip())

    if msg is None or lang.lower() not in ['dm', 'dmb']:
        return False

    log.info('knife request:\n' + msg)

    # await request_answer(message.author, message.channel, client, msg)


@discord_handler('on_message')
async def exec_script(client: Client, message: Message):
    if message.channel.type != ChannelType.private:
        return False
    if message.author.id == client.user.id:
        return False

    await message.add_reaction('\u274c')  # CROSS_MARK
    await message.add_reaction('\u2705')  # WHITE_HEAVY_CHECK_MARK
    tep = get_endpoint(message.author, client)
    tep.enqueue_script(message.content)


@discord_handler('on_reaction_add')
async def exec_script(client: Client, reaction: Reaction, user: User):
    if reaction.message.channel.type != ChannelType.private:
        return False

    if user.id == client.user.id:
        return False

    tep = get_endpoint(user)
    tep.cancel()
