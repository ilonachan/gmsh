import logging

import discord

from gmsh.discord import discord_handler

logger = logging.getLogger(__name__)


songs = ["""\
somebody once told me the world was gonna roll me
i ain't the sharpest tool in the shed
she was looking kinda dumb with her finger and her thumb
in the shape of an l on her forehead

well the ??? start coming and they don't stop coming

hey now you're an all star
get your game on go play
hey now you're a rockstar
get the show on get paid
and all that glitters is gold
only shooting stars break the mold
"""]


def song_tokens(song):
    return song.split()


def message_tokens(content):
    return content.split()


def consume_from_token(tokens, lyrics, location):
    if tokens[0].lower() == lyrics[location].lower():
        return True, tokens[1:], location + 1

    return False, tokens, location


class Song:
    def __init__(self):
        self.lyrics = None
        self.location = 0

    async def accept_message(self, content, channel):
        if self.lyrics is None:
            for song in songs:
                self.lyrics = song_tokens(song)
                if await self.accept_message(content, channel):
                    return True
                self.location = 0
            self.lyrics = None

            yall_role = discord.utils.find(lambda r: r.name == 'yall', channel.guild.roles)
            await channel.send('I don\'t know the lyrics to this song, have fun ' +
                               (yall_role.mention if yall_role is not None else '@yall'))
            return None

        old_loc = self.location

        tokens = message_tokens(content)
        while len(tokens) > 0:
            correct, tokens, self.location = consume_from_token(tokens, self.lyrics, self.location)
            if not correct:
                self.location = old_loc
                return False
        return True if self.location < len(self.lyrics) else None


channel_state = dict()


async def begin_singing(channel):
    channel_state[channel.id] = Song()
    logger.info('started singing')


async def process_lyrics(message):
    logger.info('got lyrics: %s', message.content)
    result = await channel_state[message.channel.id].accept_message(message.content, message.channel)
    if result is None:
        del channel_state[message.channel.id]
        logger.info('Song done')
        return
    if not result:
        # await message.add_reaction('❌')
        await message.delete()


@discord_handler
async def on_message(client, message):
    if message.channel.type != discord.ChannelType.text:
        return False
    if message.author.bot:
        return False

    if message.content == "ABORT SING" and message.channel.id in channel_state:
        del channel_state[message.channel.id]
        await message.channel.send('Understandable have a great day')
        return True

    if message.channel.id in channel_state:
        await process_lyrics(message)
        return True

    if message.content == "EVERYBODY SING":
        await begin_singing(message.channel)
        return True
