"""构建「单服务全栈」部署目录：tunematch/deploy/

背景
----
线上部署要求 **单端口单服务**。本脚本把「后端 + 曲库 + 前端构建产物」打包成一个
可直接发布的目录，由 FastAPI 在同一端口同时提供 /api 与前端页面。

产出结构
--------
    deploy/
      main.py  config.py  db.py  requirements.txt
      models/  routers/  schemas/  services/  scripts/
      tunematch.db               # 现有曲库（777 首）
      data/music_library.json    # 曲库种子（导入/兜底用）
      webapp/                    # 前端构建产物（frontend/dist 拷贝而来）

为什么不直接部署 backend/
-------------------------
1. backend/uploads/ 含约 43MB 本地测试上传音视频，与演示无关，会拖慢甚至拖垮上传；
2. 部署平台会排除 `dist/` 这类构建产物目录名，故前端产物统一落在 webapp/；
3. 需要额外携带 data/ 与 webapp/，保持 backend/ 作为唯一源码真源。

前置条件：前端已构建（frontend/dist/index.html 存在）。
用法：
    python scripts/build_fullstack_deploy.py

部署（平台侧）：
    项目目录 = tunematch/deploy
    language  = python
    startCmd  = uvicorn main:app --host 0.0.0.0 --port $PORT
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent          # tunematch/
BACKEND = ROOT / "backend"
FRONTEND_DIST = ROOT / "frontend" / "dist"
DATA_SEED = ROOT / "data" / "music_library.json"
DEPLOY = ROOT / "deploy"

# 后端需要随包分发的源码（显式白名单，避免误带本地数据）
BACKEND_FILES = ("main.py", "config.py", "db.py", "requirements.txt")
BACKEND_DIRS = ("models", "routers", "schemas", "services", "scripts")

# 拷贝时忽略的产物（即便出现在 whitelist 目录里也不带上）
IGNORE = shutil.ignore_patterns(
    "__pycache__", "*.pyc", "*.pyo", ".pytest_cache", ".env", "*.log",
    "uploads", "test_uploads", "exports", "chroma_data",
)


def _copy(src: Path, dst: Path, *, is_dir: bool) -> None:
    """拷贝文件/目录；已存在则覆盖合并（沙箱禁止删除，故不做 rmtree 清理）。"""
    if is_dir:
        shutil.copytree(src, dst, ignore=IGNORE, dirs_exist_ok=True)
    else:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def _size_mb(path: Path) -> float:
    if path.is_file():
        return path.stat().st_size / 1024 / 1024
    return sum(f.stat().st_size for f in path.rglob("*") if f.is_file()) / 1024 / 1024


def main() -> int:
    print(f"[1/5] 校验前置条件")
    if not (BACKEND / "main.py").is_file():
        print(f"  ✗ 未找到后端源码：{BACKEND / 'main.py'}")
        return 1
    if not (FRONTEND_DIST / "index.html").is_file():
        print(f"  ✗ 未找到前端构建产物：{FRONTEND_DIST / 'index.html'}")
        print("    请先执行：cd frontend && npm run build")
        return 1
    print(f"  ✓ 后端源码 {BACKEND}")
    print(f"  ✓ 前端产物 {FRONTEND_DIST}")

    print(f"[2/5] 清理并准备部署目录 {DEPLOY}")
    DEPLOY.mkdir(parents=True, exist_ok=True)
    print(f"  ✓ 就绪")

    print(f"[3/5] 拷贝后端源码")
    for name in BACKEND_FILES:
        src = BACKEND / name
        if not src.is_file():
            print(f"  ! 跳过缺失文件：{name}")
            continue
        _copy(src, DEPLOY / name, is_dir=False)
        print(f"  + {name}")
    for name in BACKEND_DIRS:
        src = BACKEND / name
        if not src.is_dir():
            print(f"  ! 跳过缺失目录：{name}/")
            continue
        _copy(src, DEPLOY / name, is_dir=True)
        print(f"  + {name}/")

    print(f"[4/5] 拷贝运行期数据")
    db_src = BACKEND / "tunematch.db"
    if db_src.is_file():
        _copy(db_src, DEPLOY / "tunematch.db", is_dir=False)
        print(f"  + tunematch.db ({_size_mb(db_src):.2f} MB)")
    else:
        print("  ! 未找到 tunematch.db，首次启动将自动建库（曲库为空）")
    if DATA_SEED.is_file():
        _copy(DATA_SEED, DEPLOY / "data" / "music_library.json", is_dir=False)
        print(f"  + data/music_library.json ({_size_mb(DATA_SEED):.2f} MB)")
    else:
        print("  ! 未找到曲库种子 data/music_library.json（仅影响种子导入，不影响运行时）")

    print(f"[5/5] 拷贝前端产物 → webapp/")
    _copy(FRONTEND_DIST, DEPLOY / "webapp", is_dir=True)
    assets = DEPLOY / "webapp" / "assets"
    n_assets = len(list(assets.glob("*"))) if assets.is_dir() else 0
    print(f"  + webapp/ （{n_assets} 个静态资源，{_size_mb(DEPLOY / 'webapp'):.2f} MB）")

    total = _size_mb(DEPLOY)
    print(f"\n✅ 部署目录构建完成：{DEPLOY}")
    print(f"   总大小 {total:.2f} MB")
    print(f"   校验 index.html: {(DEPLOY / 'webapp' / 'index.html').is_file()}")
    print(f"   校验 tunematch.db: {(DEPLOY / 'tunematch.db').is_file()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
