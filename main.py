import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher, F, BaseMiddleware
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode, ChatType, ChatMemberStatus
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import CommandStart, Command, IS_MEMBER
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, InlineKeyboardButton, CallbackQuery, BotCommand, \
    BotCommandScopeChat, BotCommandScopeAllPrivateChats
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import settings
from filters import IsAdminFilter
from models import db, Region, District, User, Channel

dp = Dispatcher()


class JoinChannelRequiredMiddleware(BaseMiddleware):
    def __init__(self) -> None:
        self.channel_list = []
        for channel in Channel.get_all():
            self.channel_list.append(channel.chat_id)

    async def __call__(self, handler, event: Message, data):
        user = User.get(event.from_user.id)
        if user and user.is_admin:
            return await handler(event, data)

        ikm = InlineKeyboardBuilder()
        for channel_id in self.channel_list:
            member = await event.bot.get_chat_member(channel_id, event.from_user.id)
            if member.status not in (ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR):
                channel = await event.bot.get_chat(channel_id)
                ikm.row(InlineKeyboardButton(text=channel.full_name, url=channel.invite_link))

        ikm.row(InlineKeyboardButton(text="Azo bo'ldim ✅", callback_data='joined_channels'))
        await event.answer('Kanalda azo boling', reply_markup=ikm.as_markup())
        return None


@dp.message(CommandStart(), IsAdminFilter())
async def cmd_start(message: Message):
    await message.answer("Admin xush kelibsiz")


@dp.message(Command('channel'), IsAdminFilter())
async def cmd_start(message: Message, bot: Bot):
    channels = Channel.get_all()
    ikm = InlineKeyboardBuilder()
    for channel in channels:
        channel = await bot.get_chat(channel.chat_id)
        ikm.row(*[
            InlineKeyboardButton(text=channel.full_name, url=channel.invite_link),
            InlineKeyboardButton(text='edit', callback_data=f'channel_edit_{channel.id}'),
            InlineKeyboardButton(text='del', callback_data=f'channel_delete_{channel.id}')
        ])
    ikm.row(
        InlineKeyboardButton(text='add', callback_data=f'channel_add_'),
    )

    await message.answer("Kanallar royhati", reply_markup=ikm.as_markup())


class AddChannel(StatesGroup):
    username = State()


@dp.message(CommandStart())
async def start_handler(message: Message):
    data = message.from_user.model_dump(include={'id', 'first_name', 'last_name', 'username'})
    user, created = User.get_or_create(**data)

    ikm = InlineKeyboardBuilder()
    regions = Region.get_all()

    for region in regions:
        ikm.row(InlineKeyboardButton(text=region.name, callback_data=f'region_{region.id}'))
    await message.answer('Viloyatlarni tanlang', reply_markup=ikm.as_markup())


@dp.callback_query(F.data.startswith('joined_channels'))
async def channel_add_callback(callback: CallbackQuery, bot: Bot):
    ikm = InlineKeyboardBuilder()
    has_not_joined = False
    for channel in Channel.get_all():
        member = await bot.get_chat_member(channel.chat_id, callback.from_user.id)
        if member.status not in (ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR):
            channel = await bot.get_chat(channel.chat_id)
            has_not_joined = True
            ikm.row(InlineKeyboardButton(text=channel.full_name, url=channel.invite_link))

    ikm.row(InlineKeyboardButton(text="Azo bo'ldim ✅", callback_data='joined_channels'))
    if has_not_joined:
        await callback.message.edit_text('Azo bolmagan kanallar', reply_markup=ikm.as_markup())
    else:
        await callback.message.delete()
        await start_handler(callback.message)


@dp.callback_query(F.data.startswith('channel_add_'))
async def channel_add_callback(callback: CallbackQuery, bot: Bot, state: FSMContext):
    await state.set_state(AddChannel.username)
    await callback.message.answer('Kanal username ni kiriting (kanalda bot admin bolishi shart!)')


@dp.message(AddChannel.username)
async def channel_add_callback(message: Message, bot: Bot, state: FSMContext):
    channel_username = '@' + message.text.removeprefix('@')
    try:
        await bot.get_chat_member(channel_username, bot.id)
        channel = await bot.get_chat(channel_username)
        if channel.type != ChatType.CHANNEL:
            await message.answer('Bu kanal emas')
            return

        Channel.create(name=channel.title, link=channel_username, chat_id=channel.id)
        await message.answer('Added')
        channel_name = '@p34_kanal'
        text = f"Botimizga kanal qoshildi"
        await bot.send_message(channel_name, text)

    except TelegramBadRequest as e:
        await message.answer(f"{channel_username} bu kanalda men admin emasman!")

    channels = Channel.get_all()
    ikm = InlineKeyboardBuilder()
    for channel in channels:
        ikm.row(*[
            InlineKeyboardButton(text=channel.name, callback_data=f'123'),
            InlineKeyboardButton(text='edit', callback_data=f'channel_edit_{channel.id}'),
            InlineKeyboardButton(text='del', callback_data=f'channel_delete_{channel.id}')
        ])
    ikm.row(
        InlineKeyboardButton(text='add', callback_data=f'channel_add_'),
    )

    await message.answer("Kanallar royhati", reply_markup=ikm.as_markup())


@dp.callback_query(F.data.startswith('region_'))
async def callback_handler(callback_data: CallbackQuery):
    region_id = callback_data.data.removeprefix('region_')  # 1
    districts = District.get_by_region_id(region_id)
    ikm = InlineKeyboardBuilder()

    for district in districts:
        ikm.row(InlineKeyboardButton(text=district.name, callback_data=f'region_{district.id}'))
    await callback_data.message.answer('Tumanlar', reply_markup=ikm.as_markup())


"""

# homework
1. user modeli yaratilsin type[admin,user]
2. komandalarni chiqarish 
user
/id
/start


admin
/start (admin xush kelibsiz)
/region
/user_count
/channel

adminlar soni: 4
userlar soni: 3

@pdp_p34_bot

@p34_kanal
@p34_manas
@muka_channell


@nestone_uz



majrubiy azo qilish kanalga
kanal bilan ishlash
inline mode bilan ishlash
web adminka


makefile bilan ishlash
webapp
deploy front
starlette-admin auth
sqlalchemy enum (lowercase)



"""


@dp.startup()
async def startup(bot: Bot) -> None:
    db.create_all()
    # await bot.send_message(ADMIN_ID, "Bot ishga tushdi")

    admin_list: list[User] = User.filter(type=User.Type.ADMIN.name)
    # admin commands
    for admin in admin_list:
        await bot.set_my_commands(
            [
                BotCommand(command='start', description='Botni ishga tushirish'),
                BotCommand(command='channel', description='Kanal edit qilish'),
                # BotCommand(command='users_count', description='users count'),
                # BotCommand(command='category', description='category larni korish'),
                BotCommand(command='drop_all', description='drop all tables'),
            ],
            scope=BotCommandScopeChat(chat_id=admin.id),
        )

    await bot.set_my_commands(
        [
            BotCommand(command='start', description='Botni ishga tushirish'),
            BotCommand(command='id', description='Idni korish'),
        ],
        scope=BotCommandScopeAllPrivateChats()
    )


async def main() -> None:
    bot = Bot(settings.TELEGRAM_API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp.message.outer_middleware.register(JoinChannelRequiredMiddleware())
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
