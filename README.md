# ccrAdmin

用于安全打开 myModels CCR 管理界面的本地桌面工具。

应用通过 SSH 建立本地端口转发，本地端口和服务器 CCR 端口都可以在界面中设置：

```text
http://127.0.0.1:13458
        ↓ SSH
服务器 127.0.0.1:<CCR 端口>
```

首次运行不会预填服务器地址、用户名或 CCR 端口。用户可以选择记住服务器、SSH 端口、用户名、CCR 端口和本地端口；SSH 密码只在当前连接期间用于认证，不写入配置文件或日志，而且每次发起连接后都会立即从输入框清除。关闭应用或点击“断开连接”会关闭隧道。

## 运行

需要 Python 3.10 或更高版本。

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py
```

如果系统没有 `python3-venv`、但已经安装了 `uv`，可以改用：

```bash
uv venv --system-site-packages --python /usr/bin/python3 .venv
uv pip install --python .venv/bin/python -r requirements.txt
.venv/bin/python main.py
```

也可以安装为命令：

```bash
python -m pip install -e .
ccr-admin
```

## 首次连接

首次连接服务器时，应用会显示 SSH 主机密钥指纹。请与服务器管理员核对后再接受。应用会读取当前用户已有的 `~/.ssh/known_hosts`，新接受的主机密钥则单独保存到 `~/.ccrAdmin/known_hosts`；以后如果服务器密钥变化，应用会拒绝连接并给出警告。

## Windows 打包

在 Windows 的虚拟环境中执行：

```powershell
python -m pip install -r requirements-build.txt
pyinstaller --noconfirm --clean --onefile --windowed --name CCR管理工具 main.py
```

生成文件位于 `dist/CCR管理工具.exe`。

## GitHub Actions 自动构建

仓库包含 Windows 自动构建流程：

- 推送到 `main`：运行测试、构建 Windows x64 单文件程序并上传 Artifact；
- 在 GitHub 页面手动运行 `Windows Portable Build`：执行同样的构建；
- 推送 `v*` 标签：构建 Artifact，并把 ZIP 自动添加到对应的 GitHub Release。

Artifact 名称为 `ccrAdmin-windows-x64`，压缩包内包含：

```text
ccrAdmin.exe
README.md
新电脑接入_myModels_CCR_指南.md
```

发布新版本示例：

```bash
git tag v0.1.0
git push origin v0.1.0
```

## 安全约束

- 本地转发仅监听 `127.0.0.1`，不会向局域网开放。
- 应用只允许记住非敏感连接信息，不保存 SSH 密码。
- 每次建立新连接都必须重新输入 SSH 密码。
- 取消“记住连接信息”或点击“清除记录”会删除已经保存的服务器连接信息。
- 不要在未核对指纹的情况下接受陌生的 SSH 主机密钥。
- 不要把 CCR 客户端 Key、服务器密码或其他密钥提交到仓库。
