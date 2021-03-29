from discord import TextChannel, Message, Client, User, Member, Guild, Reaction, ChannelType
from discord.utils import get
import asyncio
import re

import gmsh.discord.commands

import logging
log = logging.getLogger(__name__)

endpoints = dict()


class TerminalEndpoint:

    def __init__(self, owner: User, client: Client):
        self.client = client
        self.owner = owner

        self.channel = None
        self.origin = None
        self.replying = False

        self.buffer = ''
        self.message = None

        self.code = False
        self.flushed = True
        self.line_break = False

        endpoints[owner.id] = self
        self.queue = []
        self.loop = None

    async def send(self):
        content = self.buffer
        if self.code:
            content = '```'+self.buffer+'```'
        if self.message is None or self.message.channel.id != self.channel.id:
            if self.replying and self.origin is not None and self.origin.channel.id == self.channel.id:
                await self.origin.reply(content)
            else:
                self.message = await self.channel.send(content)
        else:
            await self.message.edit(content=content, mention_author=False)
        self.flushed = True
        self.line_break = False

    async def exec(self, instructions: str = None):
        self.instructions = instructions.split('\n') if instructions is not None else ['']

        for line in self.instructions:
            if line.startswith('.'):
                m = re.match(r'^(..?\w+)\s*(.*)$', line)
                if m is None:
                    if line == '..':
                        self.line_break = True
                        continue
                    elif line == '.```':
                        continue
                if m.group(1) in ['.clear']:
                    self.buffer = ''
                    self.message = None
                    self.line_break = False
                    self.flushed = True
                    log.debug(f'tep u={self.owner.id}: cleared backlog')
                if m.group(1) in ['.code', '.c']:
                    self.code = True
                    log.debug(f'tep u={self.owner.id}: code=True')
                if m.group(1) in ['..code', '..c']:
                    self.code = False
                    log.debug(f'tep u={self.owner.id}: code=False')
                if m.group(1) in ['.type', '.t']:
                    gmsh.discord.commands.start_typing(self, self.channel)
                    log.debug(f'tep u={self.owner.id}: started typing in c={self.channel.id}')
                if m.group(1) in ['..type', '..t']:
                    gmsh.discord.commands.stop_typing(self, self.channel)
                    log.debug(f'tep u={self.owner.id}: stopped typing in c={self.channel.id}')
                if m.group(1) == '..tt':
                    gmsh.discord.commands.stop_typing(self)
                    log.debug(f'tep u={self.owner.id}: stopped typing in all channels')
                if m.group(1) in ['.send', '.s']:
                    await self.send()
                    log.debug(f'tep u={self.owner.id}: flushed content')
                if m.group(1) in ['.break', '.br', '.b']:
                    if not self.flushed:
                        await self.send()
                    self.buffer = ''
                    self.message = None
                    log.debug(f'tep u={self.owner.id}: breaking message')
                if m.group(1) in ['.channel', '.ch']:
                    if not self.flushed:
                        await self.send()
                    self.buffer = ''
                    guild_id, channel_id = m.group(2).split(' ')
                    guild: Guild = self.client.get_guild(int(guild_id.strip()))
                    self.channel = get(guild.text_channels, id=int(channel_id.strip()))
                    self.message = None
                    log.debug(f'tep u={self.owner.id}: switched to channel c={channel_id} in g={guild_id}')
                if m.group(1) in ['.wait', '.w']:
                    duration = float(m.group(2))
                    log.debug(f'tep u={self.owner.id}: waiting {duration}s')
                    await asyncio.sleep(duration)
                if m.group(1) in ['.waitmsg', '.wm']:
                    guild_id, channel_id, user_id, pattern = m.group(2).split(' ', maxsplit=3)

                    def check(msg: Message):
                        if guild_id == 'cur':
                            if msg.guild.id != self.channel.guild.id:
                                return False
                        elif guild_id != '*' and msg.guild.id != int(guild_id):
                            return False
                        if channel_id == 'cur':
                            if msg.channel.id != self.channel.id:
                                return False
                        elif channel_id != '*' and msg.channel.id != int(channel_id):
                            return False
                        if user_id == 'me':
                            if msg.author.id != self.owner.id:
                                return False
                        elif user_id != '*' and msg.author.id != int(user_id):
                            return False
                        if re.search(pattern, msg.content, re.DOTALL) is None:
                            return False
                        return True

                    log.debug(f'tep u={self.owner.id}: waiting for message by u={user_id} matching p={pattern} '
                              f'in g={guild_id},c={channel_id}')
                    self.origin = await self.client.wait_for('message', check=check)
                    log.debug(f'tep u={self.owner.id}: message found!')
                    if not self.flushed:
                        await self.send()
                    self.buffer = ''
                    self.channel = self.origin.channel
                if m.group(1) in ['.waitok', '.wo']:
                    def check(reaction: Reaction, user: User):
                        if user.id != self.owner.id:
                            return False
                        if reaction.emoji != '\u2705':
                            return False
                        if reaction.message.channel.type != ChannelType.private:
                            return False
                        return True

                    log.debug(f'tep u={self.owner.id}: waiting for ok by owner')
                    await self.client.wait_for('reaction_add', check=check)
                if m.group(1) in ['.reply', '.r']:
                    self.replying = True
                if m.group(1) in ['..reply', '..r']:
                    self.replying = False
            else:
                if line.startswith('\\.'):
                    line = line[1:]
                if self.line_break:
                    line = '\n'+line

                self.buffer += line
                self.flushed = False
                self.line_break = True

    def enqueue_script(self, content):
        self.queue.append(content)
        if self.loop is None or self.loop.done():
            self.loop = asyncio.ensure_future(self._script_queue())

    async def _script_queue(self):
        while len(self.queue) > 0:
            await self.exec(self.queue.pop(0))

    def cancel(self):
        self.loop.cancel()


def get_endpoint(owner: User, client: Client = None) -> TerminalEndpoint:
    if owner.id not in endpoints:
        if client is None:
            raise ValueError('Need discord.Client to initialize the Terminal Endpoint')
        TerminalEndpoint(owner, client)
    if client is not None and endpoints[owner.id].client != client:
        log.warning('Terminal Endpoint of a different client instance is reused. '
                    'I have no idea if this will cause armageddon, but it shouldn\'t have happened.')
    return endpoints[owner.id]
