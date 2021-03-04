import logging

import discord
from discord import Permissions

from gmsh.config import cfg
from gmsh.discord.commands import CmdUsage, gmsh_command, codify, CommandContext

logger = logging.getLogger(__name__)


@gmsh_command('help', usage='help <command>')
async def help_command(ctx, args, metadata=None):
    term = ctx.new_terminal()
    if len(args) < 2:
        raise CmdUsage()
    if args[1] not in ctx.commands:
        term.write(f'Command {args[1]} not found')
    else:
        term.write(ctx.commands[args[1]].usage())
    term.close()


@gmsh_command('sudo', usage='sudo <command> [<args>...]')
async def sudo_command(ctx, args, metadata=None):
    term = ctx.new_terminal()
    if can_sudo(ctx):
        ctx.env_map['sudo'] = True
    else:
        term.write(f'User "{ctx.user}" is not in the sudoers list\nThis incident will be reported')
        return
    term.close()

    if len(args) < 2:
        raise CmdUsage()

    if args[1] not in ctx.commands:
        term.write(f'sudo: command "{args[1]}" not found')
        return
    await ctx.commands[args[1]](ctx, args[1:])


def can_sudo(ctx):
    if ctx.user.id == ctx.channel.guild.owner.id:
        logger.debug('User "%s" is the owner of guild "%s", can sudo', ctx.user, ctx.channel.guild)
        return True

    if ctx.user.permissions_in(ctx.channel).administrator:
        logger.debug('User "%s" has administrator permissions, can sudo', ctx.user)
        return True

    for role in ctx.user.roles:
        if role.name in ['sudoers']:
            logger.debug('User "%s" has role "%s", can sudo', ctx.user, role.name)
            return True

    return False


@gmsh_command('which', usage='which <program> [<program>...]')
async def which_command(ctx, args, metadata=None):
    term = ctx.new_terminal()

    if len(args) < 2:
        raise CmdUsage()
    res = ''
    for el in args[1:]:
        if el not in ctx.commands:
            res += f'<command {el} not found>\n'
        else:
            res += f'/domain/global:ns01/bin/{el}\n'

    term.write(res)

    term.close()


@gmsh_command('env', usage='env [OPTIONS...]')
async def env_command(ctx, args, metadata=None):
    term = ctx.new_terminal()
    term.write('GodMode SHell v0.1 alpha\n'
               'author: @Nagato\n'
               'uuid: 9483-49238599-349283744-9382')

    term.close()


@gmsh_command('invite', mundane=True)
async def invite_command(ctx: CommandContext, args, metadata=None):
    await ctx.message.reply(discord.utils.oauth_url(ctx.client.user.id, Permissions(cfg.discord.permissions(0))))
