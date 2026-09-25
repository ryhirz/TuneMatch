"""音频处理服务（可选重依赖，import 防护）。

- librosa：音频特征提取（MFCC/频谱/节奏/调性 → 向量 → ChromaDB）
- Whisper：语音转文本
- Chromaprint + AcoustID：哼唱/环境音识曲
未安装对应依赖时返回 501 语义的错误信息（由路由层映射）。
"""
from typing import Any, Optional

# ---- 惰性导入探测 ----
def _has(pkg: str) -> bool:
    try:
        __import__(pkg)
        return True
    except Exception:
        return False


LIBROSA_OK = _has("librosa")
WHISPER_OK = _has("whisper")
ACOUSTID_OK = _has("pyacoustid")
NUMPY_OK = _has("numpy")


def capabilities() -> dict[str, bool]:
    return {
        "librosa": LIBROSA_OK,
        "whisper": WHISPER_OK,
        "acoustid": ACOUSTID_OK,
        "numpy": NUMPY_OK,
    }


def extract_features(file_bytes: bytes) -> tuple[Optional[list[float]], Optional[str]]:
    """librosa 提取 48 维特征向量（MFCC 均值 + 频谱 + 节奏 + 调性）。

    返回 (features, error)。未安装 librosa 时 features=None, error=说明。
    """
    if not LIBROSA_OK:
        return None, "librosa 未安装（pip install librosa numpy soundfile）"
    try:
        import io

        import librosa
        import numpy as np

        y, sr = librosa.load(io.BytesIO(file_bytes), sr=22050, mono=True, duration=30)
        if len(y) < sr:  # 音频过短
            return None, "音频过短，无法提取特征"

        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        mfcc_mean = np.mean(mfcc, axis=1)
        spectral_centroid = np.mean(librosa.feature.spectral_centroid(y=y, sr=sr))
        spectral_bandwidth = np.mean(librosa.feature.spectral_bandwidth(y=y, sr=sr))
        rolloff = np.mean(librosa.feature.spectral_rolloff(y=y, sr=sr))
        zero_crossing = np.mean(librosa.feature.zero_crossing_rate(y))
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)

        # 调性（简单近似：chroma 均值）
        chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
        chroma_mean = np.mean(chroma, axis=1)

        vec = np.concatenate([
            mfcc_mean / (np.max(np.abs(mfcc_mean)) + 1e-9),      # 13 维归一化 MFCC
            [spectral_centroid / (sr / 2 + 1e-9)],               # 1 维
            [spectral_bandwidth / (sr / 2 + 1e-9)],              # 1 维
            [rolloff / (sr / 2 + 1e-9)],                         # 1 维
            [zero_crossing],                                     # 1 维
            [float(tempo) / 200.0],                              # 1 维
            chroma_mean,                                         # 12 维
        ])
        return [round(float(x), 6) for x in vec], None
    except Exception as e:  # pragma: no cover
        return None, f"特征提取失败: {e}"


def transcribe(file_bytes: bytes) -> tuple[Optional[str], Optional[str]]:
    """Whisper 语音转文本。返回 (text, error)。"""
    if not WHISPER_OK:
        return None, "whisper 未安装（pip install openai-whisper）"
    try:
        import io

        import whisper

        model = whisper.load_model("base")
        result = model.transcribe(io.BytesIO(file_bytes))
        return result.get("text", "").strip(), None
    except Exception as e:  # pragma: no cover
        return None, f"语音识别失败: {e}"


def fingerprint(file_bytes: bytes, api_key: str) -> tuple[Optional[dict[str, Any]], Optional[str]]:
    """Chromaprint + AcoustID 识曲。返回 (recording 信息, error)。"""
    if not ACOUSTID_OK:
        return None, "pyacoustid 未安装（pip install pyacoustid audioread）"
    if not api_key:
        return None, "未配置 ACOUSTID_API_KEY"
    try:
        import acoustid

        results = acoustid.match(api_key, file_bytes)
        if not results:
            return None, "未识别到匹配曲目"
        best = results[0][1]
        return {
            "title": best.get("title", ""),
            "artist": best.get("artist", ""),
            "score": results[0][0],
        }, None
    except Exception as e:  # pragma: no cover
        return None, f"识曲失败: {e}"
