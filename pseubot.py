from typing import Union, List

import pyrogram
from pyrogram import Client, filters, types

import json

bot = Client('pseubot', 0, '', bot_token="")

CHAT_ID = -1001202081371
FILENAME = 'restricted_members.json'


def chat_command(commands: Union[str, List[str]]):
    return filters.command(commands) & filters.chat(CHAT_ID) & ~filters.edited


def owner_command(commands: Union[str, List[str]]):
    return chat_command(commands) & filters.user('eugenenum1')


async def promote_member(chat, author):
    await chat.promote_member(
        user_id=author.id,
        can_manage_chat=False,
        can_change_info=False,
        can_delete_messages=False,
        can_restrict_members=False,
        can_invite_users=True,
        can_promote_members=False,
        can_manage_voice_chats=False
    )


async def set_title(message, chat, author, title):
    for _ in range(2):
        try:
            return await bot.set_administrator_title(
                chat_id=chat.id,
                user_id=author.id,
                title=title
            )
        except pyrogram.errors.exceptions.bad_request_400.ChatAdminRequired:
            await message.reply("Couldn't set the title."
                                "\nAny one of these is a reason:"
                                "\n- I am not an administrator"
                                "\n- I cannot add new administrators"
                                "\n- You are already an administrator. Ask admin to dismiss you.")
            return False
        except pyrogram.errors.exceptions.bad_request_400.UserCreator:
            await message.reply("I cannot set your title, creator.")
            return False
        except pyrogram.errors.exceptions.bad_request_400.AdminRankInvalid:
            await message.reply("Your title is invalid or is longer than 16 characters.")
            return False
        except ValueError:
            await promote_member(chat, author)


@bot.on_message(filters.chat(CHAT_ID) & filters.new_chat_members)
async def on_new_member(_, message: types.Message):
    member = message.new_chat_members[0]
    await bot.send_message(
        message.chat.id,
        f"Привет, {member.first_name}. В чате есть placeholder. Сдохни командой /set."
    )


@bot.on_message(chat_command(["set", "change"]))
async def set_title_command(_, message: types.Message):
    author = message.from_user

    with open(FILENAME) as file:
        restricted = json.load(file)
        if author.id in restricted:
            await message.reply("You are restricted from changing your title.")
            return

    args = message.command[1:]
    if not args:
        await message.reply("Title is not specified.")
        return

    title = ' '.join(args)
    print(title)

    chat = message.chat

    if result := await set_title(message, chat, author, title):
        await message.reply(f"Your title has been successfully set to `{title}`.")
    elif result is False:
        pass
    else:
        await message.reply(f"Something went wrong.")


@bot.on_message(owner_command(["restrict_member", "unrestrict_member"]))
async def un_restrict_member_command(_, message: types.Message):
    if entities := message.entities:
        if len(entities) < 2:
            await message.reply("You haven't specified any members.")
            return

        restrict = False if message.command[0].startswith('un') else True

        with open(FILENAME, 'r+') as file:
            members = json.load(file)
            entity = entities[1]
            chat = message.chat
            if entity.type == 'mention':
                offset = entity.offset
                member = message.text[offset:offset + entity.length]
                try:
                    member = await chat.get_member(member)
                except pyrogram.errors.exceptions.bad_request_400.UserNotParticipant:
                    await message.reply("Specified user is not a member of this chat.")
                    return
                member = member.user
            elif entity.type == 'text_mention':
                member = entity.user

            if member:
                if restrict:
                    if member.id in members:
                        await message.reply("Specified member is already restricted.")
                        return
                    members.append(member.id)
                else:
                    if member.id not in members:
                        await message.reply("Specified member is not restricted.")
                        return
                    members.remove(member.id)
                file.seek(0)
                file.truncate()
                json.dump(members, file)
                await message.reply(f"Successfully {'un' if not restrict else ''}restricted access to the specified user.")
            else:
                await message.reply(f"No new users have been {'un' if not restrict else ''}restricted.")


bot.run()
