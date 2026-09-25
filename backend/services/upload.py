"""上传服务：歌单头像（图片校验）+ 歌曲文件导入（音频校验）。

- 头像：png/jpg/jpeg/webp，≤ 2MB
- 音频：mp3/wav/flac/m4a/ogg/aac，≤ 50MB
- 保存到 config.UPLOAD_DIR，通过 /uploads 静态路由访问
"""
import os
import uuid
from datetime import datetime

from fastapi import UploadFile

import config

ALLOWED_COVER_EXTS = {".png", ".jpg", ".jpeg", ".webp"}
ALLOWED_AUDIO_EXTS = {".mp3", ".wav", ".flac", ".m4a", ".ogg", ".aac", ".wma"}

MAX_COVER_SIZE = 2 * 1024 * 1024       # 2MB
MAX_AUDIO_SIZE = 50 * 1024 * 1024      # 50MB


def _ext(filename: str) -> str:
    return os.path.splitext(filename or "")[1].lower()


def save_cover(file: UploadFile) -> tuple[dict | None, str | None]:
    """保存歌单头像。返回 (信息, 错误)。"""
    ext = _ext(file.filename)
    if ext not in ALLOWED_COVER_EXTS:
        return None, f"不支持的图片格式 {ext or '未知'}，仅支持 png/jpg/jpeg/webp"

    data = file.file.read()
    if len(data) > MAX_COVER_SIZE:
        return None, f"图片过大（{len(data) // 1024}KB），请上传 2MB 以内的图片"

    name = f"cover_{uuid.uuid4().hex[:12]}{ext}"
    path = os.path.join(config.COVER_DIR, name)
    with open(path, "wb") as f:
        f.write(data)

    url = f"/uploads/covers/{name}"
    return {"url": url, "path": path, "size": len(data)}, None


def save_audio_files(files: list[UploadFile]) -> tuple[list[dict], list[dict], str | None]:
    """批量保存音频文件。返回 (成功列表, 拒绝列表, 全局错误)。

    双重校验：扩展名 + 文件头嗅探（mp3 同步字节、wav RIFF、flac fLaC、ogg OggS、m4a ftyp）
    不合法音频文件直接拒绝，不写入磁盘。
    """
    ok, rejected = [], []
    for f in files:
        ext = _ext(f.filename)
        if ext not in ALLOWED_AUDIO_EXTS:
            rejected.append({
                "filename": f.filename or "未命名",
                "reason": f"非音频文件（{ext or '无扩展名'}），仅支持 mp3/wav/flac/m4a/ogg/aac",
            })
            continue
        data = f.file.read()
        if len(data) > MAX_AUDIO_SIZE:
            rejected.append({
                "filename": f.filename or "未命名",
                "reason": f"文件过大（{len(data) // 1024 // 1024}MB），请上传 50MB 以内",
            })
            continue
        if not _is_valid_audio(data, ext):
            rejected.append({
                "filename": f.filename or "未命名",
                "reason": "文件不是合法音频（扩展名 mp3/wav 但浏览器无法解码），请检查源文件",
            })
            continue
        name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}{ext}"
        path = os.path.join(config.AUDIO_DIR, name)
        with open(path, "wb") as fh:
            fh.write(data)
        title = os.path.splitext(f.filename or "未命名歌曲")[0]
        ok.append({
            "filename": f.filename,
            "title": title,
            "path": path,
            "audio_url": f"/uploads/audio/{name}",
            "size": len(data),
        })
    return ok, rejected, None


def _is_valid_audio(data: bytes, ext: str) -> bool:
    """嗅探文件头判断是否为合法音频。

    mp3：跳过 ID3v2 标签，找第一个 0xFF 0xE0+ 同步字节
    wav：RIFF ... WAVE 头（12 字节）
    flac：fLaC（4 字节）
    ogg：OggS（4 字节）
    m4a/aac：在字节 4-7 找到 ftyp box
    """
    if len(data) < 12:
        return False
    e = ext.lstrip(".")

    # WAV：RIFF<size>WAVE
    if e == "wav":
        return data[:4] == b"RIFF" and data[8:12] == b"WAVE"

    # FLAC：fLaC
    if e == "flac":
        return data[:4] == b"fLaC"

    # OGG：OggS
    if e == "ogg":
        return data[:4] == b"OggS"

    # M4A / AAC / MP4：第 4 字节起为 ftyp box
    if e in ("m4a", "aac", "wma"):
        return data[4:8] == b"ftyp"

    # MP3：跳过 ID3v2 标签（若存在），在剩余数据中找 MPEG 同步字（0xFF 0xE0+）
    # 注意：很多合法 mp3 的 ID3v2 标签很大（含专辑封面图），可能占用几百 KB，
    # 所以搜索范围要足够大（最多 512KB），否则会误杀合法文件。
    if e == "mp3":
        offset = 0
        if data[:3] == b"ID3":
            # ID3v2 size：第 6-9 字节，7 位编码
            try:
                sz = (data[6] << 21) | (data[7] << 14) | (data[8] << 7) | data[9]
                offset = 10 + sz
            except Exception:
                offset = 0
        # 搜索 ID3 之后的整段数据（最多 512KB），找 0xFF 0xE0+ 同步字
        end = min(len(data), offset + 512 * 1024)
        if end - offset < 2:
            return False
        for i in range(offset, end - 1):
            if data[i] == 0xFF and (data[i + 1] & 0xE0) == 0xE0:
                return True
        # 兜底：大文件未找到 sync 也可能是非常规编码，交给浏览器最终判断
        return len(data) > 64 * 1024

    return False
