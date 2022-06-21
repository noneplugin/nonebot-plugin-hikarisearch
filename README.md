# nonebot-plugin-hikarisearch

适用于 [Nonebot2](https://github.com/nonebot/nonebot2) 的搜图插件

使用 [HikariSearch](https://github.com/mixmoe/HikariSearch) 搜索

支持 SauceNAO、IqDB、ascii2d、E-Hentai、TraceMoe


### 安装

- 使用 nb-cli

```
nb plugin install nonebot_plugin_hikarisearch
```

- 使用 pip

```
pip install nonebot_plugin_hikarisearch
```


### 使用

**以下命令需要加[命令前缀](https://v2.nonebot.dev/docs/api/config#Config-command_start) (默认为`/`)，可自行设置为空**

```
搜图/saucenao搜图/iqdb搜图/ascii2d搜图/ehentai搜图/tracemoe搜图 + 图片
```
默认为 saucenao搜图

或回复包含图片的消息，回复“搜图”


### 配置

可在 `.env.xxx` 文件中添加如下配置：

```
hikarisearch_api=xxx  # HikariSearch 站点，默认为 "https://hikari.obfs.dev"
hikarisearch_max_results=xxx  # 最多返回的结果数量，默认为 3
hikarisearch_withdraw=xxx  # 自动撤回时间，默认为 0 (不撤回)，单位为秒
```
