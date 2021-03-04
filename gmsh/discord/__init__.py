import functools
import inspect

import discord
import logging

from gmsh.config import cfg

log = logging.getLogger(__name__)

intents = discord.Intents.all()


#
# Discord stuff
#
client = discord.Client(intents=intents)

handlers_base = {}
handlers = {}
handlers_dirty = {}


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
            # This is not necessary, but I'll sleep better knowing that I don't sort on every insert
            if handlers_dirty[name]:
                handlers[name].sort(key=lambda h: h.priority)
                handlers_dirty[name] = False
            for h in handlers[name]:
                try:
                    if inspect.iscoroutinefunction(h):
                        if await h(client, *args, **kwargs):
                            break
                    elif h(client, *args, **kwargs):
                        break
                except Exception as e:
                    log.error('Error executing handler', exc_info=e)
        base_handler.__name__ = name
        handlers_base[name] = base_handler
        client.event(base_handler)
        handlers[name] = []

    h = handler
    if not inspect.iscoroutinefunction(handler):
        log.warning(f'The handler function \'{handler}\' to be registered for \'{name}\' is not async. '
                    'This severely limits the use of the discord.py API, and is thus discouraged. '
                    'The handler will still be added and executed as expected.')

        # If I wrap the handler as I add it, I don't need to
        # have any logic in the actual handler loop
        async def async_handler(client, *args, **kwargs):
            return handler(client, *args, **kwargs)
        h = async_handler
        h.__name__ = handler.__name__

    setattr(h, 'priority', priority)
    setattr(h, 'remove_handler', functools.partial(remove_handler, h, name))
    handlers[name].append(h)
    handlers_dirty[name] = True
    log.info(f'Added handler function "{h.__name__}"')


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
    # Wait, this link only makes sense with that specific bot token?
    # https://discord.com/api/oauth2/authorize?client_id=754288259265200160&permissions=738323520&scope=bot
    try:
        client.run(cfg.discord.bot_token())
    except KeyError:
        log.error('No bot token was specified; the Discord bot can not be started.')
