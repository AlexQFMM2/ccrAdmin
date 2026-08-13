# CCR Docker 快速部署

这套文件来自实际运行的 Docker 部署，但已经移除服务器地址、域名、用户名、密钥、运行数据和历史备份。构建源码固定为公开上游：

```text
仓库：https://github.com/musistudio/claude-code-router
提交：f22f2a4c79b2ad51b2b947377f285769470f6e09
许可：MIT
```

`Dockerfile.tencent` 与该提交的上游 Dockerfile 功能相同，仅将 Debian 软件源切换为腾讯云镜像，以改善中国大陆服务器的构建速度。

## 前置条件

- Linux 服务器；
- Git；
- Docker Engine；
- Docker Compose v2，即 `docker compose` 命令。

## 一键部署

在本仓库中执行：

```bash
cd deploy/ccr
chmod +x deploy.sh
./deploy.sh
```

脚本会：

1. 创建权限受限的 `.env`，并生成随机的 CCR 管理 Token；
2. 将固定版本的上游 CCR 源码克隆到被 Git 忽略的 `app/`；
3. 使用腾讯云 Debian 镜像构建容器；
4. 创建持久化 Docker 卷；
5. 应用 `patches/` 中针对该固定版本验证过的 CCR 功能补丁；
6. 默认将管理端口发布到服务器的 `127.0.0.1:18080`。

当前补丁增加原生 Bilibili MCP 管理页。部署前还需在 `.env` 中填写与独立
`bilibili-mcp` 容器一致的 `BILIBILI_ADMIN_TOKEN` 和 `BILIBILI_MCP_TOKEN`。

`.env`、`app/` 和运行数据均被 `.gitignore` 排除，不会提交到仓库。

查看状态和日志：

```bash
docker compose ps
docker compose logs -f ccr
```

停止或重新启动：

```bash
docker compose stop
docker compose up -d
```

不要随意执行 `docker compose down --volumes`，该命令会删除 CCR 持久化数据。

## 配置端口或公开地址

首次运行后可以编辑 `.env`：

```text
CCR_BIND_HOST=127.0.0.1
CCR_HOST_PORT=18080
CCR_PUBLIC_BASE_URL=http://127.0.0.1:18080
```

修改后重新创建容器：

```bash
docker compose up -d --build
```

建议保留 `CCR_BIND_HOST=127.0.0.1`，通过 SSH 隧道管理，不要直接把管理页面暴露到公网。如果修改 `CCR_HOST_PORT`，应同步修改 `CCR_PUBLIC_BASE_URL` 中的端口。

## 使用 ccrAdmin 打开管理界面

从 GitHub Releases 下载 `ccrAdmin-windows-x64.zip`：

<https://github.com/AlexQFMM2/ccrAdmin/releases/latest>

解压并运行 `ccrAdmin.exe`，填写：

```text
服务器：安装 Docker 的服务器地址
SSH 端口：服务器的 SSH 端口，通常为 22
用户名：服务器 SSH 用户名
密码：当前 SSH 密码，每次连接都必须重新输入
服务器 CCR 端口：.env 中的 CCR_HOST_PORT，默认示例为 18080
本地端口：本机未被占用的端口，例如 13458
```

点击“连接服务器”，成功后点击“打开 CCR 管理界面”。应用会建立：

```text
本机 127.0.0.1:<本地端口>
        ↓ SSH
服务器 127.0.0.1:<CCR_HOST_PORT>
        ↓ Docker
CCR 容器 8080
```

关闭 ccrAdmin 会立即断开 SSH 隧道。应用可以记住服务器、用户名和端口，但不会保存 SSH 密码。

## 安全说明

- 不要提交 `.env`、`app/`、Docker 卷内容、SQLite 数据库或任何备份；
- 不要把管理 Token、Provider API Key 或 CCR 客户端 Key 写入 Compose 文件；
- Docker 端口默认仅绑定服务器回环地址；
- 首次使用 ccrAdmin 时，应核对 SSH 主机密钥指纹；
- Provider、模型和 CCR 客户端 Key 应在管理界面中配置。
