# Gemini AI Chat Assistant

这是一个基于 Python 和 Google Gemini API 的简单 AI 聊天助手，支持单次会话上下文。

## 目录结构

- `chat.py`: 主程序逻辑。
- `requirements.txt`: Python 依赖库。
- `Dockerfile`: 用于构建 Docker 镜像的配置文件。

## 前置条件

你需要一个 Google Gemini 的 API Key。

## 如何运行

### 1. 构建 Docker 镜像

在当前目录下（`gemini_chat_assistant`）运行以下命令：

```bash
docker build -t gemini-chat .
```

### 2. 运行容器

使用以下命令启动聊天助手，请将 `YOUR_API_KEY_HERE` 替换为你实际的 API Key：

```bash
docker run -it --rm  -e HTTP_PROXY=http://host.docker.internal:7897 -e HTTPS_PROXY=http://host.docker.internal:7897 gemini-chat
```

注意：必须使用 `-it` 参数，以便能够与终端进行交互输入。

### 本地开发 (可选)

如果你想在本地直接运行而不使用 Docker：

1. 安装依赖: `pip install -r requirements.txt`
2. 设置环境变量 `GEMINI_API_KEY` 或者创建一个 `.env` 文件。
3. 运行: `python chat.py`
