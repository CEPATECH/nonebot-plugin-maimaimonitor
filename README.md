# NoneBot Plugin: Maimai Monitor

一个为 [NoneBot2](https://nonebot.dev/) 框架设计的插件，用于监听群聊上报 maimai DX 服务器状态，并提供实时状态查询。

## 功能

- **实时状态查询**：`/net` 或发送「网咋样」「炸了吗」，直接获取服务器当前状态
- **手动上报**：通过 `/report` 命令上报故障类型
- **自动监听**：在群聊中自动识别玩家自然语言，无需手动触发命令
- **冯氏指数**：自动识别「华立老冯起飞/返航」等

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
| `MAIMAI_BOT_CLIENT_ID` | `str` | 无 | ClientID（必填）|
| `MAIMAI_BOT_PRIVATE_KEY` | `str` | 无 | 私钥（必填）|
| `MAIMAI_BOT_DISPLAY_NAME` | `str` | `qwq` | Bot显示名称 |
| `MAIMAI_WORKER_URL` | `str` | `https://maiapi.chongxi.us` | 上报API地址 |

获取 ClientID 和私钥请联系：qwq@chongxi.us

## 使用

### 查看服务器状态
发送 `/net`、`网咋样` 或 `炸了吗`

```
【舞萌DX游戏服务器状态】
游戏服务器 ✅ 好
⏱ 当前延迟：396ms｜负载：正常｜延迟高波动

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

- 主语：华立、SEGA、服务器、机台、NET 等
- 动词：炸、挂、死、坏、崩 等
- 示例：「服务器又炸了」「SEGA挂了」「机台灰网」

- 示例：「服务器好了」「华立稳了」「绿网了」

**冯氏指数**
- 起飞（异常）：「华立冯飞了」「SEGA老冯起飞」
- 返航（正常）：「华立冯返航了」「SEGA老冯落地」

## 关于

数据由 [mai.chongxi.us](https://mai.chongxi.us) 提供，基于玩家上报 + 机台探针 + 服务器探针三方聚合。

## 开发计划

- [x] Auth v2：新密钥体系，支持 `v2_` 前缀 Client ID，兼容现有 v1 用户
- [ ] 主动断网通知：检测到异常激增时，bot 自动推送告警到所在群

## 贡献

欢迎提交 PR。

## 注
由于本人同时维护服务器监测的前端/后端/探针以及bot服务，可能有不及时更新的情况，望谅解
