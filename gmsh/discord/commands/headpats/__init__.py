import re
import io
import aiohttp

import importlib.resources

from PIL import Image

from gmsh.discord.commands import gmsh_command, codify, CommandContext
import discord

mention_pattern = re.compile(r'<@!?(\d+)>', re.MULTILINE)


async def fetch_avatar_image(usr: discord.User, size=1024) -> Image:
    if usr is None:
        raise ValueError('No user specified')
    if usr.avatar is None:
        return None

    async with aiohttp.ClientSession() as session:
        session: aiohttp.ClientSession
        async with session.get(f'https://cdn.discordapp.com/avatars/{usr.id}/{usr.avatar}.png?size={size}') as resp:
            test = await resp.read()
            with io.BytesIO() as f:
                f.write(test)
                f.seek(0)
                res: Image = Image.open(f)
                res.load()
                return res


# This warrants its own file
@gmsh_command('headpat', usage='usage: headpat <@USERID> # just tag someone', mundane=True)
async def headpat_command(ctx: CommandContext, args, **kwargs):
    pet0: Image = Image.open(importlib.resources.open_binary('gmsh.discord.commands.headpats',
                                                             'pet0.gif'))

    m = mention_pattern.match(args[1])
    if m is None:
        await ctx.message.reply(codify(f'No valid mention was specified', ctx.mundane), mention_author=False)
        return

    userid = int(m.group(1))
    usr = ctx.client.get_user(userid)

    if usr is None:
        return
    avtr = await fetch_avatar_image(usr)
    if avtr is None:
        return

    res = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    avtr = avtr.convert("RGBA").resize((350, 350))
    res.paste(avtr, (75, 150), avtr)
    pet0 = pet0.convert("RGBA").resize((450, 450))
    res.paste(pet0, (0, 0), pet0)

    with io.BytesIO() as image_binary:
        res.save(image_binary, 'PNG')
        image_binary.seek(0)
        await ctx.channel.send(file=discord.File(fp=image_binary, filename='image.png'))