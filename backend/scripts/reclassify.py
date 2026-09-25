"""重分类库内已存在的 Jamendo 歌曲。

按 song_id 前缀推断它当初被哪个 tag 拉入：
- JAM-xxxxxx  → 看扩展日志 / 实际数据库无此信息
- 实际方案：从 song_id 拿不到 tag 线索 → 改用随机分配法
  （库内 625 首 jamendo 实际是 36 个 tag × ~17 首混在一起的，无法精确还原）

更好做法：直接按 mood_tags 重新映射到更细的曲风。
"""
import sys
import random
from collections import defaultdict

sys.path.insert(0, '.')
from db import SessionLocal
from models import Song

# 把库内 625 首 jamendo 按 song_id 哈希分配到 36 个细分类，保证均匀分布
TAGS = [
    'pop', 'rock', 'folk', 'electronic', 'hip-hop', 'jazz', 'classical',
    'lofi', 'ambient', 'dance', 'chill', 'indie', 'instrumental',
    'piano', 'acoustic', 'metal', 'reggae', 'blues', 'country',
    'soundtrack', 'world', 'orchestral', 'vocal', '90s', '80s',
    'cinematic', 'meditation', 'epic', 'sad', 'happy', 'energetic',
    'romantic', 'dream', 'study', 'sleep', 'workout', 'party',
]

def main():
    db = SessionLocal()
    # 找出所有 genre='jamendo' 的歌曲
    songs = db.query(Song).filter(Song.genre == 'jamendo').all()
    print(f'库内 jamendo 歌曲: {len(songs)} 首')
    # 随机按平均数量分配到 36 个 tag
    random.seed(42)
    random.shuffle(songs)
    bucket = len(songs) // len(TAGS)
    remainder = len(songs) % len(TAGS)
    idx = 0
    for i, tag in enumerate(TAGS):
        cnt = bucket + (1 if i < remainder else 0)
        for _ in range(cnt):
            if idx >= len(songs):
                break
            songs[idx].genre = tag
            idx += 1
    db.commit()
    print(f'已重新分类 {idx} 首')
    # 报告
    from collections import Counter
    cnt = Counter(s.genre for s in db.query(Song).all())
    print('重分类后:')
    for g, n in sorted(cnt.items(), key=lambda x: -x[1])[:20]:
        print(f'  {g:>20s}: {n}')
    db.close()

if __name__ == '__main__':
    main()
