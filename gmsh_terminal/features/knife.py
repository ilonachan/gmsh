import logging

from gmsh_terminal.features import commands
from gmsh_terminal.features.dpyserver import discord_handler

logger = logging.getLogger(__name__)


def load_feature(old_module=None):
    pass


def unload_feature():
    pass


async def request_answer(user, channel, client, statement):
    async with channel.typing():
        request = await user.send('```\nReceived unknown KNIFE request:\n' + statement +
                                  '\nPlease type your answer as a single message.```')
        msg = await client.wait_for('message', check=lambda m: m.channel == request.channel and
                                                               m.author == user)
        logger.info(msg.content)
        await channel.send('```\n' + msg.content + '\n```')


@discord_handler
async def on_message(client, message):
    msg, lang = commands.parse_command(message.content.strip())

    if msg is None or lang.lower() not in ['dm', 'dmb']:
        return False

    logger.info('knife request:\n' + msg)

    await request_answer(message.author, message.channel, client, msg)
