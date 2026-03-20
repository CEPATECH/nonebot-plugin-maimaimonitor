from nonebot.plugin import PluginMetadata
from .maimai_plugin_v11 import *
from .maimai_plugin_v11 import process_maimai_report

__plugin_meta__ = PluginMetadata(
    name="舞萌服务器监控",
    description="一个检测舞萌服务器似了没的bot插件，支持上报各种信息",
    usage="发送`/report help`即可查看菜单",
    type="application",
    homepage="https://github.com/CEPATECH/nonebot-plugin-maimaimonitor",
    supported_adapters={"~onebot.v11"},
    extra={
        "author": "Chongxi3555",
    },
)
