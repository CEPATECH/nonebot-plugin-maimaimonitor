from enum import IntEnum
import re

class ReportCode(IntEnum):
    ERR_NET_LOST = 101
    ERR_LOGIN = 102
    ERR_MAI_NET = 103
    ACC_INVOICE = 201
    ACC_BAN = 202
    ACC_SCAN = 203
    WAIT_TIME = 300
    GROUP_KEYWORD = 801
    GROUP_KEYWORD_BAN = 802
    GROUP_KEYWORD_GUEST = 803

REPORT_MAPPING = {
    "1": (ReportCode.ERR_NET_LOST, "断网"),
    "断网": (ReportCode.ERR_NET_LOST, "断网"),
    
    "2": (ReportCode.ERR_LOGIN, "无法登录"),
    "无法登录": (ReportCode.ERR_LOGIN, "无法登录"),

    "3": (ReportCode.ERR_MAI_NET, "NET打不开"),
    "net打不开": (ReportCode.ERR_MAI_NET, "NET打不开"),

    "4": (ReportCode.ACC_INVOICE, "被发票"),
    "被发票": (ReportCode.ACC_INVOICE, "被发票"),

    "5": (ReportCode.ACC_BAN, "小黑屋"),
    "小黑屋": (ReportCode.ACC_BAN, "小黑屋"),

    "6": (ReportCode.ACC_SCAN, "其他扫号行为"),
    "其他扫号行为": (ReportCode.ACC_SCAN, "其他扫号行为"),

    "7": (ReportCode.WAIT_TIME, "罚站时长"),
    "罚站时长": (ReportCode.WAIT_TIME, "罚站时长"),
    "罚站": (ReportCode.WAIT_TIME, "罚站时长"),
}

OPERATOR_PATTERN = r'(?:华立|[Ss][Ee][Gg][Aa]|[Ss][Bb][Gg][Aa]|冯|老冯|服务器|机台|[Nn][Ee][Tt]|会员|标题|游戏)'

ANOMALY_VERB_PATTERN = r'(?:炸|挂|死|坏|灰|飞|崩|寄|凉|废|完|烂|蹦|卡死|不行)'

NORMAL_VERB_PATTERN = r'(?:好了|稳了|正常了|恢复了|回来了|活了|绿了|通了|好使了|没事了)'

NEGATIVE_WORDS = ['不', '没', '没有', '别', '未', '并未', '并没', '不会', '不是']

UNCERTAIN_WORDS = ['好像', '可能', '应该', '感觉', '貌似']

STANDALONE_BAN = ['小黑屋', '黑屋了', '黑屋', '进黑屋', '被关小黑屋', '关小黑屋']

STANDALONE_GUEST = ['游客了', '变游客', '游客模式', '掉游客', '游客登录']

STANDALONE_ANOMALY = ['灰网', '炸网', '被发票', '发票了', '扫号']

STANDALONE_NORMAL = ['绿网了', '服务器好了', '恢复正常']

FENG_FLY_PATTERN = r'(?=.*(?:华立|[Ss][Ee][Gg][Aa]|[Ss][Bb][Gg][Aa]))(?=.*冯)(?=.*(?:飞|起飞))'
FENG_RETURN_PATTERN = r'(?=.*(?:华立|[Ss][Ee][Gg][Aa]|[Ss][Bb][Gg][Aa]))(?=.*冯)(?=.*(?:返航|落地|稳了))'

def detect_ban(text: str) -> bool:
    def has_negation(pos: int) -> bool:
        prefix = text[max(0, pos-5):pos]
        return any(w in prefix for w in NEGATIVE_WORDS)
    
    for word in STANDALONE_BAN:
        idx = text.find(word)
        if idx != -1 and not has_negation(idx):
            return True
    
    if re.search(r'\d+\s*(min|分钟)了', text, re.IGNORECASE):
        return True
    
    return False

def detect_guest(text: str) -> bool:
    def has_negation(pos: int) -> bool:
        prefix = text[max(0, pos-5):pos]
        return any(w in prefix for w in NEGATIVE_WORDS)
    
    for word in STANDALONE_GUEST:
        idx = text.find(word)
        if idx != -1 and not has_negation(idx):
            return True
    
    return False

def detect_anomaly(text: str) -> bool:
    def has_negation(pos: int) -> bool:
        prefix = text[max(0, pos-5):pos]
        return any(w in prefix for w in NEGATIVE_WORDS)
    
    for word in STANDALONE_ANOMALY:
        idx = text.find(word)
        if idx != -1 and not has_negation(idx):
            return True
    
    pattern = re.compile(
        rf'{OPERATOR_PATTERN}.{{0,10}}{ANOMALY_VERB_PATTERN}',
        re.IGNORECASE
    )
    for m in pattern.finditer(text):
        if not has_negation(m.start()):
            return True
    
    return False

def detect_normal(text: str) -> bool:
    if any(w in text for w in UNCERTAIN_WORDS):
        return False
    
    for word in STANDALONE_NORMAL:
        if word in text:
            return True
    
    pattern = re.compile(
        rf'{OPERATOR_PATTERN}.{{0,10}}{NORMAL_VERB_PATTERN}',
        re.IGNORECASE
    )
    return bool(pattern.search(text))

def detect_feng(text: str) -> int:
    def has_negation_global(t: str) -> bool:
        return any(w in t for w in NEGATIVE_WORDS)
    
    if has_negation_global(text):
        return 0
    if re.search(FENG_RETURN_PATTERN, text, re.IGNORECASE):
        return -1
    if re.search(FENG_FLY_PATTERN, text, re.IGNORECASE):
        return 1
    return 0

def get_help_menu():
    menu = """查看使用方法:
/report help 或 /上报 帮助

帮助菜单
用法: /report [类型] [参数(可选)]
1. 断网
2. 无法登录
3. NET打不开
4. 被发票
5. 小黑屋
6. 其他扫号行为
7. 罚站时长 + [秒数]

示例:
/report 1
/report 7 120
/report 断网
/report 罚站 120

其他查询:
/net : 查看服务器状态
直接发送「网咋样」或「炸了吗」也可触发"""
    return menu
