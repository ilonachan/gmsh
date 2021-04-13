import asyncio
import functools
import logging
import importlib.util
import os
import re
import shlex
from os import listdir
from os.path import splitext, basename, abspath, join, isfile

from discord import Client, Message, Member, TextChannel
from discord.abc import GuildChannel, User
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from ezconf import cfg
from gmsh.discord import discord_handler

logger = logging.getLogger(__name__)

commands = {}


def register_command(command, names):
    global commands
    for name in names:
        commands[name] = command
    logger.debug('Loaded command %s from module %s', names, command.__module__)


def load_command(path):
    """
    Load commands from the python file at the specified location

    :param path: the location of the module
    """
    global commands
    module_name = load_command.__module__ + '.' + splitext(basename(path))[0]

    # remove the old versions of commands by that module from the registry
    unload_command(path)

    # do the python magic boogie-woogie
    spec = importlib.util.spec_from_file_location(module_name, abspath(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)


def unload_command(path):
    module_name = load_command.__module__ + '.' + splitext(basename(path))[0]

    # remove the old versions of commands by that module from the registry
    global commands
    commands = {key: value for key, value in commands.items() if value.__module__ != module_name}


class CommandReloadHandler(FileSystemEventHandler):
    def __init__(self):
        super(CommandReloadHandler, self).__init__()

    def on_moved(self, event):
        super(CommandReloadHandler, self).on_moved(event)
        if event.is_directory or not event.src_path.endswith('.py') or event.src_path.startswith('__'):
            return

        what = 'directory' if event.is_directory else 'file'
        logger.info("%s was moved from %s to %s, no action will be taken", what, event.src_path, event.dest_path)

    def on_created(self, event):
        super(CommandReloadHandler, self).on_created(event)
        if event.is_directory or not event.src_path.endswith('.py') or event.src_path.startswith('__'):
            return

        try:
            load_command(event.src_path)
            logger.info('Loaded commands from newly added module %s', event.src_path)
        except Exception as e:
            logger.error('Could not load new module %s', event.src_path, exc_info=True)
            raise e

    def on_deleted(self, event):
        super(CommandReloadHandler, self).on_deleted(event)
        if event.is_directory or not event.src_path.endswith('.py') or event.src_path.startswith('__'):
            return

        unload_command(event.src_path)

        logger.info('Command %s was unloaded', event.src_path)

    def on_modified(self, event):
        super(CommandReloadHandler, self).on_modified(event)
        if event.is_directory or not event.src_path.endswith('.py') or event.src_path.startswith('__'):
            return

        try:
            load_feature(event.src_path)
            logger.info('Reloaded commands from changed module %s', event.src_path)
        except Exception as e:
            logger.error('Could not reload module %s', event.src_path, exc_info=True)
            raise e


observer = Observer()


def load_all_commands(cmd_base):
    for file in [join(cmd_base, f) for f in listdir(cmd_base)]:
        if not isfile(file):
            if isfile(f'{file}/__init__.py'):
                load_command(f'{file}/__init__.py')
                logger.info(f'Loaded commands from module {file}')
            continue
        if basename(file).startswith('__'):
            continue
        load_command(file)
        logger.info(f'Loaded commands from module {file}')


class CmdUsage(Exception):
    """
    When writing a command function, throwing this exception will cause the wrapping class
    to print the command's usage in the current channel of the command's execution.

    This is a convenience method to simplify the handling of user input errors
    """
    pass


# magic decorator class
def gmsh_command(name, *, usage=None, aliases=None, mundane=False, **metadata):
    """
    This annotation marks an async function as a command for my bot,
    as well as register it automatically. As per this process, the command will
    be part of the auto-reload machinery

    The function will be wrapped by a class storing the command's metadata as state.
    This approach will make the addition of new commands incredibly straightforward,
    while still giving me a powerful interface to evolve commands in the future.

    :param name: the name of the command
    :param usage: a usage string to be printed when the command throws CmdUsage
    :param aliases: a list of alias names to be registered
    :param mundane: When set to True, the command can be called using the mundane syntax.
                    This syntax breaks the immersion, but allows users to more easily
                    access functional commands this bot presents
    :param metadata: other miscellaneous metadata to be stored in the command object.
                     The resulting dict will be passed to the command function as a named parameter.
    :return: the wrapping class that will be used to decorate the function,
             as required by the decorator syntax
    """
    if aliases is None:
        aliases = []

    class GmshCommand:
        def __init__(self, func):
            functools.update_wrapper(self, func)

            self.name = name
            self.usage = usage
            self.aliases = aliases
            self.metadata = metadata
            self.mundane = mundane
            self.func = func

            register_command(self, [self.name] + self.aliases)

        async def __call__(self, ctx, args, *pargs, **kwargs):
            try:
                return await self.func(ctx, args, *pargs, metadata=self.metadata, **kwargs)
            except CmdUsage:
                if self.usage is not None:
                    await ctx.message.reply(codify('usage: ' + self.usage, ctx.mundane), mention_author=False)
                else:
                    if ctx.mundane:
                        await ctx.message.reply('incorrect usage, but no help text was found', mention_author=False)
                    else:
                        await ctx.message.reply('```diff\n- incorrect usage, but no help text was found\n```', mention_author=False)
            except Exception as e:
                logger.error('error executing command ' + args[0], exc_info=True)
                raise e

    return GmshCommand


curr_typing = {}
typing_event = {}


async def typing_loop(channel: TextChannel):
    """
    Global typing loop for the provided channel:
    Will run until the respective event is notified and
    there are no more typing terminals left.
    :param channel:
    :return:
    """
    if len(curr_typing[channel.id]) > 1:
        return

    typing_event[channel.id] = asyncio.Event()
    logger.info(f'Started typing in channel {channel.name}')
    async with channel.typing():
        await typing_event[channel.id].wait()
        while len(curr_typing[channel.id]) > 0:
            typing_event[channel.id].clear()
            await typing_event[channel.id].wait()
    logger.info(f'Stopped typing in channel {channel.name}')
    del typing_event[channel.id]


def start_typing(handle, channel):
    """
    Activates the typing indicator in the given channel.
    """
    if channel.id not in curr_typing:
        curr_typing[channel.id] = []
    curr_typing[channel.id].append(handle)
    if channel.id not in typing_event:
        asyncio.create_task(typing_loop(channel))


def stop_typing(handle, channel=None):
    """
    Disables the typing indicator, if it was enabled by this terminal previously.
    """
    try:
        if channel is not None:
            if channel.id in curr_typing:
                curr_typing[channel.id].remove(handle)
            if channel.id in typing_event:
                typing_event[channel.id].set()
        else:
            for id in curr_typing:
                if handle in curr_typing[id]:
                    curr_typing[id].remove(handle)
                if id in typing_event:
                    typing_event[id].set()
    except ValueError:
        pass


class Terminal:
    def __init__(self, channel, mundane=False, call=None):
        self.channel = channel
        self.message = None
        self.call = call
        self.content = ''
        self.mundane = mundane

    def write(self, content):
        """
        Write the provided string to the terminal.
        :param content: what to print
        """
        self.content += content
        asyncio.get_event_loop().create_task(self.async_write(content))

    async def async_write(self, content):
        if self.message is None:
            if self.call is None:
                self.message = await self.channel.send(codify(content, self.mundane), allowed_mentions=None)
            else:
                self.message = await self.call.reply(codify(content, self.mundane),
                                                     allowed_mentions=None, mention_author=False)
        else:
            await self.message.edit(content=codify(self.content, self.mundane),
                                    allowed_mentions=None, mention_author=False)
        logger.debug(f'Sent message: {content}')

    def close(self):
        """
        Closes the terminal. Debating whether a closed terminal can be reopened.
        In the final product, stops typing.
        """
        logger.debug('Closed terminal')
        self.stop_typing()

    def start_typing(self):
        """
        Activates the typing indicator in the terminal's discord chat.
        """
        start_typing(self, self.channel)

    def stop_typing(self):
        """
        Disables the typing indicator, if it was enabled by this terminal previously.
        """
        stop_typing(self, self.channel)


class CommandContext:
    def __init__(self, channel: TextChannel, user: Member, client: Client, mundane: bool, message: Message = None,
                 env_map=None, commands=None):
        self.commands = commands or {}
        self.terminals = []
        self.dm_terminals = []
        self.channel = channel
        self.mundane = mundane
        self.user = user
        self.message = message
        self.env_map = env_map or {}
        self.client = client

    def new_terminal(self):
        term = Terminal(self.channel, self.mundane, self.message)
        self.terminals.append(term)
        logger.debug('Created new terminal')
        return term

    def dm_terminal(self):
        if self.user.dm_channel is None:
            self.user.create_dm()
        term = Terminal(self.user.dm_channel, self.mundane, self.message)
        self.dm_terminals.append(term)
        logger.debug('Created new DM terminal')
        return term

    def getvar(self, key):
        if key in self.env_map:
            return self.env_map[key]
        return None


cmd_pattern = re.compile(r'```(\w*)\s+(.*?)\s*```', re.MULTILINE)


def parse_command(content: str):
    m = cmd_pattern.match(content)
    if m is None:
        return None, None

    return m.group(2), m.group(1)


def codify(message: str, mundane: bool = False, language: str = ""):
    if mundane:
        return message
    else:
        return f'```{language}\n{message}\n```'


@discord_handler
async def on_message(client: Client, message: Message):
    global commands

    msg, lang = parse_command(message.content.strip())
    mundane = False

    if msg is None:
        if message.content.startswith('<<'):
            msg = message.content
            lang = None
            mundane = True
        else:
            return False
    elif lang.lower() not in ["gmsh", "sh", "cmd"] or not msg.startswith('$ '):
        return False

    msg = msg[2:].strip()

    if mundane:
        logger.info('Received command %s (mundane)', msg)
    else:
        logger.info('Received command %s (tag language: %s)', msg, lang)

    args = shlex.split(msg, comments=True, posix=False)
    if args[0].lower() not in commands:
        if mundane:
            return False

        await message.reply(codify('gmsh: command "' + args[0].lower() + '" not found'), mention_author=False)
        return True

    if mundane and not commands[args[0]].mundane:
        return False

    try:
        ctx = CommandContext(message.channel, message.author, client, mundane, message, env_map={}, commands=commands)
        await commands[args[0]](ctx, args)
    except CmdUsage:
        await message.reply(codify(commands[args[0]].usage(), mundane), mention_author=False)
    except Exception as e:
        logger.error(f'Exception while executing command line "{msg}"', exc_info=True)
        await message.reply(codify('Something went wrong while trying to process your request,'
                                   ' please try again later.\n'
                                   'If this error persists, please report it to '
                                   f'@{cfg.devs.nagato.discord_handle("Nagato_Yoshikage#2286")}.',
                                   mundane), mention_author=False)
        raise e
    return True


# bot module lifecycle function
# It would probably okay to move this logic to the top level,
# but then again maybe this makes more sense.
def load(old_module=None):
    cmd_base = os.path.dirname(__file__)
    load_all_commands(cmd_base)
    if old_module is None:
        event_handler = CommandReloadHandler()
        # observer.schedule(event_handler, cmd_base, recursive=False)
        # observer.start()