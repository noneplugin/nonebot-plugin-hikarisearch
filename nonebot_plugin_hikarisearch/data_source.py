from typing import List, Tuple, Protocol
from dataclasses import dataclass
import httpx
from nonebot.adapters.onebot.v11 import Message, MessageSegment
from nonebot.log import logger

from .config import hikari_config

API = hikari_config.hikarisearch_api.strip("/")


async def search_saucenao(image: bytes) -> List[Message]:
    data = {"hide": "true"}
    result = await post("/api/SauceNAO", data, image)

    msg = []
    for res in result:
        _msg = ''
        if hikari_config.hikarisearch_thumb:
            _msg += await thumb_msg(res["image"])

        _msg += "{}\n图片相似度: {:.2f}%\n图片来源:\n{}".format(
                res["title"],
                res["similarity"],
                "\n".join(
                    ["\n".join(dict(content).values())
                    for content in res["content"]]
                ),
            )
        msg.append(_msg)

    return msg


async def search_iqdb(image: bytes) -> List[Message]:
    data = {
        "services": '["danbooru","konachan","yandere","gelbooru","sankaku_channel","e_shuushuu","zerochan","anime_pictures"]',
        "discolor": "false",
    }
    result = await post("/api/IqDB", data, image)
    
    msg = []
    for res in result:
        _msg = ''
        if hikari_config.hikarisearch_thumb:
            _msg += await thumb_msg(res["image"])

        _msg += "图片相似度: {:.0f}%\n图片来源:\n{}".format(res["similarity"], res["url"])
        msg.append(_msg)
        
    return msg


async def search_ascii2d(image: bytes) -> List[Message]:
    data = {"type": "color"}
    result = await post("/api/ascii2d", data, image)
    
    msg = []
    for res in result:
        _msg = ''
        if hikari_config.hikarisearch_thumb:
            _msg += await thumb_msg(res["image"])
            
        _msg += "图片来源: {}\n{}\n图片作者: {}\n{}".format(
            res["source"]["text"],
            res["source"]["link"],
            res["author"]["text"],
            res["author"]["link"],
        )
        msg.append(_msg)
    
    return msg


async def search_ehentai(image: bytes) -> List[Message]:
    data = {"site": "eh", "cover": "false", "deleted": "false", "similar": "true"}
    result = await post("/api/E-Hentai", data, image)
    
    msg = []
    for res in result:
        _msg = ''
        if hikari_config.hikarisearch_thumb:
            _msg += await thumb_msg(res["image"])
            
        _msg += "[{}] {}\n图片来源:\n{}".format(res["type"], res["title"], res["link"])
        msg.append(_msg)
    
    return msg


async def search_tracemoe(image: bytes) -> List[Message]:
    data = {"cutBorders": "true"}
    result = await post("/api/TraceMoe", data, image)
    
    msg = []
    for res in result:
        _msg = ''
        if hikari_config.hikarisearch_thumb:
            _msg += await thumb_msg(res["image"])
            
        _msg += "图片相似度:{:.2f}\n{}图片来源:\n{}\n英文名:{}\n罗马字名:{}".format(
            res["similarity"],
            res["file"],
            res["name"]["native"],
            res["name"]["english"],
            res["name"]["romaji"],
        )
        msg.append(_msg)
        
    return msg


async def post(url, data: dict, image: bytes) -> dict:
    files = {"image": image}
    async with httpx.AsyncClient(proxies=hikari_config.hikarisearch_proxy) as client:
        resp = await client.post(API + url, data=data, files=files, timeout=20)
        return resp.json()


async def download_image(url: str, timeout=20) -> bytes:
    async with httpx.AsyncClient(proxies=hikari_config.hikarisearch_proxy) as client:
        resp = await client.get(url, timeout=timeout)
        return resp.content


async def thumb_msg(url: str) -> MessageSegment:
    try:
        img = await download_image(url, timeout=5)
        return MessageSegment.image(img)
    except Exception as e:
        logger.warning('下载搜索结果预览图失败，将使用原始图片链接。原因: {}', e)
        return MessageSegment.image(url)


class Func(Protocol):
    async def __call__(self, image: bytes) -> List[Message]:
        ...


@dataclass
class Source:
    name: str
    keywords: Tuple[str, ...]
    func: Func

    def __post_init__(self):
        self.commands: Tuple[str] = tuple(
            sum(([keyword + "搜图", "搜图" + keyword] for keyword in self.keywords), [])
        )


sources = [
    Source("SauceNAO", ("saucenao", "SauceNAO", "sauce", "nao"), search_saucenao),
    Source("ascii2d", ("ascii2d", "ascii", "asc"), search_ascii2d),
    Source("IqDB", ("iqdb", "IqDB", "IQDB"), search_iqdb),
    Source("E-Hentai", ("ehentai", "E-Hentai", "e-hentai", "eh"), search_ehentai),
    Source("TraceMoe", ("tracemoe", "TraceMoe", "trace"), search_tracemoe),
]
