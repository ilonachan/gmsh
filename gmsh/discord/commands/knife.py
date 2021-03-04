import logging

from gmsh.discord.commands import gmsh_command, CmdUsage

logger = logging.getLogger(__name__)


async def request_answer(terminal, ctx, statement):
    request = await ctx.user.send('```\nReceived unknown KNIFE request:\n' + statement +
                                  '\nPlease type your answer as a single message.```')
    msg = await ctx.client.wait_for('message', check=lambda m: m.channel == request.channel and
                                                               m.author == ctx.user)
    logger.info(msg.content)
    await terminal.channel.send('```\n' + msg.content + '\n```')


async def knife_single(terminal, ctx, statement):
    async with terminal.channel.typing():
        await request_answer(terminal, ctx, statement)


async def knife_loop(terminal, ctx):
    while True:
        msg = await ctx.client.wait_for('message', check=lambda m: m.channel == terminal.channel and
                                                                   m.author == ctx.user)
        logger.info(f'Received message: {msg.content}')
        # Single-response Timed Opt-out Protocol
        if msg.content == '```\n$ knife stop\n```':
            await terminal.channel.send('```\nStopped listening for commands.\nThank you for using '
                                        '"KNIFE: the New Interactive Functional Environment"\n```')
            return

        await request_answer(terminal, ctx, msg.content)


@gmsh_command('knife', usage='knife stab | init | stop')
async def execute(ctx, args, **kwargs):
    term = ctx.new_terminal()
    if len(args) == 1:
        raise CmdUsage()

    # Single-use Terminal Accessor Bounce
    if args[1] == 'stab':
        await knife_single(term, ctx, ' '.join(args[1:]))
        return
    # Inline Nonintrusive Interactive Terminal
    elif args[1] == 'init':
        term.write('Started listening for commands.')
        await knife_loop(term, ctx)
        return
    elif args[1] == 'stop':
        return
    raise CmdUsage()
