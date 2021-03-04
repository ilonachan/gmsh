from gmsh.discord.commands import gmsh_command

@gmsh_command('cookies', usage='cookies')
async def cookies_func(ctx, args, metadata=None):
    term = ctx.new_terminal()
    term.write('Cookies!!!')
    term.close()
