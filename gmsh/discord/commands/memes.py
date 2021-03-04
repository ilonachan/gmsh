import asyncio
import re

from gmsh.discord.commands import gmsh_command, CmdUsage, codify, CommandContext


@gmsh_command('jojo', usage='jojo <is this a jojos reference>')
async def jojo_command(ctx, args, **kwargs):
    term = ctx.new_terminal()
    term.write('Holy shit, was that a motherfucking JoJo\'s Reference!?')
    term.close()


worldline = '1.039285'
secs_start = 0
secs_left = 60 * 1


@gmsh_command('wltool', usage='wltool read | reset')
async def wltool_command(ctx, args, **kwargs):
    term = ctx.new_terminal()
    if len(args) < 2:
        raise CmdUsage()
    if args[1] == 'read':
        term.write('Worldline value: ' + worldline)
    elif args[1] == 'reset':
        if ctx.getvar('sudo'):
            await visible_genwl(term)
        else:
            term.write(
                'ERROR: could not modify /domain/rs:c137/wl/wl.conf: not permitted\n' +
                'Try running the command again with sudo')
    else:
        raise CmdUsage()
    term.close()


async def visible_genwl(term):
    term.start_typing()
    term.write('Resetting worldline...')
    await asyncio.sleep(10)
    generate_worldline()
    term.write('Reset complete\nNew worldline: ' + worldline)
    term.stop_typing()


def generate_worldline():
    global worldline, secs_start, secs_left
    worldline = '1.039285'
    secs_start = 0
    secs_left = 60 * 1


@gmsh_command('log', usage='log start | stop')
async def log_command(ctx, args, **kwargs):
    term = ctx.new_terminal()
    if len(args) < 2:
        raise CmdUsage()
    if args[1] == 'start':
        term.write('Beginning new protocol for future reference')
    elif args[1] == 'stop':
        term.write('Saved protocol as "sevenfour-20200909.log')
    else:
        raise CmdUsage()
    term.close()


mention_pattern = re.compile(r'<@!?(\d+)>', re.MULTILINE)


@gmsh_command('stealpfp', usage='usage: stealpfp <@USERID> # just tag someone', mundane=True)
async def stealpfp_command(ctx: CommandContext, args, **kwargs):
    m = mention_pattern.match(args[1])
    if m is None:
        await ctx.channel.send(codify(f'No valid mention was specified', ctx.mundane))
        return

    userid = int(m.group(1))
    usr = ctx.client.get_user(userid)
    if usr is None:
        await ctx.channel.send(codify(f'Could not get user', ctx.mundane))
        return
    if usr.avatar is None:
        await ctx.channel.send(codify(f'The user {usr} has not set an avatar', ctx.mundane))
        return
    await ctx.channel.send(f'https://cdn.discordapp.com/avatars/{usr.id}/{usr.avatar}.png?size=1024')
    return


@gmsh_command('countrole', usage='usage: countrole @role_mention', mundane=True)
async def countrole_command(ctx: CommandContext, args, **kwargs):
    term = ctx.new_terminal()
    for role in ctx.message.role_mentions:
        term.write(f'Role {role.mention} has {len(role.members)} members')
    term.close()


@gmsh_command('bubblewrap', usage='usage: bubblewrap <width>x<height> [<text to use as bubbles>]', mundane=True)
async def bubblewrap_command(ctx: CommandContext, args, **kwargs):
    match = re.fullmatch(r'(\d+)x(\d+)', args[1] if len(args) > 1 else '')
    width, height = (int(match.group(1)), int(match.group(2))) if match is not None else (4, 6)
    text = args[2] if len(args) > 2 else 'pop'
    result = (('||'+text+'||')*width+'\n')*height
    if len(result) > 2000:
        await ctx.channel.send('That bubble wrap would be too large to be sent through Discord')
    await ctx.channel.send(result)
