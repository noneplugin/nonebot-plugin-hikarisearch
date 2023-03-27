from nonebot import get_driver
from pydantic import BaseModel, Extra


class Config(BaseModel, extra=Extra.ignore):
    hikarisearch_api: str = "https://hikari.obfs.dev"
    hikarisearch_max_results: int = 3
    hikarisearch_withdraw: int = 0
    _hikarisearch_proxy: str = ''
    hikarisearch_thumb: bool = True
    
    # hikarisearch_proxy只能为None或非空字符串
    @property
    def hikarisearch_proxy(self):
        if self._hikarisearch_proxy == '':
            return None
        return self._hikarisearch_proxy
    
    @hikarisearch_proxy.setter
    def hikarisearch_proxy(self, value):
        if value is None:
            value = ''
        self._hikarisearch_proxy = value


hikari_config = Config.parse_obj(get_driver().config.dict())
