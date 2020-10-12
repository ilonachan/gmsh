import functools
import inspect

import discord
import yaml
import logging

import gmsh_terminal.vault as vault

log = logging.getLogger(__name__)


with open('discord.yaml', 'r') as df:
    bot_cfg = yaml.safe_load(df.read())

intents = discord.Intents.all()


#
# Discord stuff
#
client = discord.Client(intents=intents)


handlers = {}


def add_handler(name, handler, priority=100):
    """
    Add the specified function to the Discord bot in order to have it be called in
    reaction to the named event specified. Optionally a priority can be set if a specific
    order of operations is necessary (default priority is 100)

    :param name: name of the event to be listened for
    :param handler: function to be called when the event occurs
    :param priority: priority number used for determining the order in which the handlers are called
    """
    if name is None:
        name = handler.__name__

    if name not in handlers:
        # The base handler opens the structure up for adding more than one handler
        async def base_handler(*args, **kwargs):
            for h in handlers[name]:
                if inspect.iscoroutinefunction(h):
                    if await h(client, *args, **kwargs):
                        break
                elif h(client, *args, **kwargs):
                    break
        base_handler.__name__ = name
        client.event(base_handler)
        handlers[name] = []

    if not inspect.iscoroutinefunction(handler):
        log.warning(f'The handler function \'{handler}\' to be registered for \'{name}\' is not async. '
                    'This severely limits the use of the discord.py API, and is thus discouraged. '
                    'The handler will still be added and executed as expected.')
    setattr(handler, 'priority', priority)
    setattr(handler, 'remove_handler', functools.partial(remove_handler, handler, name))
    handlers[name].append(handler)
    handlers[name].sort(key=lambda h: h.priority)
    log.info(f'Added handler function "{handler.__name__}"')


def remove_handler(handler, name=None):
    """
    Removes the specified handler function from the Discord bot, so it is no longer called
    when the specified named event occurs. If no name is specified, the handler is removed
    from all events it is registered for.

    :param handler: the handler function to be removed
    :param name: the event name which the handler was listening for, or None
    """
    if name is None:
        for lst in handlers.values():
            lst.remove(handler)

    if name not in handlers:
        return
    handlers[name].remove(handler)


def discord_handler(name=None, priority=100):
    """
    Convenience decorator which automatically adds the annotated function into a handler.

    :param name: The name of the event this handler should listen to. If it is None,
                 the function's name will be used instead. In that case this parameter
                 also accepts the callable itself, allowing the user to omit calling the decorator itself.
    :param priority: The priority used to determine the order in which handlers are called. Default is 100.
    :return: the original function for further use
    """
    def register_handle(func):
        add_handler(name, func, priority)
        return func

    if hasattr(name, '__call__'):
        handler = name
        name = None
        return register_handle(handler)

    return register_handle


@discord_handler('on_ready')
async def server_init(client):
    log.info('Logged on as {0}!'.format(client.user))

    # I've always wanted to do this \^o^/
    activity = discord.Activity(name='terminal endpoints', type=discord.ActivityType.watching)
    await client.change_presence(activity=activity)


def start():
    if bot_cfg['devenv']:
        key = bot_cfg['prod_token'] + ':' + bot_cfg['secret']
        vault.prepare(key)
    else:
        key = bot_cfg['token'] + ':' + bot_cfg['secret']
    vault.unlock(key)

    # https://discord.com/api/oauth2/authorize?client_id=754288259265200160&permissions=738323520&scope=bot
    client.run(bot_cfg['token'])
