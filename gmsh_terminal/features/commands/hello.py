from gmsh_terminal.features.commands import gmsh_command


@gmsh_command('hello', usage='hello [<name>...]', mundane=True)
async def hello_cmd(ctx, args, metadata=None):
    term = ctx.new_terminal()

    if len(args) == 1:
        if ctx.mundane:
            name = ctx.user.mention
        else:
            name = 'Admin' if ctx.getvar('sudo') else ctx.user.nick or ctx.user.name
        term.write(f'Hello {name}!')

    for name in args[1:]:
        term.write(f'Hello {name}!')

    term.close()
