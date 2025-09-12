from aiogram.filters import Filter
from aiogram.types import Message

from models import User


class IsAdminFilter(Filter):

    def __init__(self):
        super().__init__()

    async def __call__(self, message: Message):
        user = User.get(message.from_user.id)
        return user and user.is_admin
