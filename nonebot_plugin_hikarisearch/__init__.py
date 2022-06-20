import asyncio
import traceback
from typing import List, Dict
from nonebot import on_command
from nonebot.matcher import Matcher
from nonebot.plugin import PluginMetadata
from nonebot.typing import T_Handler, T_State
from nonebot.message import event_postprocessor
from nonebot.params import EventMessage, CommandArg, State
from nonebot.adapters.onebot.v11 import Bot, Message, MessageEvent, GroupMessageEvent
from nonebot.log import logger

from .config import hikari_config, Config
from .data_source import sources, Source, download_image

options = " / ".join([source.commands[0] for source in sources])

__plugin_meta__ = PluginMetadata(
    name="搜图",
    description="HikariSearch 动漫图片聚合搜索",
    usage=(f"搜图 / {options} + 图片\n默认为saucenao搜图\n或回复图片消息 搜图\n或 搜图上一张，搜索上一次出现的图"),
    config=Config,
    extra={
        "unique_name": "hikarisearch",
        "example": "搜图 [图片]",
        "author": "meetwq <meetwq@gmail.com>",
        "version": "0.1.5",
    },
)


last_img: Dict[str, str] = {}


def get_cid(event: MessageEvent):
    return (
        f"group_{event.group_id}"
        if isinstance(event, GroupMessageEvent)
        else f"private_{event.user_id}"
    )


@event_postprocessor
async def save_last_img(event: MessageEvent, msg: Message = EventMessage()):
    cid = get_cid(event)
    if imgs := msg["image"]:
        last_img.update({cid: imgs[-1].data["url"]})


def get_img_url(
    event: MessageEvent,
    state: T_State = State(),
    msg: Message = EventMessage(),
    arg: Message = CommandArg(),
) -> bool:
    img_url = ""
    if event.reply:
        if imgs := event.reply.message["image"]:
            img_url = imgs[0].data["url"]
    elif imgs := msg["image"]:
        img_url = imgs[0].data["url"]
    if not img_url:
        if arg.extract_plain_text().strip().startswith("上一张"):
            cid = get_cid(event)
            img_url = last_img.get(cid, "")
    if img_url:
        state["img_url"] = img_url
        return True
    return False


def create_matchers():
    def create_handler(source: Source) -> T_Handler:
        async def handler(
            bot: Bot, matcher: Matcher, event: MessageEvent, state: T_State = State()
        ):
            img_url: str = state["img_url"]

            try:
                img = await download_image(img_url)
            except:
                logger.warning(traceback.format_exc())
                await matcher.finish("图片下载出错，请稍后再试")

            try:
                res = await source.func(img)
            except:
                logger.warning(traceback.format_exc())
                await matcher.finish("出错了，请稍后再试")

            help_msg = f"当前搜索引擎：{source.name}\n可使用 {options} 命令使用其他引擎搜索"
            if res:
                await send_msg(bot, matcher, event, res, help_msg)
            else:
                await matcher.finish(f"{source.name} 中未找到匹配的图片")

        return handler

    for source in sources:
        on_command(
            source.commands[0],
            get_img_url,
            aliases=set(source.commands),
            block=True,
            priority=13,
        ).append_handler(create_handler(source))


create_matchers()


async def handler(
    bot: Bot, matcher: Matcher, event: MessageEvent, state: T_State = State()
):
    img_url: str = state["img_url"]

    try:
        img = await download_image(img_url)
    except:
        logger.warning(traceback.format_exc())
        await matcher.finish("图片下载出错，请稍后再试")

    res: List[Message] = []
    help_msg = ""
    for source in sources:
        try:
            res = await source.func(img)
            if res:
                help_msg = f"当前搜索引擎：{source.name}\n可使用 {options} 命令使用其他引擎搜索"
                break
            else:
                logger.info(f"{source.name} 中未找到匹配的图片")
        except:
            logger.warning(f"{source.name} 搜索出错")

    if not res:
        await matcher.finish("出错了，请稍后再试")

    await send_msg(bot, matcher, event, res, help_msg)


on_command(
    "搜图", get_img_url, aliases={"以图搜图", "识图"}, block=True, priority=13
).append_handler(handler)


async def help_handler(matcher: Matcher):
    await matcher.finish(__plugin_meta__.usage)


on_command("搜图帮助", aliases={"帮助搜图"}, block=True, priority=13).append_handler(
    help_handler
)


async def send_msg(
    bot: Bot, matcher: Matcher, event: MessageEvent, msgs: List[Message], help_msg: str
):
    msgs = msgs[: hikari_config.hikarisearch_max_results]
    if isinstance(event, GroupMessageEvent) and len(msgs) > 1:
        msgs.insert(0, Message(help_msg))
        await send_forward_msg(bot, event, "HikariSearch", bot.self_id, msgs)
    else:
        for msg in msgs:
            await matcher.send(msg)
            await asyncio.sleep(2)


async def send_forward_msg(
    bot: Bot,
    event: GroupMessageEvent,
    name: str,
    uin: str,
    msgs: List[Message],
):
    def to_json(msg: Message):
        return {"type": "node", "data": {"name": name, "uin": uin, "content": msg}}

    messages = [to_json(msg) for msg in msgs]
    await bot.call_api(
        "send_group_forward_msg", group_id=event.group_id, messages=messages
    )
