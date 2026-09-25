"""导出服务：PDF 歌单卡片（ReportLab）+ 社交分享海报（Pillow）。

可选重依赖（import 防护）：reportlab / pillow 未安装时返回错误信息。
"""
import os
from typing import Optional

import config
from schemas import SongOut

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    _REPORTLAB_OK = True
except Exception:  # pragma: no cover
    _REPORTLAB_OK = False

try:
    from PIL import Image, ImageDraw, ImageFont
    _PIL_OK = True
except Exception:  # pragma: no cover
    _PIL_OK = False


def export_pdf(playlist_name: str, songs: list[SongOut]) -> tuple[Optional[str], Optional[str]]:
    """导出歌单 PDF，返回 (文件路径, error)。"""
    if not _REPORTLAB_OK:
        return None, "reportlab 未安装（pip install reportlab）"
    if not songs:
        return None, "歌单为空"

    filename = os.path.join(config.EXPORT_DIR, f"playlist_{playlist_name or 'untitled'}.pdf")
    doc = SimpleDocTemplate(filename, pagesize=A4,
                            rightMargin=20 * mm, leftMargin=20 * mm,
                            topMargin=18 * mm, bottomMargin=18 * mm)

    title_style = ParagraphStyle("Title", fontSize=18, leading=24,
                                 textColor=colors.HexColor("#1D1D1F"), spaceAfter=4 * mm)
    sub_style = ParagraphStyle("Sub", fontSize=10, leading=14,
                               textColor=colors.HexColor("#86868B"), spaceAfter=8 * mm)
    song_style = ParagraphStyle("Song", fontSize=11, leading=16,
                                textColor=colors.HexColor("#1D1D1F"))

    story = [Paragraph(playlist_name, title_style),
             Paragraph(f"共 {len(songs)} 首 · TuneMatch AI 智能推荐", sub_style)]

    rows = [["#", "歌曲", "歌手", "曲风", "匹配度"]]
    for i, s in enumerate(songs, 1):
        rows.append([str(i), Paragraph(s.title, song_style), s.artist,
                     s.genre or "-", f"{s.match}%"])
    table = Table(rows, colWidths=[12 * mm, 80 * mm, 40 * mm, 30 * mm, 20 * mm], repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F5F5F7")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#1D1D1F")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E5EA")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#FAFAFC")]),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(table)
    doc.build(story)
    return filename, None


def export_poster(playlist_name: str, songs: list[SongOut]) -> tuple[Optional[str], Optional[str]]:
    """生成 1080×1350 分享海报，返回 (文件路径, error)。"""
    if not _PIL_OK:
        return None, "pillow 未安装（pip install pillow）"
    if not songs:
        return None, "歌单为空"

    W, H = 1080, 1350
    img = Image.new("RGB", (W, H), "#F5F5F7")
    draw = ImageDraw.Draw(img)
    _font = ImageFont.load_default()

    # 标题区
    draw.rounded_rectangle([60, 60, W - 60, 220], radius=20, fill="#FFFFFF")
    draw.text((100, 100), playlist_name, fill="#1D1D1F", font=_font)
    draw.text((100, 170), f"TuneMatch · {len(songs)} 首", fill="#86868B", font=_font)

    # 歌曲卡片列表（封面色块 + 歌名）
    y = 260
    for i, s in enumerate(songs[:8]):
        x0, x1 = 60, W - 60
        draw.rounded_rectangle([x0, y, x1, y + 110], radius=16, fill="#FFFFFF")
        draw.rounded_rectangle([x0 + 16, y + 15, x0 + 80, y + 95], radius=10,
                               fill=_hex(s.cover_color))
        draw.text((x0 + 100, y + 30), s.title, fill="#1D1D1F", font=_font)
        draw.text((x0 + 100, y + 62), f"{s.artist} · {s.match}%", fill="#86868B", font=_font)
        y += 130
        if i >= 7:
            break

    filename = os.path.join(config.EXPORT_DIR, f"poster_{playlist_name or 'untitled'}.png")
    img.save(filename, "PNG")
    return filename, None


def _hex(color: str) -> tuple:
    """'#4DABF7' → (77, 171, 247)。"""
    c = (color or "#4DABF7").lstrip("#")
    if len(c) != 6:
        c = "4DABF7"
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))
