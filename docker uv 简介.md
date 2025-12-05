# 环境配置指南：Docker 与现代 Python 工程化


---

## 引言：两大痛点与两层解法

在科研和工程落地中，我们面临两个层面的混乱：

1.  **系统级混乱**：“我电脑上能跑，你那怎么不行？”（底层库、OS差异）$\rightarrow$ **解法：Docker**
2.  **依赖级混乱**：“pip install 了一堆，过两个月 requirements.txt 居然装不上了。” $\rightarrow$ **解法：uv**

---

## 第一部分：Docker —— 容器化实战攻略

*(核心逻辑参考 B站 CodeSheep《40分钟Docker实战》)*


### 1. 核心概念：集装箱思维

Docker 并不是虚拟机，它更像是一个轻量级的“应用集装箱”。


**三个核心名词：**

*   **Image (镜像)**：类的定义（只读安装包，如 `python:3.9`）。
*   **Container (容器)**：类的实例（运行中的进程，用完即焚）。
*   **Repository (仓库)**：放镜像的地方（类似 GitHub）。

### 2. 实战命令：“五步走”闭环

不用死记硬背，掌握这 5 步即可应对 90% 的场景：

**Step 1: 找 (Pull)**

```bash
docker pull python:3.9
```

**Step 2: 跑 (Run) —— 最核心一步**

牢记“三剑客”参数：

```bash
docker run -d -p 8080:80 -v $(pwd):/app --name my-app python:3.9
```

*   `-d` (Detached)：后台静默运行。
*   `-p` (Port)：端口映射 (主机:容器)。别人访问你的 8080，就是访问容器的 80。
*   `-v` (Volume)：挂载数据卷 (主机路径:容器路径)。开发神器——你在外面改代码，容器里实时生效，不用反复打包！

**Step 3: 看 (Ps)**

```bash
docker ps       # 看活着的
docker ps -a    # 看所有的（包括挂掉的）
```

**Step 4: 进 (Exec)**

容器在后台跑，怎么进去调试？

```bash
docker exec -it <容器ID> /bin/bash
```

**Step 5: 停/删 (Stop/Rm)**

```bash
docker stop <容器ID>
docker rm <容器ID>
```

### 3. Dockerfile 与镜像构建：将代码打包

前面我们学会了拉取现有的镜像来运行容器。但更多时候，我们需要将自己的项目代码打包成一个镜像。这时，就需要编写 `Dockerfile`。

`Dockerfile` 是一个包含用户可以调用来组装镜像的所有命令的文本文档。你可以把它想象成制作镜像的“菜谱”。

**常用指令速查：**

*   `FROM`：指定基础镜像。例如 `FROM python:3.9-slim-buster`。
*   `WORKDIR`：设置工作目录。后续命令（如 `COPY`, `RUN`, `CMD`）都会在该目录下执行。
*   `COPY`：复制文件或目录到镜像中。
*   `RUN`：在镜像构建过程中执行命令。常用于安装依赖。
*   `EXPOSE`：声明容器运行时监听的端口。
*   `ENV`：设置环境变量。
*   `CMD`：容器启动时执行的默认命令。

**示例 `Dockerfile` (适用于本项目或其他 Python 项目)：**

在项目根目录下创建一个名为 `Dockerfile` 的文件，内容如下：

```dockerfile
# 使用官方 Python 3.9 的轻量级镜像作为基础
FROM python:3.9-slim-buster

# 设置工作目录
WORKDIR /app

# 将当前目录下的 requirements.txt 复制到容器的 /app 目录下
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 将当前项目的所有文件复制到容器的 /app 目录下
COPY . .

# 暴露端口 (如果你的应用是 Web 服务)
# EXPOSE 8000

# 定义容器启动时要执行的命令
CMD ["python", "chat.py"]
```

**构建镜像：**

在 `Dockerfile` 所在的目录 (即项目根目录) 执行以下命令：

```bash

docker build -t clsfantasy/gemini-chat-assistant:latest .
```

*   `-t` (Tag)：给镜像命名和打标签。`<your-username>/<image-name>:<tag>` 是推荐格式。
*   `.`：表示 `Dockerfile` 在当前目录下。

构建成功后，你就可以用 `docker run` 命令来运行你的新镜像了！

**分享镜像：推送 (Push)**

如果你想在服务器或其他电脑上使用这个镜像，需要先将其推送到 Docker Hub：

1.  **登录**：`docker login -u <your-username>`
2.  **推送**：
    ```bash
    docker push <your-username>/<image-name>:<tag>
    ```

### 4. 本项目实战：获取 Gemini Chat Assistant

如果你想直接运行本项目，无需配置本地 Python 环境，请直接拉取镜像：

**1. 拉取镜像 (Pull)**

```bash
docker pull clsfantasy/gemini-chat-assistant:latest
```

**2. 运行容器 (Run)**

由于需要连接 Google API，国内网络环境下必须配置代理（使用 `host.docker.internal` 指向宿主机代理）。

**Windows (PowerShell) 启动命令：**

```powershell
docker run -it --rm 
  -e HTTP_PROXY="http://host.docker.internal:7897" 
  -e HTTPS_PROXY="http://host.docker.internal:7897" 
  clsfantasy/gemini-chat-assistant:latest
```

*   `host.docker.internal`: Docker Desktop 提供的特殊 DNS，允许容器访问宿主机网络。
*   `:7890`: 请替换为你本机代理软件（Clash/v2rayN）的实际端口。

### 5. 关键问题：如何离线发给师弟？

国内网络环境差，或者服务器在内网，直接传文件最稳：

1.  **你打包**：`docker save -o image.tar my-app:v1`
2.  **传文件**：(U盘/微信/网盘)
3.  **他加载**：`docker load -i image.tar`

---

## 第二部分：从 pip 到 uv —— 现代 Python 项目管理

*(参考 B站“从pip到uv”视频核心理念)*

### 1. 为什么要抛弃 pip / requirements.txt？

传统的 `pip install` + `requirements.txt` 有三个致命缺陷：

1.  **锁不住依赖**：你写 `pandas`，它今天装 1.0，明天装 2.0，代码可能就挂了。
2.  **环境污染**：所有包都装在一起，A项目要 `numpy 1.2`，B项目要 `numpy 2.0`，直接打架。
3.  **慢**：pip 是串行下载，uv 是并行下载。

### 2. 什么是“现代”管理流？(uv)

uv 不仅仅是一个“更快的 pip”，它是 Cargo (Rust) 理念在 Python 的实现。它把 pip, pip-tools, virtualenv, pyenv, poetry 全部统一成了一个工具。


**核心工作流 (Hands-on)：**

**0. 安装 uv**

```bash
pip install uv  # 或者 curl 安装
```

**1. 初始化项目 (Init)**

```bash
uv init my-project
cd my-project
```
*变化*：它会自动生成一个 `pyproject.toml`。这是现代 Python 的唯一真理标准，以后别再手写 `requirements.txt` 了。

**2. 声明式添加依赖 (Add)**

```bash
uv add numpy requests
```
*发生了什么*：
*   自动创建虚拟环境 `.venv` (不用你操心)。
*   自动下载最新兼容版本。
*   自动生成 `uv.lock` (全平台锁定文件，保证师弟装出来的包和你一模一样，一个 bit 都不差)。

**3. 运行 (Run)**

```bash
uv run app.py
```
*优势*：自动检测环境，哪怕你没激活虚拟环境，它也会用对的环境跑。

**4. 管理 Python 版本 (杀手锏)**

```bash
uv python install 3.10
uv python pin 3.10
```
*牛在哪*：你电脑上甚至不需要预装 Python，uv 会自动给你下载一个独立的 Python 解释器给这个项目用。

---

## 第三部分：终极对比 —— 什么时候用什么？

uv 虽然强，但在深度学习领域，Conda 依然有壁垒。

| 维度 | uv (现代派) | Conda (传统派) |
| :--- | :--- | :--- |
| **核心理念** | 项目级隔离 (`pyproject.toml`) | 环境级隔离 (Anaconda 目录) |
| **杀手锏** | 极速 (秒级)、标准化、Lock文件 | 二进制库管理 (CUDA, cudnn, GDAL) |
| **谁在用** | 后端开发、工具开发、数据分析、90%的场景 | 深度学习 (PyTorch/TF)、生物信息、地理信息 |
| **缺点** | 装不了系统级的非 Python 库 (如 C++ 动态库) | 慢、臃肿、Solver 容易卡死 |

### 总结建议

1.  **做 Deep Learning / 需要 CUDA**：
    *   请用 **Mamba** (Conda 的快速版)。
    *   *理由*：uv 目前还不能完美解决 pytorch-cuda 这种复杂的底层驱动依赖。

2.  **写 Python 工具 / 爬虫 / Web / 数据脚本**：
    *   无脑用 **uv**。
    *   *理由*：体验碾压 Conda，且符合现代 Python 标准。

3.  **要给别人交付代码**：
    *   **Docker**。
    *   *理由*：这是终极方案。