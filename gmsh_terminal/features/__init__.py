import discord

from gmsh_terminal.features.dpyserver import discord_handler
import gmsh_terminal.vault as vault


@discord_handler('on_message')
async def k_name_handler(client, message):
    if vault.vault['k_real_name'] in message.content.lower() or \
            (message.author.id == 368764120981307393 and 'pls summon puro' == message.content.lower()):
        await message.delete()
        puro = discord.utils.find(lambda m: m.id == 480160612022747136, message.guild.members)
        msg = await message.channel.send(f'Congrats {message.author.mention}, you did it!' +
                                         (f'\n{puro.mention}, you have been summoned!' if puro is not None else ''))
        await msg.add_reaction('\U0001F973')  # party-face
