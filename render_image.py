#!/usr/bin/env python3
"""Render the front page for Sunday 22 November 2026.

Reads stories.json (next to this file), draws a classic broadsheet front
page with PIL, and writes entry.png next to this file (or to the path
given as the first command-line argument). No network, no randomness:
the same stories.json always produces the same bytes.
"""

import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent

PAGE = 1024
MARGIN = 38
CONTENT_W = PAGE - 2 * MARGIN
GUTTER = 30
COL_W = (CONTENT_W - GUTTER) // 2

PAPER = (249, 246, 238)
INK = (17, 17, 17)
RED = (166, 27, 27)
RULE = (60, 60, 60)
FAINT = (150, 144, 132)

BOLD = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
REGULAR = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"


def font(path, size):
    return ImageFont.truetype(path, size)


def text_w(draw, s, fnt):
    return draw.textlength(s, font=fnt)


def wrap(draw, text, fnt, max_w):
    """Greedy word wrap; returns the list of lines."""
    lines = []
    current = ""
    for word in text.split():
        trial = word if not current else current + " " + word
        if text_w(draw, trial, fnt) <= max_w:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def fit_size(draw, text, path, max_w, start):
    """Largest font size <= start at which text fits on one line."""
    size = start
    while size > 10:
        fnt = font(path, size)
        if text_w(draw, text, fnt) <= max_w:
            return fnt
        size -= 2
    return font(path, size)


def spaced_width(draw, text, fnt, spacing):
    return sum(text_w(draw, ch, fnt) for ch in text) + spacing * (len(text) - 1)


def draw_spaced(draw, cx, y, text, fnt, spacing, fill):
    """Draw letter-spaced text centred on cx; returns its height."""
    total = spaced_width(draw, text, fnt, spacing)
    x = cx - total / 2
    for ch in text:
        draw.text((x, y), ch, font=fnt, fill=fill)
        x += text_w(draw, ch, fnt) + spacing
    return fnt.size


def panel_layout(draw, story, head_size, body_size, width):
    """Measure one panel: returns (label_f, head_lines, head_f, body_lines, body_f, height)."""
    label_f = font(BOLD, 21)
    head_f = font(BOLD, head_size)
    body_f = font(REGULAR, body_size)
    head_lines = wrap(draw, story["headline"], head_f, width)
    body_lines = wrap(draw, story["body"], body_f, width)
    # matches draw_panel exactly: 34 to the first headline line, 3 after it
    height = 37 + len(head_lines) * int(head_size * 1.18) + len(body_lines) * int(body_size * 1.28)
    return label_f, head_lines, head_f, body_lines, body_f, height


def draw_panel(draw, x, y, story, lay):
    label_f, head_lines, head_f, body_lines, body_f, _ = lay
    draw.text((x, y), story["label"], font=label_f, fill=RED)
    draw.rectangle([x, y + 25, x + 44, y + 28], fill=RED)
    cy = y + 34
    for line in head_lines:
        draw.text((x, cy), line, font=head_f, fill=INK)
        cy += int(head_f.size * 1.18)
    cy += 3
    for line in body_lines:
        draw.text((x, cy), line, font=body_f, fill=INK)
        cy += int(body_f.size * 1.28)
    return cy


def main():
    stories = json.loads((HERE / "stories.json").read_text(encoding="utf-8"))
    lead = next(s for s in stories if s["role"] == "lead")
    panels = [s for s in stories if s["role"] == "panel"]

    img = Image.new("RGB", (PAGE, PAGE), PAPER)
    draw = ImageDraw.Draw(img)
    cx = PAGE // 2

    # ---- Masthead ------------------------------------------------------
    y = 18
    draw.rectangle([MARGIN, y, PAGE - MARGIN, y + 5], fill=INK)
    draw.rectangle([MARGIN, y + 8, PAGE - MARGIN, y + 9], fill=INK)
    y += 14
    title_f = fit_size(draw, "THE WORLD IN ONE PICTURE", BOLD, CONTENT_W, 78)
    tw = text_w(draw, "THE WORLD IN ONE PICTURE", title_f)
    draw.text((cx - tw / 2, y), "THE WORLD IN ONE PICTURE", font=title_f, fill=INK)
    y += int(title_f.size * 1.22)

    day_f = font(BOLD, 32)
    y += 2
    draw_spaced(draw, cx, y, "SUNDAY", day_f, 26, RED)
    y += int(day_f.size * 1.3)

    date_f = fit_size(draw, "22 NOVEMBER 2026", BOLD, CONTENT_W, 88)
    dw = text_w(draw, "22 NOVEMBER 2026", date_f)
    draw.text((cx - dw / 2, y), "22 NOVEMBER 2026", font=date_f, fill=INK)
    y += int(date_f.size * 1.24)
    draw.rectangle([MARGIN, y, PAGE - MARGIN, y + 4], fill=RED)
    y += 14

    # ---- Lead story ----------------------------------------------------
    lead_label_f = font(BOLD, 22)
    draw.text((MARGIN, y), lead["label"], font=lead_label_f, fill=RED)
    draw.rectangle([MARGIN, y + 26, MARGIN + 52, y + 29], fill=RED)
    y += 36
    lead_head_f = font(BOLD, 46)
    for line in wrap(draw, lead["headline"], lead_head_f, CONTENT_W):
        draw.text((MARGIN, y), line, font=lead_head_f, fill=INK)
        y += int(46 * 1.16)
    y += 4
    lead_body_f = font(REGULAR, 22)
    for line in wrap(draw, lead["body"], lead_body_f, CONTENT_W):
        draw.text((MARGIN, y), line, font=lead_body_f, fill=INK)
        y += int(22 * 1.28)
    y += 10
    draw.rectangle([MARGIN, y, PAGE - MARGIN, y + 2], fill=RULE)
    grid_top = y + 14

    # ---- Panel grid ----------------------------------------------------
    # Two rows of two columns, then the last panel spans the full width.
    grid_bottom = PAGE - 46
    head_size, body_size = 30, 20
    while True:
        lays = [panel_layout(draw, s, head_size, body_size, COL_W) for s in panels[:4]]
        lays.append(panel_layout(draw, panels[4], head_size, body_size, CONTENT_W))
        row_h = [max(lays[0][5], lays[1][5]), max(lays[2][5], lays[3][5]), lays[4][5]]
        total = sum(row_h) + 2 * 14
        if total <= grid_bottom - grid_top or (head_size <= 25 and body_size <= 18):
            break
        head_size -= 1
        body_size -= 1

    rows_y = []
    yy = grid_top
    for r in range(3):
        rows_y.append(yy)
        yy += row_h[r] + 14

    col_x = [MARGIN, MARGIN + COL_W + GUTTER]
    for i in range(4):
        r, c = divmod(i, 2)
        draw_panel(draw, col_x[c], rows_y[r], panels[i], lays[i])
    draw_panel(draw, MARGIN, rows_y[2], panels[4], lays[4])

    # column divider (top two rows) and row rules
    div_x = MARGIN + COL_W + GUTTER // 2
    draw.line([div_x, grid_top + 2, div_x, rows_y[1] + row_h[1] - 4], fill=FAINT, width=1)
    for r in range(2):
        ry = rows_y[r] + row_h[r] + 6
        draw.line([MARGIN, ry, PAGE - MARGIN, ry], fill=FAINT, width=1)

    # ---- Footer --------------------------------------------------------
    fy = PAGE - 32
    draw.rectangle([MARGIN, fy - 8, PAGE - MARGIN, fy - 6], fill=INK)
    foot_f = font(REGULAR, 19)
    foot = "Six stories from one day, on one page"
    fw = text_w(draw, foot, foot_f)
    draw.text((cx - fw / 2, fy), foot, font=foot_f, fill=RULE)

    out = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "entry.png"
    img.save(out, format="PNG", optimize=True)
    print(f"wrote {out} ({out.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
