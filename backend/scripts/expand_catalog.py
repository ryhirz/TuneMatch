"""批量扩展曲库：从 Jamendo 多 tag 拉取 500+ 首曲目。

用法：python -m scripts.expand_catalog 7d0b6f06
"""
import asyncio
import sys
import time

from db import SessionLocal
from services import jamendo as j

# 主流曲风标签（覆盖 25+ 分类）
TAGS = [
    'pop', 'rock', 'folk', 'electronic', 'hip-hop', 'jazz', 'classical',
    'lofi', 'ambient', 'dance', 'chill', 'indie', 'instrumental',
    'piano', 'acoustic', 'metal', 'reggae', 'blues', 'country',
    'soundtrack', 'world', 'orchestral', 'vocal', '90s', '80s',
    'cinematic', 'meditation', 'epic', 'sad', 'happy', 'energetic',
    'romantic', 'dream', 'study', 'sleep', 'workout', 'party',
]

PER_TAG = 30  # 每个 tag 拉 30 首

async def main():
    client_id = sys.argv[1] if len(sys.argv) > 1 else '7d0b6f06'
    print(f'使用 client_id: {client_id}')
    print(f'计划 {len(TAGS)} 个 tag × {PER_TAG} 首 = {len(TAGS) * PER_TAG} 首')
    db = SessionLocal()
    t0 = time.time()
    total_imported = 0
    failed_tags = []
    for tag in TAGS:
        try:
            result = await j.sync_from_jamendo(db, client_id, query='', tags=tag, limit=PER_TAG)
            cnt = result['imported']
            total_imported += cnt
            print(f'  [{tag:>15s}] +{cnt} 首 (库内已 {result["total"]} 返回,去重后实际新增 {cnt})')
        except Exception as e:
            print(f'  [{tag:>15s}] ❌ {e}')
            failed_tags.append(tag)
        await asyncio.sleep(0.5)  # 礼貌限速
    total = db.query(j.Song).count() if hasattr(j, 'Song') else 0
    from models import Song
    total = db.query(Song).count()
    print(f'\n🎉 同步完成 · 新增 {total_imported} 首 · 库内总数 {total} · 耗时 {time.time()-t0:.0f}s')
    if failed_tags:
        print(f'⚠️ 失败 tags: {failed_tags}')
    db.close()

if __name__ == '__main__':
    asyncio.run(main())
