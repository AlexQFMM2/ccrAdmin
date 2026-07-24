# 新电脑快速接入 myModels CCR

普通使用者不需要 SSH 登录服务器，也不需要安装隧道软件。

只需要：

```text
1. 安装 VS Code
2. 安装 Claude Code 官方插件
3. 获取管理员分配的 CCR 客户端 Key
4. 创建 ~/.claude/settings.json
5. Reload Window
```

公共模型地址：

```text
https://ccr.example.com
```

本文档为脱敏版本。`ccr.example.com`、`<服务器地址>`、`<SSH用户名>`、
`<CCR管理端口>` 和路径占位符必须替换成管理员实际提供的值。

## 一、管理员先分配 CCR Key

管理员在 CCR 管理端为每台电脑或每位使用者创建独立客户端 Key。

管理员操作流程：

1. 建立管理隧道：

   ```bash
   ssh -NT -L 13458:127.0.0.1:<CCR管理端口> <SSH用户名>@<服务器地址>
   ```

2. 浏览器打开 `http://127.0.0.1:13458`。
3. 进入左侧的 **API 密钥** 页面。
4. 点击 **添加 API 密钥**。
5. 填写名称，例如使用者姓名或设备名。
6. 选择有效期：永不、7 天、30 天、90 天或自定义。
7. 如有需要，展开 **高级设置** 添加请求数、Token 数或图片数限额。
8. 点击 **添加**。
9. 在“API 密钥已创建”弹窗中立即复制并安全保存完整 Key。

完整 Key 应视为只显示一次。关闭创建弹窗后，不要依赖管理端再次显示明文；如果丢失，删除旧 Key 并重新创建。

建议命名：

```text
user-home-pc
user-work-laptop
user-zhangsan
user-lisi
```

Key 格式类似：

```text
ccr_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

注意：

- 给用户的是 CCR 客户端 Key。
- 不要给用户 DeepSeek 的真实 API Key。
- 不要把 CCR 管理令牌发给用户。
- 每个人使用独立 Key，方便撤销、限流和统计。

管理规则：

- 修改有效期或限额：点击对应 Key 的 **编辑 API 密钥**。
- 立即停止某人访问：点击 **移除 API 密钥**，删除后立即失效。
- Key 泄露：删除旧 Key、创建新 Key，并让使用者更新 `ANTHROPIC_AUTH_TOKEN`。
- 不要多人共用同一个 Key，否则无法区分用量，也无法单独撤销。
- 初次共享建议设置有效期和请求次数上限；根据日志中的真实用量再调整 Token 限额。

## 二、安装客户端

1. 安装 VS Code。
2. 打开 VS Code 扩展商店。
3. 搜索并安装 Anthropic 官方 `Claude Code` 插件。

不需要在新电脑安装或配置 SSH。

## 三、创建 Claude Code 配置

配置文件位置：

```text
Linux / macOS：~/.claude/settings.json
Windows：%USERPROFILE%\.claude\settings.json
```

如果 `.claude` 目录不存在，先创建它。

把下面的 `<管理员分配的CCR客户端Key>` 替换成真实客户端 Key：

```json
{
  "env": {
    "ANTHROPIC_AUTH_TOKEN": "<管理员分配的CCR客户端Key>",
    "ANTHROPIC_BASE_URL": "https://ccr.example.com",
    "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",

    "ANTHROPIC_MODEL": "deepseek-v4-pro[1m]",
    "ANTHROPIC_DEFAULT_OPUS_MODEL": "deepseek-v4-pro[1m]",
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "deepseek-v4-pro[1m]",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "deepseek-v4-flash",
    "ANTHROPIC_SMALL_FAST_MODEL": "deepseek-v4-flash",
    "CLAUDE_CODE_SUBAGENT_MODEL": "deepseek-v4-flash",

    "CLAUDE_CODE_EFFORT_LEVEL": "max",
    "CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY": "1"
  },
  "companyAnnouncements": [
    "您正在使用 myModels CCR 🚀"
  ]
}
```

## 四、避免 VS Code 重复配置

在 VS Code 执行：

```text
Ctrl+Shift+P
Preferences: Open User Settings (JSON)
```

如果存在：

```json
"claudeCode.environmentVariables": [
  ...
]
```

删除整个配置块。

这样 VS Code 插件和终端 Claude Code 会统一读取：

```text
~/.claude/settings.json
```

## 五、重新加载 VS Code

执行：

```text
Ctrl+Shift+P
Developer: Reload Window
```

然后新建 Claude 会话，不要继续旧会话。

发送：

```text
你好
```

能够正常回复即接入成功。

## 六、确认 1M 模型

打开 `Switch model` 或输入：

```text
/model
```

模型列表应包含类似：

```text
DeepSeek/DeepSeek V4 Pro (1M context)
```

CCR 当前已验证：

```text
模型：DeepSeek V4 Pro
最大输入：1,050,000 Tokens
supports_1m_context：true
one_million_context_variant：true
```

配置关系：

```text
Claude Code：deepseek-v4-pro[1m]
              ↓
CCR 识别 1M 上下文能力
              ↓
CCR 上游：deepseek-v4-pro
              ↓
DeepSeek API
```

不要在 CCR Provider 中把真实上游模型改成字面量 `deepseek-v4-pro[1m]`。CCR Provider 应保持基础模型名：

```text
deepseek-v4-pro
```

`[1m]` 是 Claude Code 侧的上下文能力标记。

## 七、可选：测试 Claude CLI

如果电脑上可以运行 `claude` 命令：

```bash
claude -p --output-format text "只回复：OK"
```

正常结果：

```text
OK
```

## 八、常见问题

### `401` 或认证失败

原因通常是：

- CCR 客户端 Key 填错；
- Key 被管理员撤销；
- 误用了 CCR 管理令牌；
- 误用了 DeepSeek API Key。

处理：让管理员在 CCR `API Keys` 页面重新创建客户端 Key。

### `400 All target providers failed`

检查：

```text
本地 Claude Code：deepseek-v4-pro[1m]
服务器 CCR Provider：deepseek-v4-pro
```

同时确认本地配置包含：

```json
"CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY": "1"
```

修改后 Reload Window，并新建会话。

### VS Code 和终端表现不一致

检查 VS Code 用户设置中是否还有：

```json
"claudeCode.environmentVariables"
```

删除重复配置后 Reload Window。

### 模型列表没有 1M 版本

确认：

```json
"ANTHROPIC_MODEL": "deepseek-v4-pro[1m]",
"CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY": "1"
```

然后新建会话。

### 域名无法访问

检查：

```text
https://ccr.example.com/health
```

正常情况下会返回 `status: running`。

## 九、管理员说明

普通用户只能访问模型 API，不能通过公网打开 CCR 管理后台。

公网允许：

```text
/v1/*
/v1beta/*
/messages
/chat/completions
/responses
/interactions
/mcp/*
/health
```

公网禁止：

```text
/
/pages/*
/api/ccr/rpc
```

管理员仍通过 SSH 隧道访问管理端：

```bash
ssh -NT \
  -L 13458:127.0.0.1:<CCR管理端口> \
  <SSH用户名>@<服务器地址>
```

然后打开：

```text
http://127.0.0.1:13458
```

查看容器：

```bash
ssh <SSH用户名>@<服务器地址> \
  "docker ps --filter name=myModels"
```

查看日志：

```bash
ssh <SSH用户名>@<服务器地址> \
  "docker logs --tail 100 myModels"
```

服务器部署目录：

```text
<服务器部署目录>
```

Nginx 公网配置：

```text
<Nginx配置文件路径>
```

TLS 证书：

```text
<TLS证书目录>
```

证书由 Certbot 自动续期。

## 十、最短接入清单

```text
□ 安装 VS Code
□ 安装 Claude Code 官方插件
□ 向管理员领取个人 CCR 客户端 Key
□ 创建 ~/.claude/settings.json
□ 删除 VS Code 中重复的 claudeCode.environmentVariables
□ Developer: Reload Window
□ 新建会话
□ 确认 DeepSeek V4 Pro (1M context)
```
