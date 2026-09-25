# TuneMatch · AI 智能音乐推荐平台

[![CI](https://github.com/ryhirz/tunematch/actions/workflows/ci.yml/badge.svg)](https://github.com/ryhirz/tunematch/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![Vue](https://img.shields.io/badge/Vue-3-42B883?logo=vuedotjs&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?logo=fastapi&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-blue)

面向年轻音乐爱好者的 AI 智能音乐推荐平台：通过文本 / 语音 / 标签 / 音频等多模态输入获得个性化推荐，AI 完成音乐特征解析、情绪匹配、曲风归类与推荐理由生成。

> 全栈项目：**Vue 3 + TypeScript** 前端 · **FastAPI + SQLAlchemy** 后端 · SQLite 曲库 **777 首** · 后端 **45** 个 pytest 用例 · 前端 **11** 个页面。

---

## 🚀 30 秒上手

**两条路，挑一条走：**

### A · 只想看看效果 → 直接点开在线 Demo

**🔗 https://1d1b65ea9e5841928436535de31eda1d.app.workbuddy.host**

不用安装、不用注册、不需要任何 Key。建议按这个顺序点：

| 步骤 | 做什么 | 你会看到 |
|---|---|---|
| 1 | 首页输入「适合学习的轻音乐」 | 带**匹配度**的推荐列表 + 推荐理由 |
| 2 | 进入 **AI 助手**，说「想听浪漫的歌」 | SSE **流式**回复，逐字吐字 + 歌曲卡片 |
| 3 | 点任意歌曲进详情页 | 真实封面 + 歌词 + 可直接播放的音频 |

> ✅ Demo 跑的是**真实后端**，不是静态录屏：AI 对话 / 推荐 / 歌词 / 歌单读写全部在线。
> ℹ️ 未配置 LLM Key，自动走规则引擎降级 —— 这是刻意设计：**无 Key、甚至断网也不白屏**。

### B · 想本地跑起来 → 复制这几行

```bash
git clone https://github.com/ryhirz/TuneMatch.git && cd TuneMatch
cd backend  && pip install -r requirements.txt && uvicorn main:app --port 8000   # 终端 1
cd frontend && npm install && npm run dev                                        # 终端 2
```

打开 **http://localhost:5173** —— 曲库 **777 首已随仓库附带**（`backend/tunematch.db`），无需额外准备数据。

> 详细步骤、环境要求、常见报错见 **[QUICKSTART.md](QUICKSTART.md)**。

---

## ✨ 核心亮点

- **多模态输入**：自然语言 / 标签 / 种子歌曲 / 音频（识曲 / 特征）四种方式
- **LLM 供应商可热切换**：默认硅基流动（SiliconFlow），支持 DeepSeek / OpenAI / 任意 OpenAI 兼容端点
- **全链路无 Key 降级**：不配任何 Key 即可完整演示（规则解析 + 模板理由 + Mock 曲库）
- **真实曲库**：SQLite `backend/tunematch.db` 共 **777 首**（iTunes 真实封面/试听 + Jamendo CC 全曲 + Apple 热门榜）；`data/music_library.json` 与 `frontend/src/assets/music_library.json` 均为从曲库导出的 **777 首**镜像（前端离线兜底 / 离线重建种子，口径与数据库一致）
- **统一响应格式**：`{code, message, data}`，前端自动 Mock 兜底
- **可验证**：GitHub Actions CI（后端 pytest + 前端构建/测试）绿灯

## 🧱 技术栈

| 层 | 选型 |
|---|---|
| 前端 | Vue 3 + TypeScript + Vite + Tailwind CSS + Pinia + Vue Router 4 + Axios |
| 后端 | FastAPI + Uvicorn + SQLAlchemy ORM（SQLite）+ Pydantic v2 |
| 向量检索 | ChromaDB（可选，未装自动降级） |
| LLM | OpenAI SDK 兼容（SiliconFlow / DeepSeek / OpenAI，环境变量切换） |
| 音频 | librosa（特征）· Whisper（语音）· Chromaprint+AcoustID（识曲，均可选） |
| 导出 | ReportLab（PDF 歌单）· Pillow（分享海报，均可选） |

## 📁 目录结构

```
tunematch/
├── frontend/                 # Vue3 前端（11 页面 + 10 组件）
│   └── src/
│       ├── api/              # index.ts（真实）/ mock.ts（离线兜底）/ types.ts
│       ├── components/       # SongCard / PlayerBar / EqualizerPanel / ToastHost ...
│       ├── views/            # Home / Scene / Genre / SongDetail / Playlist / AIChat /
│       │                     # Recommendations / WeeklyReport / Profile / Settings / Help
│       ├── stores/           # Pinia：player / chat / playlist / toast
│       └── router/
├── backend/                  # FastAPI 后端
│   ├── main.py               # 入口（CORS + 统一异常 + /health）
│   ├── routers/              # songs / recommend / playlists / chat(SSE) / catalog /
│   │                         # upload / export / config / feedback（9 个模块）
│   ├── services/             # recommend / jamendo / catalog / lyrics / playlist_import /
│   │                         # audio / upload / llm / chroma / export（11 个）
│   ├── models/ schemas/      # SQLAlchemy 模型 + Pydantic v2 校验
│   ├── tests/                # pytest（45 用例全绿，零外部依赖）
│   └── tunematch.db          # SQLite 曲库（777 首）
├── data/music_library.json   # 777 首种子曲库镜像（含 mood_tags / cover_color）
├── scripts/init_library.py   # 曲库导入（SQLite + ChromaDB）
├── .github/workflows/ci.yml  # GitHub Actions：后端 pytest + 前端 build/test
├── .env.example
├── LICENSE
└── Makefile
```

## 🚀 快速开始

```bash
# 0. 克隆
git clone https://github.com/ryhirz/TuneMatch.git
cd TuneMatch
```

### 1. 后端（端口 8000）

```bash
cd backend
pip install -r requirements.txt          # 核心依赖（不装可选重依赖也能跑）
uvicorn main:app --reload --port 8000    # 启动
```

验证：`curl http://localhost:8000/health` —— 交互式文档：http://localhost:8000/docs

> 曲库已随仓库附带（`backend/tunematch.db`，777 首），开箱即用；如需从种子重建：`python ../scripts/init_library.py`。

### 2. 前端（端口 5173）

```bash
cd frontend
npm install
npm run dev
```

打开 http://localhost:5173 即可使用。**后端未启动时前端自动进入 Mock 模式**，可独立演示。

> 也可以使用 Makefile：`make seed && make backend` / `make frontend`

## 🚢 线上部署（单服务全栈）

部署平台只暴露**一个端口**，因此把「后端 + 曲库 + 前端产物」打成一份，由 FastAPI 在同一端口同时提供 `/api/*` 与前端页面（同源，无跨域、无需配置 API 地址）。

```bash
# 1. 构建前端产物
cd frontend && npm run build && cd ..

# 2. 组装部署目录 tunematch/deploy/（后端源码 + 曲库 + webapp/，约 2MB）
python scripts/build_fullstack_deploy.py

# 3. 以 deploy/ 为项目目录发布（Python 服务）
#    installCmd: pip install -r requirements.txt
#    startCmd:   MUSIC_LIBRARY_PATH=./data/music_library.json uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
```

| 环境变量 | 说明 |
|---|---|
| `WEBAPP_DIR` | 前端产物目录，默认 `./webapp`；目录内无 `index.html` 时自动退回纯 API 模式 |
| `MUSIC_LIBRARY_PATH` | 曲库种子路径；部署时需指向包内副本 `./data/music_library.json` |

实现要点（`backend/main.py`）：

- 通配兜底路由注册在**所有 `/api` 路由之后**，否则接口会被抢先匹配成 `index.html`
- `api` / `uploads` / `docs` / `redoc` / `openapi.json` / `health` 为保留前缀，未命中返回 404 JSON 而非 HTML
- 静态文件解析后校验仍在 `WEBAPP_DIR` 内，防目录穿越
- `config.py` 中 DB / 上传 / 导出路径均为 **CWD 相对**，必须以部署目录为工作目录启动

> 不直接部署 `backend/` 的原因：`backend/uploads/` 含本地测试音视频（约 43MB）与演示无关；且部署平台会排除 `dist/` 这类构建产物目录名，故前端产物统一落在 `webapp/`。

## 🖼️ 演示

- **在线 Demo（全栈，推荐用这个）**：https://1d1b65ea9e5841928436535de31eda1d.app.workbuddy.host
  - 含真实后端：AI 对话（SSE）/ AI 推荐 / 歌词 / 歌单 CRUD 均可用
  - 未配置 LLM Key，走规则引擎降级，因此**打开即用、不会白屏**
- 本地运行：见上方「🚀 30 秒上手 → B」或 [QUICKSTART.md](QUICKSTART.md)，无需任何 API Key 即可完整体验。
- 项目报告与答辩材料：`deliverable/TuneMatch项目报告.pdf`、`deliverable/TuneMatch答辩PPT/`

> Demo 为免费沙箱托管，**首次访问可能需 10~20 秒冷启动**；若长时间无响应请刷新一次。
> 线上 SQLite 是沙箱临时副本，你在 Demo 里创建的歌单**不会写回仓库**，也不影响本地。

## 🔑 LLM 供应商切换

编辑 `.env`（或环境变量）：

```bash
LLM_BASE_URL=https://api.siliconflow.cn/v1    # 硅基流动（默认）
LLM_API_KEY=sk-xxx
LLM_MODEL_NAME=deepseek-ai/DeepSeek-V3
```

| 供应商 | LLM_BASE_URL | LLM_MODEL_NAME 示例 |
|---|---|---|
| 硅基流动 | `https://api.siliconflow.cn/v1` | `deepseek-ai/DeepSeek-V3` |
| DeepSeek 官方 | `https://api.deepseek.com/v1` | `deepseek-chat` |
| OpenAI | `https://api.openai.com/v1` | `gpt-4o-mini` |
| 任意兼容端点 | 你的 base_url | 你的模型名 |

## 📡 API 一览

统一响应：`{ "code": 0, "message": "success", "data": {...} }`；错误码 422 / 404 / 500。

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/health` | 健康检查（LLM / ChromaDB / 音频能力状态） |
| GET | `/api/songs` | 歌曲列表（`?genre=&mood=&keyword=&q=` 含全文搜索） |
| GET | `/api/songs/{id}` | 歌曲详情 |
| GET | `/api/songs/meta/genres` | 曲风列表 |
| POST | `/api/recommend` | AI 推荐（text / tags / seed / audio） |
| GET/POST | `/api/playlists` | 歌单列表 / 创建 |
| PUT/DELETE | `/api/playlists/{id}` | 更新 / 删除 |
| POST | `/api/playlists/{id}/songs` | 添加歌曲（重复 422） |
| DELETE | `/api/playlists/{id}/songs/{songId}` | 移除歌曲 |
| POST | `/api/playlists/{id}/import-text` | 外部歌单文本导入 |
| POST | `/api/chat` | AI 对话（SSE 流式） |
| GET | `/api/chat/history` | 历史对话 |
| POST | `/api/catalog/sync` · `/jamendo` · `/hot` | 曲库同步（iTunes / Jamendo / Apple 热门榜） |
| POST | `/api/upload/audio` | 音频上传（fingerprint / features / voice） |
| GET | `/api/export/playlist/{id}/pdf` | 导出歌单 PDF |
| GET | `/api/export/playlist/{id}/poster` | 生成分享海报 |

## 🧪 测试

```bash
# 后端（45 用例，零外部依赖，使用临时数据库）
cd backend && pytest tests/ -q

# 前端（类型检查 + 构建）
cd frontend && npm run build

# 前端单元测试（Vitest）
cd frontend && npm run test
```

CI 配置见 `.github/workflows/ci.yml`，push / PR 自动运行后端测试与前端构建测试。

## 🎨 设计系统

- 极简蓝调 Apple 变体，**无阴影**，靠留白 + 细边框分层
- 主色 `#007AFF`，背景 `#F5F5F7`，卡片 `#FFFFFF`，边框 `#E5E5EA`
- 封面 8 色占位：`#FF6B6B #FFA94D #FFD43B #69DB7C #38D9A9 #4DABF7 #748FFC #F783AC`
- 全局播放条 64px 固定底部（<768 简化 56px）
- 响应式四断点：≥1440 / 1024-1439 / 768-1023 / <768，无横向滚动
- 所有颜色 / 间距 / 圆角通过 Tailwind tokens 引用，禁止硬编码

## 📋 环境变量

| 变量 | 说明 | 必须 |
|---|---|---|
| `LLM_BASE_URL` / `LLM_API_KEY` / `LLM_MODEL_NAME` | LLM 供应商 | 否（无 Key 降级规则） |
| `DATABASE_URL` | SQLite 连接串 | 否（默认 ./tunematch.db） |
| `CHROMA_PERSIST_DIR` | ChromaDB 持久化目录 | 否 |
| `ACOUSTID_API_KEY` | 识曲服务 key | 否 |
| `VITE_API_BASE` | 前端 API 地址 | 否（开发默认 `http://localhost:8000`；生产构建默认同源相对基址） |

> `.env` 与 `data/settings.json` 已在 `.gitignore` 中忽略，密钥不会入库。

## ✅ 交付自检表

- [x] 颜色全部引用 token（Tailwind `brand/bg/card/line/ink/playing/ai/danger/cover`，无硬编码）
- [x] 播放条 64px 固定底部（`<768` 简化 56px）
- [x] 响应式四断点（≥1440 / 1024-1439 / 768-1023 / <768）
- [x] 无横向滚动（`overflow-x: hidden` + 弹性布局）
- [x] LLM 供应商可通过环境变量切换
- [x] 后端 pytest 全部通过（**45** 用例，零外部依赖）
- [x] 前端 `vue-tsc` + `vite build` 通过（**零错误**）
- [x] 前端 Vitest 通过（**4** 用例）
- [x] GitHub Actions CI 绿灯
- [x] 前后端联调打通（Vite proxy `/api` → :8000）
- [x] 线上全栈 Demo 已上线并验证（单端口：前端 SPA + `/api` 同源，AI 对话 / 推荐 / 歌词走真实后端）

## 📄 许可

本项目以 [MIT License](LICENSE) 开源。
