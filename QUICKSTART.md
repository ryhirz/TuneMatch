# TuneMatch · 30 秒上手指引

给第一次接触这个项目的人。两条路，按需挑一条。

| 我想… | 去看 | 耗时 |
|---|---|---|
| 先看效果，不想装环境 | **[路径 A：在线 Demo](#a--在线-demo)** | 30 秒 |
| 克隆到本地跑起来 | **[路径 B：本地运行](#b--本地运行)** | 5 分钟 |

---

## A · 在线 Demo

### 打开这个链接

**https://1d1b65ea9e5841928436535de31eda1d.app.workbuddy.host**

不用安装、不用注册、不需要任何 API Key。

### 建议这样逛（约 2 分钟）

| # | 操作 | 你应该看到 |
|---|---|---|
| 1 | 首页输入框填「**适合学习的轻音乐**」，回车 | 一组带**匹配度百分比**的歌曲，每首附推荐理由 |
| 2 | 左侧进入 **AI 助手**，输入「**想听浪漫的歌**」 | 文字**逐字流式**吐出，随后附上歌曲卡片 |
| 3 | 点任意歌曲进详情页 | 真实专辑封面 + 歌词 + 可直接播放的音频 |
| 4 | **场景**页任选一个场景（如「深夜 coding」） | 按场景标签筛选出的歌单 |
| 5 | **我的歌单** → 新建歌单并添加歌曲 | 真实写入后端（刷新后仍在） |

### 这个 Demo 是真家伙

它跑的是**完整的 FastAPI 后端**，不是静态录屏、也不是假数据：

- ✅ AI 对话（SSE 流式）· AI 推荐 · 歌词拉取 · 歌单增删改 · 曲库搜索 —— **全部真实可用**
- ✅ 曲库 **777 首**真实数据（真实封面 + 可播放音频）

### 两个你可能误会的事

**❓「没配 LLM Key，那 AI 是不是假的？」**
不是假的，是**降级**。项目刻意做了「全链路无 Key 降级」：没有 LLM Key 时自动切换到「规则引擎 + 11 维音乐特征」计算——你输入「适合学习」，它会解析出「安静、纯音乐、lofi」这类特征再去曲库匹配。

这套设计的意义是：**演示现场没网、没额度、Key 过期都不会白屏**。同一个推荐接口，配置 Key 后会改由 LLM 做意图解析，在规则之上再叠一层语义理解。

**❓「我在 Demo 里建的歌单会同步到 GitHub 吗？」**
不会。Demo 跑在免费沙箱里，SQLite 是临时副本，**你在上面写的数据不会回流仓库**，也不影响任何人本地的代码。想保存数据请走路径 B。

<details>
<summary>打不开 / 很慢？</summary>

- 免费沙箱**首次访问需 10~20 秒冷启动**，属正常现象，刷新一次即可。
- 若持续无法访问，可能托管实例已休眠，直接改用路径 B（本地运行，效果完全一致且更快）。

</details>

---

## B · 本地运行

### 环境要求

| 依赖 | 版本 | 备注 |
|---|---|---|
| Python | 3.11+ | 已在 3.11 / 3.13 实测通过 |
| Node.js | 18+ | 推荐 20 LTS 或 22 |
| Git | 任意 | — |

> **不需要**任何 API Key、GPU、外部数据库。曲库 `backend/tunematch.db`（777 首）已随仓库附带。

### 三步启动

```bash
# 1. 克隆
git clone https://github.com/ryhirz/TuneMatch.git
cd TuneMatch

# 2. 后端（终端 1）—— 保持运行
cd backend
pip install -r requirements.txt
uvicorn main:app --port 8000

# 3. 前端（终端 2）
cd frontend
npm install
npm run dev
```

浏览器打开 **http://localhost:5173**。

### 验证装好了没

```bash
curl http://localhost:8000/health
# 期望返回：{"code":0,"message":"success","data":{"status":"ok",...}}

curl "http://localhost:8000/api/songs?q=Coldplay"   # 应返回 Viva La Vida 等
curl http://localhost:8000/docs                     # 交互式 API 文档，推荐打开看看
```

后端 pytest 应全绿：

```bash
cd backend && python -m pytest tests/ -q     # 期望 45 passed
```

### 可选：接真实的 LLM

不配也能正常用（见路径 A 的降级说明）。想体验 LLM 语义解析，在 `backend/` 下建 `.env`：

```bash
LLM_BASE_URL=https://api.siliconflow.cn/v1
LLM_API_KEY=你的密钥
LLM_MODEL=Qwen/Qwen3-8B
```

任何 OpenAI 兼容端点都可以（SiliconFlow / DeepSeek / OpenAI / 本地 vLLM），改 `LLM_BASE_URL` 即可热切换，无需改代码。
可用模型列表：`curl http://localhost:8000/api/config/llm/models`

> ⚠️ `.env` 已在 `.gitignore` 中，**不要使用 `--force` 添加它**。

---

## 常见问题

<details>
<summary><b>后端起不来：端口 8000 已被占用</b></summary>

换端口，并把前端代理一起改：

```bash
uvicorn main:app --port 8010
cd frontend && VITE_API_BASE=http://localhost:8010 npm run dev
```

</details>

<details>
<summary><b>前端页面能打开，但数据空白 / 请求失败</b></summary>

先确认后端活着：`curl http://localhost:8000/health`。

这个项目的容错设计是「后端挂了前端自动降级到 Mock 模式」，所以你会看到界面正常但数据来自本地 JSON —— 这容易被误判为"接口坏了"。浏览器控制台若出现 `checkBackend: false` 即说明走了降级。

</details>

<details>
<summary><b>npm install 很慢或卡住</b></summary>

国内网络常见。切镜像后重试：

```bash
npm config set registry https://registry.npmmirror.com
npm install
```

若遇到 peer 依赖冲突（`ERESOLVE`），加 `--legacy-peer-deps`。

</details>

<details>
<summary><b>pip install 报 “from versions: none” / 找不到包</b></summary>

多是本机 pip 被全局配置重定向到了某个不支持新版 JSON API 的镜像源。显式指定 PyPI 官方源即可：

```bash
pip install -r requirements.txt --index-url https://pypi.org/simple
```

</details>

<details>
<summary><b>Python 3.13 报 No module named 'aifc'</b></summary>

Python 3.13 移除了部分标准库音频模块，`librosa` 会受影响。补两个官方回溯包：

```bash
pip install standard-aifc standard-sunau
```

（仅在你启用音频特征提取这条可选链路时需要；核心功能不受影响。）

</details>

<details>
<summary><b>想从种子 JSON 重建曲库</b></summary>

```bash
python scripts/init_library.py          # 重建 backend/tunematch.db
python scripts/export_library_json.py   # 反向：从 DB 导出种子 JSON（保持口径一致）
```

</details>

---

## 接下来读什么

| 你想了解 | 去看 |
|---|---|
| 12 个功能模块全貌 | [README.md](README.md) → 核心亮点 |
| 接口清单 | [README.md](README.md) → API 一览，或直接开 http://localhost:8000/docs |
| 部署到线上 | [README.md](README.md) → 线上部署（单服务全栈） |
| 环境变量全集 | [README.md](README.md) → 环境变量 |

技术栈一句话：**Vue 3 + TypeScript** 前端 · **FastAPI + SQLAlchemy** 后端 · SQLite 777 首曲库。

---

## 许可

MIT © 2026 Ryhirz
