import datetime

import discord
from discord import CategoryChannel, VoiceChannel, TextChannel, Role, Guild, Message, RawReactionActionEvent, Client, \
    Member, PartialEmoji
from discord.utils import find, get
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

from gmsh_terminal.features import database
from gmsh_terminal.features.dpyserver import discord_handler
from gmsh_terminal.features.commands import gmsh_command, CmdUsage, CommandContext, codify

proficiency_emojis = None


def get_emoji(proficiency, ctx):
    global proficiency_emojis
    if proficiency_emojis is None:
        proficiency_emojis = {
            0: '1️⃣',
            1: '2️⃣',
            2: '3️⃣',
            3: '4️⃣'
        }
    if proficiency not in proficiency_emojis:
        return None
    return proficiency_emojis[proficiency]


def get_proficiency_by_emoji(emoji: PartialEmoji):
    global proficiency_emojis
    if proficiency_emojis is None:
        proficiency_emojis = {
            0: '1️⃣',
            1: '2️⃣',
            2: '3️⃣',
            3: '4️⃣'
        }

    if emoji.is_unicode_emoji():
        for key in proficiency_emojis:
            if proficiency_emojis[key] == emoji.name:
                return key
    return None


async def send_react_msg(ctx, subject):
    text = f'__**Subject: {subject.name}**__\n' + \
           f'Please react with one of the following to obtain a role ' + \
           f'denoting your proficiency in this subject:\n\n' + \
           '\n'.join(f'{get_emoji(role.proficiency, ctx)} {role.name}' for role in subject.roles)

    message: Message = await get(ctx.channel.guild.text_channels, name='hub', category__name='tutoring').send(text)
    for role in subject.roles:
        await message.add_reaction(get_emoji(role.proficiency, ctx))

    await message.pin()

    return database.ReactionMessage(id=message.id, subject=subject)


@discord_handler(name='on_raw_reaction_add')
async def handle_react_msg_pos(client: Client, payload: RawReactionActionEvent):
    session = database.DefaultSession()
    try:
        subject = session.query(database.Subject).join(database.ReactionMessage)\
            .filter(database.ReactionMessage.id == payload.message_id).one()
    except MultipleResultsFound:
        return False
    except NoResultFound:
        return False

    proficiency = get_proficiency_by_emoji(payload.emoji)

    guild: Guild = get(client.guilds, id=payload.guild_id)
    role = guild.get_role(get(subject.roles, proficiency=proficiency).id)
    user: Member = guild.get_member(payload.user_id)
    await user.add_roles(role)
    session.close()


@discord_handler(name='on_raw_reaction_remove')
async def handle_react_msg_neg(client: Client, payload: RawReactionActionEvent):
    session = database.DefaultSession()
    try:
        subject = session.query(database.Subject).join(database.ReactionMessage)\
            .filter(database.ReactionMessage.id == payload.message_id).one()
    except MultipleResultsFound:
        return False
    except NoResultFound:
        return False

    proficiency = get_proficiency_by_emoji(payload.emoji)

    guild: Guild = get(client.guilds, id=payload.guild_id)
    role = guild.get_role(get(subject.roles, proficiency=proficiency).id)
    user: Member = guild.get_member(payload.user_id)
    await user.remove_roles(role)
    session.close()


async def subject_section(ctx, args):
    if len(args) < 3:
        raise CmdUsage()
    if args[2].lower() == 'create':
        if len(args) < 4:
            raise CmdUsage()
        session = database.DefaultSession()
        subject = database.Subject(name=' '.join(args[3:]))
        roles = [await ctx.channel.guild.create_role(name=subject.name+' - '+level)
                 for level in ['Needs Help', 'Beginner', 'Advanced', 'Tutor']]
        subject.roles = [database.TutorRoles(id=role.id, name=role.name, proficiency=i)
                         for i, role in enumerate(roles)]
        subject.reactmsg = [await send_react_msg(ctx, subject)]
        session.add(subject)
        session.commit()
        await ctx.message.channel.send(f'Subject "{subject.name}" created (database ID is {subject.id})')


async def create_room(ctx, name, private, members, create_vc=True):
    """
    Creates a new breakout room in the specified context. This includes:
    - a text channel <name>,
    - a voice channel <name>-v if create_vc is True, and
    - a role <name>-role, if len(members)>0.

    If members have been specified, they will be assigned the <name>-role role, which is pinged right afterwards.
    All specified members which are currently in the tutor hub voice channel will be dragged to <name>-vc.
    If private is True, the text and voice channel's role overrides will be adapted
    so only the specified members (ie the members of the <name>-role) have read access.
    For this reason it is an error to set private to True but not specify any members.

    :param create_vc:
    :param ctx:
    :param name:
    :param private:
    :param members:
    :return:
    """
    if len(members) == 0 and private:
        await ctx.message.channel.send('To create a private breakout room you must mention the participants,'
                                       'otherwise nobody will be able to access the room.')
        return

    guild: Guild = ctx.message.guild
    tutoring_category: CategoryChannel = get(guild.categories, name='tutoring')
    tutoring_hub: TextChannel = get(tutoring_category.text_channels, name='hub')
    tutoring_hub_vc: VoiceChannel = get(tutoring_category.voice_channels, name='hub-vc')

    if get(tutoring_category.text_channels, name=name) is not None:
        await ctx.message.channel.send('A breakout room by that name already exists')
        return

    br_text = await tutoring_category.create_text_channel(name)
    br_voice: VoiceChannel = None
    if create_vc:
        br_voice: VoiceChannel = get(tutoring_category.voice_channels, name=name+'-vc')
        if br_voice is not None:
            await ctx.message.channel.send('Inconsistency: A voice channel for that breakout room exists already. '
                                           'It will be deleted.')
            for user in br_voice.members:
                await user.move_to(tutoring_hub_vc)
            await br_voice.delete(reason='Fixing inconsistent Guild structure')
        br_voice = await tutoring_category.create_voice_channel(name + '-vc')

    if len(members) > 0:
        br_role: Role = get(guild.roles, name=name+'-role')
        if br_role is not None:
            await ctx.message.channel.send('Inconsistency: A role for that breakout room exists already. '
                                           'It will be deleted.')
            await br_role.delete(reason='Fixing inconsistent Guild structure')
        br_role: Role = await guild.create_role(name=name + '-role')
        for user in members:
            await user.add_roles(br_role)
            # move members currently talking in the hub to the breakout room
            if create_vc and user.voice is not None and user.voice.channel.id == tutoring_hub_vc.id:
                await user.move_to(br_voice)

        if private:
            await br_text.set_permissions(guild.default_role, view_channel=False)
            await br_text.set_permissions(br_role, view_channel=True)
            if create_vc:
                await br_voice.set_permissions(guild.default_role, view_channel=False, connect=False)
                await br_voice.set_permissions(br_role, view_channel=True, connect=True)

        await br_text.send(br_role.mention + ': Breakout Room created. To close it please use\n'
                                             f'<<tutor rooms (close|archive) {name}\n'
                                             '(name optional if executed in here)')
    else:
        await br_text.send('Breakout Room created. To close it please use\n'
                           f'<<tutor rooms (close|archive) {name}\n'
                           '(name optional if executed in here)')

    await ctx.channel.send(f'Breakout Room {br_text.mention} created. To close it please use\n'
                           f'<<tutor rooms (close|archive) {name}')


async def delete_room(ctx, name, archive):
    guild: Guild = ctx.message.guild
    tutoring_category: CategoryChannel = get(guild.categories, name='tutoring')
    archive_category: CategoryChannel = get(guild.categories, name='archived channels')
    tutoring_hub: TextChannel = get(tutoring_category.text_channels, name='hub')
    tutoring_hub_vc: VoiceChannel = get(tutoring_category.voice_channels, name='hub-vc')

    br_text: TextChannel = get(tutoring_category.text_channels, name=name)
    if br_text is None:
        await ctx.message.channel.send(f'Breakout Room "{name}" does not exist')
        return

    if archive:
        await br_text.edit(name=name+'-'+str(datetime.datetime.now()),
                           category=archive_category, reason='Breakout Room closed')
    else:
        await br_text.delete(reason='Breakout Room closed')

    br_voice: VoiceChannel = get(tutoring_category.voice_channels, name=name+'-vc')
    if br_voice is not None:
        for user in br_voice.members:
            await user.move_to(tutoring_hub_vc)
        await br_voice.delete(reason='Breakout Room closed')

    br_role: Role = get(guild.roles, name=name+'-role')
    if br_role is not None:
        await br_role.delete(reason='Breakout Room closed')

    await tutoring_hub.send(f'Breakout Room {name} closed.')


async def rooms_section(ctx: CommandContext, args):
    if len(args) < 3:
        raise CmdUsage()
    if args[2].lower() == 'create':
        mentions = ctx.message.mentions
        for role in ctx.message.role_mentions:
            mentions += role.members

        await create_room(ctx, args[4], args[3].lower() in ['private', 'prv'], mentions)
    elif args[2].lower() in ['delete', 'archive']:
        if len(args) > 3:
            names = args[3:]
        elif ctx.channel.category is not None and ctx.channel.category.name == 'tutoring':
            names = [ctx.channel.name]
        else:
            await ctx.message.channel.send('The current channel is not a breakout room, '
                                           'and no breakout room to close was specified')
            return

        for name in names:
            if name == 'hub':
                await ctx.message.channel.send('The hub is not a breakout room and cannot be closed')
                return
            await delete_room(ctx, name, args[2].lower() == 'archive')
    elif args[2].lower() == 'topic':
        if ctx.channel.category is None or ctx.channel.category.name != 'tutoring' or ctx.channel.name == 'hub':
            await ctx.message.channel.send('This command can only change the topic of breakout rooms')
            return
        if len(args) < 4:
            await ctx.message.channel.send('Please specify a topic to set for this breakout room')
            return
        await ctx.channel.edit(topic=' '.join(args[3:]))
        await ctx.message.channel.send('Topic set')
    elif args[2].lower() == 'call':
        if ctx.channel.category is None or ctx.channel.category.name != 'tutoring' or ctx.channel.name == 'hub':
            await ctx.message.channel.send('This command can only be used in breakout rooms')
            return
        mentions = ctx.message.mentions
        for role in ctx.message.role_mentions:
            mentions += role.members

        br_role = get(ctx.channel.guild.roles, name=ctx.channel.name+'-role')
        if br_role is not None:
            for user in mentions:
                await user.add_roles(br_role)
    else:
        raise CmdUsage()


@gmsh_command('tutor', mundane=True, usage='tutor (subject | room | board | help) [...]')
async def tutor(ctx, args, metadata=None):
    if len(args) < 2:
        raise CmdUsage()
    if args[1].lower() == 'subject':
        await subject_section(ctx, args)
    elif args[1].lower() == 'room':
        await rooms_section(ctx, args)
    elif args[1].lower() == 'board':
        pass
    elif args[1].lower() == 'help':
        pass
    else:
        raise CmdUsage()
