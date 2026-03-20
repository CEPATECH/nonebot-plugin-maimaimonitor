from asyncio import Lock
from collections import defaultdict
from nonebot import on_command, on_message, require, get_plugin_config
from nonebot.rule import Rule
from nonebot.matcher import Matcher
from nonebot.adapters.onebot.v11 import Bot, Event, Message, GroupMessageEvent
from nonebot.params import CommandArg
import time
from typing import Any
from .config import Config
from .constants import (
    get_help_menu, REPORT_MAPPING, ReportCode, 
    detect_anomaly, detect_normal, detect_feng
)

config = get_plugin_config(Config)

from .client import MaimaiReporter

reporter = MaimaiReporter(
    client_id=config.maimai_bot_client_id,
    private_key=config.maimai_bot_private_key,
    worker_url=config.maimai_worker_url
)

report_cache: defaultdict[int, list[int]] = defaultdict(list)
cache_lock = Lock()

report_matcher = on_command("report", aliases={"上报"}, priority=5, block=False)
net_matcher = on_command("net", priority=5, block=False)

DIRECT_ALIASES = {"网咋样", "华立服务器死了吗", "炸了吗"}

async def _direct_alias_rule(event: Event) -> bool:
    return event.get_plaintext().strip() in DIRECT_ALIASES

net_direct_matcher = on_message(rule=Rule(_direct_alias_rule), priority=5, block=False)

@net_matcher.handle()
@net_direct_matcher.handle()
async def handle_net(matcher: Matcher):
    data = await reporter.fetch_status()
    if not data:
        await matcher.finish(
            "获取服务器状态失败，请稍后重试\n🔗 https://mai.chongxi.us"
        )
        return
    
    status = data.get("status", "empty")
    status_map = {"normal": "✅ 好", "anomaly": "⚠️ 不稳定", "empty": "❌ 坏"}
    status_label = status_map.get(status, "❓ 未知")
    
    latency = data.get("latency", {})
    logs = data.get("recent_logs", [])
    broadcast = data.get("broadcast")
    
    msg = f"【舞萌DX游戏服务器状态】\n"
    msg += f"游戏服务器 {status_label}\n"
    msg += f"⏱ 当前延迟：{latency.get('current_ms', '--')}ms｜"
    msg += f"负载：{latency.get('load_text', '--')}｜"
    msg += f"延迟{latency.get('volatility_text', '--')}\n\n"
    msg += f"💬 {data.get('summary', '')}\n"
    
    if logs:
        for log in logs[:3]:
            msg += f"• {log.get('time_ago', '--')} {log.get('region', '--')} {log.get('type', '--')}\n"
    
    if broadcast and broadcast.get("msg"):
        msg += f"\n📢 {broadcast['msg']}\n"
    
    msg += f"\n🔗 详情请查看 https://mai.chongxi.us/"
    
    await matcher.finish(msg)

async def _keyword_rule(event: Event) -> bool:
    if not isinstance(event, GroupMessageEvent):
        return False
    text = event.get_plaintext().strip()
    if not text:
        return False
    return bool(detect_anomaly(text) or detect_normal(text) or detect_feng(text))

keyword_matcher = on_message(rule=Rule(_keyword_rule), priority=10, block=False)

@keyword_matcher.handle()
async def handle_keyword(event: GroupMessageEvent):
    text = event.get_plaintext().strip()
    
    feng = detect_feng(text)
    if feng != 0:
        async with cache_lock:
            report_cache[ReportCode.GROUP_KEYWORD].append(feng)
        return
    
    if detect_normal(text):
        async with cache_lock:
            report_cache[ReportCode.ERR_NET_LOST].append(-1)
        return
    
    if detect_anomaly(text):
        async with cache_lock:
            report_cache[ReportCode.GROUP_KEYWORD].append(1)

@report_matcher.handle()
async def handle_report(bot: Bot, event: Event, args: Message = CommandArg()):
    arg_text = args.extract_plain_text().strip()
    arg_parts = arg_text.split()

    if not arg_text or len(arg_parts) == 0:
        await report_matcher.finish(f"指令格式错误。\n{get_help_menu()}")
        return

    if arg_parts[0].lower() in ['help', '帮助']:
        await report_matcher.finish(get_help_menu())
        return

    report_key = arg_parts[0].lower()
    if report_key not in REPORT_MAPPING:
        await report_matcher.finish(f"未知的报告类型: '{report_key}'\n请使用 /report help 查看可用类型。")
        return

    report_code, report_name = REPORT_MAPPING[report_key]
    report_value = 1

    if report_code == ReportCode.WAIT_TIME:
        if len(arg_parts) > 1:
            try:
                report_value = int(arg_parts[1])
            except ValueError:
                await report_matcher.finish("罚站时长参数必须是数字（秒数）")
                return
        else:
            await report_matcher.finish("请输入罚站时长（秒）。\n用法: /report 罚站 [秒数]")
            return

    result_message = await process_maimai_report(
        report_code=report_code,
        report_name=report_name,
        report_value=report_value,
        bot=bot,
        event=event
    )
    await report_matcher.finish(result_message)


async def process_maimai_report(
    report_code: ReportCode,
    report_name: str,
    report_value: Any,
    bot: Bot,
    event: Event
) -> str:
    async with cache_lock:
        report_cache[report_code].append(report_value)
    return f"{report_name}上报成功"


COUNT_BASED_TYPES = {
    ReportCode.ERR_NET_LOST, ReportCode.ERR_LOGIN, ReportCode.ERR_MAI_NET,
    ReportCode.ACC_INVOICE, ReportCode.ACC_BAN, ReportCode.ACC_SCAN
}

async def send_aggregated_reports():
    final_payload = []
    
    async with cache_lock:
        if not report_cache:
            return
        
        cached_items = list(report_cache.items())
        report_cache.clear()

    for report_type, values in cached_items:
        if report_type == ReportCode.ERR_NET_LOST:
            anomaly_values = [v for v in values if v != -1]
            normal_count = sum(1 for v in values if v == -1)
            
            if anomaly_values:
                final_payload.append({"t": ReportCode.ERR_NET_LOST, "v": sum(anomaly_values), "r": "BOT"})
            
            if normal_count > 0:
                final_payload.append({"t": 501, "v": normal_count, "r": "BOT"})
        elif report_type == ReportCode.GROUP_KEYWORD:
            anomaly_count = sum(1 for v in values if v > 0)
            return_count = sum(1 for v in values if v < 0)
            
            if anomaly_count > 0:
                final_payload.append({"t": int(report_type), "v": anomaly_count, "r": "BOT"})
            
            if return_count > 0:
                # 返航信号上报正常类型 t:501
                final_payload.append({"t": 501, "v": return_count, "r": "BOT"})
        elif report_type in COUNT_BASED_TYPES:
            total_value = sum(values)
            if total_value > 0:
                final_payload.append({"t": report_type, "v": total_value, "r": "BOT"})
        else:
            for value in values:
                final_payload.append({"t": report_type, "v": value, "r": "BOT"})
    
    if not final_payload:
        return

    try:
        await reporter.send_report(final_payload, config.maimai_bot_display_name)
    except Exception:
        pass

require("nonebot_plugin_apscheduler")
from nonebot_plugin_apscheduler import scheduler

scheduler.add_job(send_aggregated_reports, "interval", seconds=30, id="maimai_report_scheduler_v11")
