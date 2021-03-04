from sqlalchemy.engine import ResultProxy

from gmsh.database import sqlol_engine
from gmsh.discord import discord_handler
from gmsh.discord.commands import parse_command, codify


@discord_handler('on_message')
async def sqlol_handler(client, message):
    expr, lang = parse_command(message.content.strip())

    if expr is None or not lang.lower() == 'sql':
        return False

    with sqlol_engine.connect() as con:
        try:
            rs: ResultProxy = con.execute(expr)
            if rs.returns_rows:
                rows = rs.fetchall()
                result = f'{len(rows)} rows matched ('+', '.join(rs.keys())+')\n'+'\n'.join(str(r) for r in rows)
            else:
                result = 'Operation completed successfully'
            await message.channel.send(codify(result))
        except Exception as e2:
            await message.channel.send(codify(f'Could not execute command:\n{e2}'))
        return True
