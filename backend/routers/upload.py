"""音频上传路由：识曲（AcoustID）/ 特征提取（librosa）/ 语音转文本（Whisper）。"""
import base64

from fastapi import APIRouter, File, Form, UploadFile

import config
from schemas import err, ok
from services import audio as audio_svc

router = APIRouter(prefix="/api/upload", tags=["upload"])


@router.post("/audio")
async def upload_audio(
    file: UploadFile = File(...),
    mode: str = Form(default="fingerprint", pattern="^(fingerprint|features|voice)$"),
) -> dict:
    """上传音频。

    - mode=fingerprint：Chromaprint+AcoustID 识曲
    - mode=features：librosa 提取特征向量
    - mode=voice：Whisper 语音转文本
    """
    data = await file.read()
    if not data:
        return err(422, "文件为空")

    if mode == "features":
        features, fe_err = audio_svc.extract_features(data)
        if fe_err:
            return err(501, fe_err)
        return ok({"features": features, "dim": len(features or [])})

    if mode == "voice":
        text, tr_err = audio_svc.transcribe(data)
        if tr_err:
            return err(501, tr_err)
        return ok({"text": text})

    # fingerprint
    result, fp_err = audio_svc.fingerprint(data, config.ACOUSTID_API_KEY)
    if fp_err:
        return err(501, fp_err)
    return ok(result)
