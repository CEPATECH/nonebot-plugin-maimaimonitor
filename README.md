# NoneBot Plugin: Maimai Monitor

一个为 [NoneBot2](https://nonebot.dev/) 框架设计的插件，用于监听群聊上报舞萌DX服务器状态，并提供实时状态查询。

## 功能

- **实时状态查询**：`/net` 或发送「网咋样」「炸了吗」，直接获取服务器当前状态
- **手动上报**：通过 `/report` 命令上报故障类型
- **自动监听**：在群聊中自动识别玩家自然语言，无需手动触发命令
- **冯氏指数**：自动识别「老冯起飞/返航」
- **断网播报**：服务器状态变化时，自动推送告警和恢复通知到配置的群
- **广播公告**：服务端推送公告时，`/net` 自动显示

## 安装

```bash
nb plugin install nonebot-plugin-maimaimonitor
```

或通过 pip：

```bash
pip install nonebot-plugin-maimaimonitor
```

## 配置

在 `.env` 文件中配置：

| 环境变量 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `MAIMAI_BOT_CLIENT_ID` | `str` | 无 | 由 [isMaiDown](https://mai.chongxi.us) 提供，联系 qwq@chongxi.us 申请 |
| `MAIMAI_BOT_PRIVATE_KEY` | `str` | 无 | 与 ClientID 配套的私钥，申请时一并提供 |
| `MAIMAI_BOT_DISPLAY_NAME` | `str` | `qwq` | Bot显示名称，上报时展示 |
| `MAIMAI_WORKER_URL` | `str` | `https://maiapi.chongxi.us` | 上报API地址 |
| `MAIMAI_BROADCAST_GROUP_IDS` | `list[int]` | `[]` | 广播推送的群组列表 |
| `MAIMAI_BROADCAST_INTERVAL` | `int` | `300` | 广播轮询检测间隔（秒） |
| `MAIMAI_BROADCAST_ALL_GROUPS` | `bool` | `false` | 向bot所在所有群播报，谨慎使用，不建议在非舞萌群中开启 |

**Client ID由您提供，任意ASCII字符，联系qwq@chongxi.us或chongxi3555@proton.me**

## 使用

### 查看服务器状态
发送 `/net`、`网咋样` 或 `炸了吗`

```
【舞萌DX游戏服务器状态】
游戏服务器 ✅ 好
⏱ 当前延迟：396ms｜服务器负载：空闲｜延迟中波动

💬 服务器运行正常
• 1小时前 中国 机台断网
• 4小时前 JP 机台无法登录

🔗 详情请查看 https://mai.chongxi.us/
```

### 手动上报
```
/report 断网
/report 小黑屋
/report 被发票
/report 罚站 300
/report help
```

### 自动监听（群聊）
插件会自动识别群聊中的以下说法并上报，无需手动触发：

**异常触发**（主语+动词组合）
- 主语：华立、SEGA、服务器、机台、NET 等
- 动词：炸、挂、死、坏、崩 等
- 示例：「服务器又炸了」「SEGA挂了」「机台灰网」「游客了」「20min了」

**正常触发**
- 示例：「服务器好了」「华立稳了」「绿网了」

**冯氏指数**
- 起飞（异常）：「华立冯飞了」「SEGA老冯起飞」
- 返航（正常）：「华立冯返航了」「SEGA老冯落地」

### 断网播报
配置 `MAIMAI_BROADCAST_GROUP_IDS` 后，服务器出现异常时自动推送：

```
【舞萌DX服务器断网播报】
游戏服务器 ❌ 坏

💬 过去1小时有5条异常上报，延迟934ms
• 刚刚 BOT 机台断网
• 2分钟前 中国 机台断网

🔗 详情请查看 https://mai.chongxi.us/
```

恢复后自动推送：

```
【舞萌DX服务器状态恢复】
游戏服务器 ✅ 好
本次约持续 1hr 23min

🔗 详情请查看 https://mai.chongxi.us/
```

## 关于

数据由 [mai.chongxi.us](https://mai.chongxi.us) 提供，基于玩家上报 + 机台探针 + 服务器探针 + QQ群聊监听四方聚合。

## 开发计划

- [x] Auth v2：新密钥体系，支持 `v2_` 前缀 Client ID，兼容现有 v1 用户
- [x] 主动断网通知：服务器状态变化时自动推送告警和恢复通知

## 贡献

欢迎提交 PR。

## 注

本人同时维护前端/后端/探针及bot服务，更新可能有延迟，望谅解。
