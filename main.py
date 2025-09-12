import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardButton, CallbackQuery, BotCommand, \
    BotCommandScopeChat, BotCommandScopeAllPrivateChats
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import settings
from filters import IsAdminFilter
from models import db, Region, District, User

dp = Dispatcher()


@dp.message(CommandStart(), IsAdminFilter())
async def cmd_start(message: Message):
    await message.answer("Xush kelibsiz")


@dp.message(CommandStart())
async def start_handler(message: Message):
    data = message.from_user.model_dump(include={'id', 'first_name', 'last_name', 'username'})
    user, created = User.get_or_create(**data)

    ikm = InlineKeyboardBuilder()
    regions = Region.get_all()

    for region in regions:
        ikm.row(InlineKeyboardButton(text=region.name, callback_data=f'region_{region.id}'))
    await message.answer('Viloyatlarni tanlang', reply_markup=ikm.as_markup())


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
adminlar soni: 4
userlar soni: 3

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
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
