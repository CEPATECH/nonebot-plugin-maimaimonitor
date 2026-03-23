from asyncio import Lock
from collections import defaultdict
from nonebot import on_command, on_message, require, get_plugin_config
from nonebot.log import logger
from nonebot.rule import Rule
from nonebot.matcher import Matcher
from nonebot.adapters.onebot.v11 import Bot, Event, Message, GroupMessageEvent
from nonebot.params import CommandArg
import time
from typing import Any
from .config import Config
from .constants import (
    get_help_menu, REPORT_MAPPING, ReportCode, 
    detect_anomaly, detect_normal, detect_feng, detect_ban, detect_guest
)

config = get_plugin_config(Config)

keyword_cooldown: dict[int, float] = {}
KEYWORD_COOLDOWN_SECONDS = 60

last_status: str = "normal"
anomaly_start_time: float | None = None

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
    reports = data.get("reports", {})
    logs = data.get("recent_logs", [])
    broadcast = data.get("broadcast")
    
    msg = f"【舞萌DX游戏服务器状态】\n"
    msg += f"游戏服务器 {status_label}\n"
    msg += f"⏱ 当前延迟：{latency.get('current_ms', '--')}ms｜"
    msg += f"服务器负载：{latency.get('load_text', '--')}｜"
    msg += f"延迟{latency.get('volatility_text', '--')}\n\n"

    anomaly = reports.get('anomaly_count', 0)
    normal = reports.get('normal_count', 0)
    if anomaly == 0 and normal == 0:
        msg += f"💬 过去1小时内无任何上报\n"
    elif normal == 0:
        msg += f"💬 过去1小时有{anomaly}条异常上报，无正常上报\n"
    elif anomaly == 0:
        msg += f"💬 过去1小时有{normal}条正常上报，无异常\n"
    else:
        msg += f"💬 过去1小时有{anomaly}条异常，{normal}条正常上报\n"
    
    if logs:
        for log in logs[:3]:
            msg += f"• {log.get('time_ago', '--')} {log.get('region', '--')} {log.get('type', '--')}\n"
    
    if broadcast and broadcast.get("msg"):
        msg += f"\n📢 {broadcast['msg']}\n"
    
    msg += f"\n🔗 详情请查看 https://mai.chongxi.us/"
    
    await matcher.finish(msg)

def format_duration(seconds: int) -> str:
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    if hours > 0:
        return f"{hours}hr {minutes}min"
    return f"{minutes}min"

async def broadcast_to_groups(msg: str):
    try:
        from nonebot import get_bot
        bot = get_bot()
        if config.maimai_broadcast_all_groups:
            group_list = await bot.get_group_list()
            for group in group_list:
                try:
                    await bot.send_group_msg(group_id=group['group_id'], message=msg)
                    logger.info(f"播报成功 group_id={group['group_id']}")
                except Exception as e:
                    logger.warning(f"播报失败 group_id={group['group_id']}: {e}")
        elif config.maimai_broadcast_group_ids:
            for group_id in config.maimai_broadcast_group_ids:
                try:
                    await bot.send_group_msg(group_id=group_id, message=msg)
                    logger.info(f"播报成功 group_id={group_id}")
                except Exception as e:
                    logger.warning(f"播报失败 group_id={group_id}: {e}")
        else:
            return
    except Exception as e:
        logger.warning(f"获取bot实例失败: {e}")

async def check_server_status():
    global last_status, anomaly_start_time
    if not config.maimai_broadcast_group_ids and not config.maimai_broadcast_all_groups:
        return
    try:
        data = await reporter.fetch_status()
        if not data:
            return
        status = data.get("status", "normal")
        now = time.time()

        if last_status == "normal" and status in ("anomaly", "empty"):
            anomaly_start_time = now
            last_status = status
            summary = data.get("summary", "")
            logs = data.get("recent_logs", [])
            msg = "【舞萌DX服务器断网播报】\n"
            msg += "游戏服务器 ❌ 坏\n\n"
            msg += f"💬 {summary}\n"
            for log in logs[:3]:
                msg += f"• {log.get('time_ago', '--')} {log.get('region', '--')} {log.get('type', '--')}\n"
            msg += "\n🔗 详情请查看 https://mai.chongxi.us/"
            logger.info(f"检测到服务器异常，开始播报")
            await broadcast_to_groups(msg)

        elif last_status in ("anomaly", "empty") and status == "normal":
            duration = int(now - anomaly_start_time) if anomaly_start_time else 0
            last_status = "normal"
            anomaly_start_time = None
            msg = "【舞萌DX服务器状态恢复】\n"
            msg += "游戏服务器 ✅ 好\n"
            msg += f"本次约持续 {format_duration(duration)}\n\n"
            msg += "🔗 详情请查看 https://mai.chongxi.us/"
            logger.info(f"服务器恢复正常，播报恢复通知")
            await broadcast_to_groups(msg)

        else:
            last_status = status

    except Exception as e:
        logger.warning(f"状态检测失败: {e}")

async def _keyword_rule(event: Event) -> bool:
    if not isinstance(event, GroupMessageEvent):
        return False
    text = event.get_plaintext().strip()
    if not text:
        return False
    return bool(detect_anomaly(text) or detect_normal(text) or detect_feng(text) or detect_ban(text) or detect_guest(text))

keyword_matcher = on_message(rule=Rule(_keyword_rule), priority=10, block=False)

@keyword_matcher.handle()
async def handle_keyword(event: GroupMessageEvent):
    user_id = event.user_id
    now = time.time()
    if user_id in keyword_cooldown:
        if now - keyword_cooldown[user_id] < KEYWORD_COOLDOWN_SECONDS:
            return
    keyword_cooldown[user_id] = now
    
    text = event.get_plaintext().strip()
    
    feng = detect_feng(text)
    if feng != 0:
        logger.info(f"关键词触发冯氏指数 direction={feng} | 文本：{text} | 用户：{event.user_id} | 群：{event.group_id}")
        async with cache_lock:
            report_cache[ReportCode.GROUP_KEYWORD].append(feng)
        return
    
    if detect_ban(text):
        async with cache_lock:
            report_cache[ReportCode.GROUP_KEYWORD_BAN].append(1)
        logger.info(f"关键词触发小黑屋上报 | 文本：{text} | 用户：{event.user_id} | 群：{event.group_id}")
        return

    if detect_guest(text):
        async with cache_lock:
            report_cache[ReportCode.GROUP_KEYWORD_GUEST].append(1)
        logger.info(f"关键词触发游客上报 | 文本：{text} | 用户：{event.user_id} | 群：{event.group_id}")
        return

    if detect_normal(text):
        logger.info(f"关键词触发正常上报 | 文本：{text} | 用户：{event.user_id} | 群：{event.group_id}")
        async with cache_lock:
            report_cache[ReportCode.ERR_NET_LOST].append(-1)
        return
    
    if detect_anomaly(text):
        logger.info(f"关键词触发异常上报 | 文本：{text} | 用户：{event.user_id} | 群：{event.group_id}")
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
            anomaly_count = min(sum(1 for v in values if v > 0), 5)
            return_count = min(sum(1 for v in values if v < 0), 5)
            
            if anomaly_count > 0:
                final_payload.append({"t": 101, "v": anomaly_count, "r": "BOT"})
            
            if return_count > 0:
                final_payload.append({"t": 501, "v": return_count, "r": "BOT"})
        elif report_type == ReportCode.GROUP_KEYWORD_BAN:
            ban_count = min(sum(1 for v in values if v > 0), 5)
            if ban_count > 0:
                final_payload.append({"t": 202, "v": ban_count, "r": "BOT"})
        elif report_type == ReportCode.GROUP_KEYWORD_GUEST:
            guest_count = min(sum(1 for v in values if v > 0), 5)
            if guest_count > 0:
                final_payload.append({"t": 102, "v": guest_count, "r": "BOT"})
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
scheduler.add_job(check_server_status, "interval", seconds=config.maimai_broadcast_interval, id="maimai_broadcast_checker")
