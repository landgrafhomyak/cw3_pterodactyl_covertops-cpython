import asyncio
from datetime import datetime, tzinfo
import re
import sys
from io import StringIO

from aiogram import Bot, Dispatcher
from aiogram.dispatcher.filters import Filter
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.utils.exceptions import MessageNotModified
from sqlalchemy import Table, Column, MetaData, BigInteger, DateTime, Text, select, and_, update
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql.ddl import CreateTable

table = Table(
    "kamikadzes",
    MetaData(),
    Column("user", BigInteger, primary_key=True, unique=True),
    Column("date", DateTime),
    Column("attack", BigInteger),
    Column("name", Text)
)

profile_pattern = re.compile(r"(?:^|\n)([^\w\[]\ufe0f?(?:\[\w{2,3}]|)[\w\s]{4,16})\n.+\n.+Атака:\s(\d+)")


class KamikadzeDatabase:
    __slots__ = "__sf"

    @classmethod
    async def connect(cls, session_factory):
        self = super().__new__(cls)
        self.__sf = session_factory
        async with self.__sf.begin() as c:
            await c.execute(CreateTable(table, if_not_exists=True))
        return self

    async def set_user(self, uid: int, date: int, name: str, attack: int):
        if not isinstance(uid, int):
            raise TypeError(f"uid must be int (got {type(uid) !r})")
        if not isinstance(date, datetime):
            raise TypeError(f"uid must be {datetime.__qualname__} (got {type(date) !r})")
        if not isinstance(name, str):
            raise TypeError(f"uid must be str (got {type(name) !r})")
        if not isinstance(attack, int):
            raise TypeError(f"uid must be int (got {type(attack) !r})")

        async with self.__sf.begin() as c:
            for rec in await c.execute(select(table).where(table.c.user == uid)):
                if rec.date.timestamp() >= date.timestamp():
                    return False
                await c.execute(update(table).where(table.c.user == uid).values(date=date, name=name, attack=attack))
                return True
            await c.execute(table.insert().values(user=uid, date=date, name=name, attack=attack))
        return True

    async def get_user(self, uid: int):
        if not isinstance(uid, int):
            raise TypeError(f"uid must be int (got {type(uid) !r})")

        async with self.__sf.begin() as c:
            for rec in await c.execute(select(table).where(table.c.user == uid)):
                return rec.name, rec.attack
        return None

    async def get_all_users(self):
        users = []
        async with self.__sf.begin() as c:
            for rec in await c.execute(select(table)):
                users.append((rec.user, rec.name, rec.attack))
        return users


class HeroFilter(Filter):
    @staticmethod
    async def check(msg: Message):
        return msg.is_forward() and msg.forward_from.id == 265204902 and profile_pattern.search(msg.text) is not None


class PrefixCheckFilter(Filter):
    __slots__ = ("__prefix",)

    def __init__(self, prefix):
        self.__prefix = prefix

    async def check(self, cbq):
        return cbq.data.startswith(self.__prefix)


squad_msg_pattern = re.compile(r"^[^(]+\(\D*(\d+)\D+\).+(?:\n([\s\S]*)|)$")
squad_msg_row_pattern = re.compile(r"^\D*(\d+)\D.+tg://user\?id=(\d+)\D")


class KamikadzeBot:
    __slots__ = "__bot", "__dp", "__db", "__current_battle"

    def __init__(self, token, *, database):
        self.__bot = Bot(token=token)
        self.__dp = Dispatcher(self.__bot)
        self.__db = database
        self.__dp.register_message_handler(self.__parse_profile, HeroFilter())
        self.__dp.register_message_handler(self.__get_me, commands=["me"])
        self.__dp.register_message_handler(self.__button, commands=["suicide"])
        self.__dp.register_callback_query_handler(self.__add, PrefixCheckFilter("add"))

    def start(self, loop=None):
        if loop is None:
            loop = asyncio.get_event_loop()

        return loop.create_task(self.run())

    async def run(self):
        asyncio.create_task(self.__reset())
        await self.__dp.start_polling()

    async def __parse_profile(self, msg: Message):
        match = profile_pattern.search(msg.text)
        if match is None:
            return

        name, attack = match.group(1), int(match.group(2))
        if await self.__db.set_user(msg.from_user.id, msg.forward_date, name, attack):
            await msg.reply(f"Профиль записан:\n<code>{name} \u2694\ufe0f{attack}</code>", parse_mode="html")
        else:
            await msg.reply("Слишком старый профиль")

    async def __get_me(self, msg: Message):
        data = await self.__db.get_user(msg.from_user.id)
        if data is None:
            await msg.reply("Ты слишком сильно любишь жить, чтобы мне была интересна информация про тебя")
        else:
            await msg.reply(f"<code>{data[0]} \u2694\ufe0f{data[1]}</code>", parse_mode="html")

    async def __reset(self):
        while True:
            await asyncio.sleep(3600 * 8 + 120 - round(datetime.now().timestamp() - 6 * 3600) % (3600 * 8))
            self.__current_battle.clear()

    async def __button(self, msg: Message):
        await msg.reply("<b>Отряд суицидников (<u>0\u2694\ufe0f</u>):</b>", parse_mode="html", reply_markup=InlineKeyboardMarkup(row_width=1, inline_keyboard=[[InlineKeyboardButton(text="Сдохнуть", callback_data="add")]]))

    async def __add(self, query: CallbackQuery):

        if (m := squad_msg_pattern.search(query.message.html_text)) is None:
            await query.answer("С этим сообщением что то не так")
            return

        atk = int(m.group(1))
        u = None
        new_rows = StringIO()

        async def proc_user(neg):
            nonlocal atk, u, new_rows, self
            u = await self.__db.get_user(query.from_user.id)
            if u is None:
                await query.message.reply(f"<a href='tg://user?id={query.from_user.id}'>{query.from_user.full_name}</a> скинь свой <a href='https://t.me/share/url?url=/hero'>/hero</a> для начала", parse_mode="html")
                await query.answer("Профиль где?")
                return True
            new_rows.write(f"<code>{str(u[1]).rjust(5, ' ')}\u2694\ufe0f</code> <a href='tg://user?id={query.from_user.id}'>{u[0]}</a>\n")
            atk = atk - neg + u[1]

        for row in filter(bool, (m.group(2) or "").split("\n")):
            mm = squad_msg_row_pattern.search(row)
            if mm is None:
                new_rows.write(row + "\n")
                continue
            if int(mm.group(2)) == query.from_user.id:
                if await proc_user(int(mm.group(1))):
                    return
            else:
                new_rows.write(row + "\n")

        if u is None:
            if await proc_user(0):
                return

        new_rows.seek(0)
        try:
            await query.answer("Записан в суицидники")
            await query.message.edit_text(f"<b>Отряд суицидников (<u>{atk}\u2694\ufe0f</u>):</b>\n" + new_rows.read(), parse_mode="html", reply_markup=query.message.reply_markup)
        except MessageNotModified:
            pass

async def amain(argv):
    engine = create_async_engine(f"postgresql+asyncpg://{argv[2]}:{argv[3]}@{argv[4]}:{argv[5]}/{argv[6]}", )
    db = await KamikadzeDatabase.connect(sessionmaker(engine, class_=AsyncSession))
    await KamikadzeBot(argv[1], database=db).run()


def main(argv):
    asyncio.get_event_loop().run_until_complete(amain(argv))


if __name__ == "__main__":
    exit(main(sys.argv))
