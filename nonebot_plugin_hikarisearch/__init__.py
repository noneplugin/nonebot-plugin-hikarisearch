import asyncio
import traceback
from typing import List
from nonebot import on_startswith
from nonebot.matcher import Matcher
from nonebot.params import EventMessage
from nonebot.typing import T_Handler, T_State
from nonebot.adapters.onebot.v11 import Bot, Message, MessageEvent, GroupMessageEvent
from nonebot.log import logger

from .data_source import sources, Source, download_image
from .config import hikari_config


__help__plugin_name__ = "imgsearch"
__des__ = "搜图"
options = " / ".join([source.commands[0] for source in sources])
__cmd__ = f"""
搜图 / {options} + 图片
默认为saucenao搜图
或回复图片消息 搜图
""".strip()
__short_cmd__ = "搜图 [图片]"
__usage__ = f"{__des__}\nUsage:\n{__cmd__}"


def get_img_url(
    event: MessageEvent, state: T_State, msg: Message = EventMessage()
) -> bool:
    img_url = ""
    if event.reply:
        if imgs := event.reply.message["image"]:
            img_url = imgs[0].data["url"]
    elif imgs := msg["image"]:
        img_url = imgs[0].data["url"]
    if img_url:
        state["img_url"] = img_url
        return True
    return False


def create_matchers():
    def create_handler(source: Source) -> T_Handler:
        async def handler(
            bot: Bot, matcher: Matcher, event: MessageEvent, state: T_State
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
                await send_msg(
                    bot,
                    matcher,
                    event,
                    res[: hikari_config.hikarisearch_max_results],
                    help_msg,
                )
            else:
                await matcher.finish(f"{source.name} 中未找到匹配的图片")

        return handler

    for source in sources:
        on_startswith(
            source.commands, get_img_url, ignorecase=True, block=True, priority=13
        ).append_handler(create_handler(source))


create_matchers()


async def send_msg(
    bot: Bot, matcher: Matcher, event: MessageEvent, msgs: List[Message], help_msg: str
):
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
