"""Build PARCHED_final.pptx - light-theme 16:9 deck for CMSC 176 final project.

Editorial light theme: warm paper background, single deep-maroon accent,
serif headers paired with sans-serif body. Run from release/presentation/
with the release/model/.venv activated.
"""
from __future__ import annotations

import os
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Emu, Inches, Pt

# Paths
THIS_DIR = Path(__file__).resolve().parent
RELEASE_DIR = THIS_DIR.parent
FIG_DIR = RELEASE_DIR / "figures"
OUT_PATH = THIS_DIR / "PARCHED_final.pptx"

# Claude palette (use ONLY these)
PAPER = RGBColor(0xFA, 0xF9, 0xF5)   # warm off-white background
INK = RGBColor(0x1F, 0x1E, 0x1D)     # near-black body
MUTED = RGBColor(0x60, 0x5E, 0x5B)   # warm gray caption/source
ACCENT = RGBColor(0x7B, 0x2D, 0x26)  # deep maroon, use sparingly
RULE = RGBColor(0xE8, 0xE4, 0xDC)    # subtle divider (avoid using under titles)

# Fonts
SERIF = "Georgia"
SANS = "Helvetica Neue"

# Slide dimensions (16:9)
SLIDE_W = 13333333
SLIDE_H = 7500000

# Generous margins (~0.75 inch)
MARGIN_L = Emu(700000)
MARGIN_T = Emu(500000)
MARGIN_R = Emu(700000)
CONTENT_W = Emu(SLIDE_W - 1400000)


def set_background(slide, color: RGBColor) -> None:
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = color


def add_text_box(
    slide,
    left,
    top,
    width,
    height,
    text: str,
    *,
    size: int = 16,
    color: RGBColor = INK,
    bold: bool = False,
    italic: bool = False,
    align=PP_ALIGN.LEFT,
    anchor=MSO_ANCHOR.TOP,
    font_name: str = SANS,
):
    tb = slide.shapes.add_textbox(left, top, width, height)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = Emu(0)
    tf.margin_right = Emu(0)
    tf.margin_top = Emu(0)
    tf.margin_bottom = Emu(0)
    tf.vertical_anchor = anchor

    lines = text.split("\n") if isinstance(text, str) else list(text)
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        run = p.add_run()
        run.text = line
        run.font.name = font_name
        run.font.size = Pt(size)
        run.font.bold = bold
        run.font.italic = italic
        run.font.color.rgb = color
    return tb


# Motif: small maroon tick square to the LEFT of every slide title.
TICK_SIZE = Emu(110000)  # ~0.12 inch


def add_title(slide, text: str, *, size: int = 36, top: int = None) -> None:
    """Slide title in serif with a small maroon square motif to its left."""
    if top is None:
        top = int(MARGIN_T)
    # Tick square, vertically aligned near the cap-height of the title text.
    # 1 pt = 12700 EMU. Offset down about 40% of font size to center on cap-height.
    tick_top = top + int(size * 12700 * 0.45)
    tick = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        MARGIN_L,
        Emu(tick_top),
        TICK_SIZE,
        TICK_SIZE,
    )
    tick.line.fill.background()
    tick.fill.solid()
    tick.fill.fore_color.rgb = ACCENT

    title_left = Emu(int(MARGIN_L) + int(TICK_SIZE) + 180000)
    title_width = Emu(int(CONTENT_W) - int(TICK_SIZE) - 180000)
    add_text_box(
        slide,
        title_left,
        Emu(top),
        title_width,
        Emu(900000),
        text,
        size=size,
        color=INK,
        bold=True,
        font_name=SERIF,
    )


def add_bullets(
    slide,
    left,
    top,
    width,
    height,
    bullets,
    *,
    size: int = 16,
    color: RGBColor = INK,
    line_spacing: float = 1.35,
):
    """Body bullets in sans-serif, with a small maroon middle-dot bullet."""
    tb = slide.shapes.add_textbox(left, top, width, height)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = Emu(0)
    tf.margin_right = Emu(0)
    tf.margin_top = Emu(0)
    tf.margin_bottom = Emu(0)
    tf.vertical_anchor = MSO_ANCHOR.TOP

    for i, item in enumerate(bullets):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = PP_ALIGN.LEFT
        p.line_spacing = line_spacing
        # bullet marker (small maroon middle dot)
        marker = p.add_run()
        marker.text = "·  "
        marker.font.name = SANS
        marker.font.size = Pt(size)
        marker.font.bold = True
        marker.font.color.rgb = ACCENT
        # bullet text
        run = p.add_run()
        run.text = item
        run.font.name = SANS
        run.font.size = Pt(size)
        run.font.color.rgb = color
    return tb


def add_footer(slide, slide_no: int, total: int) -> None:
    # Bottom-left: project shortname
    add_text_box(
        slide,
        MARGIN_L,
        Emu(SLIDE_H - 380000),
        Emu(2500000),
        Emu(300000),
        "PARCHED",
        size=9,
        color=MUTED,
        align=PP_ALIGN.LEFT,
        font_name=SANS,
    )
    # Bottom-right: slide number / total
    add_text_box(
        slide,
        Emu(SLIDE_W - 2200000),
        Emu(SLIDE_H - 380000),
        Emu(1500000),
        Emu(300000),
        f"{slide_no} / {total}",
        size=9,
        color=MUTED,
        align=PP_ALIGN.RIGHT,
        font_name=SANS,
    )


def set_speaker_notes(slide, text: str) -> None:
    notes = slide.notes_slide.notes_text_frame
    notes.text = text


def new_slide(prs: Presentation):
    blank = prs.slide_layouts[6]  # blank
    slide = prs.slides.add_slide(blank)
    set_background(slide, PAPER)
    return slide


def add_image_centered(slide, image_path: Path, top_emu: int, max_w_emu: int, max_h_emu: int):
    """Add an image scaled to fit within max_w x max_h, centered horizontally."""
    from PIL import Image

    with Image.open(image_path) as im:
        w_px, h_px = im.size
    aspect = w_px / h_px
    target_w = max_w_emu
    target_h = int(target_w / aspect)
    if target_h > max_h_emu:
        target_h = max_h_emu
        target_w = int(target_h * aspect)
    left = int((SLIDE_W - target_w) / 2)
    slide.shapes.add_picture(
        str(image_path), Emu(left), Emu(top_emu), width=Emu(target_w), height=Emu(target_h)
    )


# ---------------------------------------------------------------------------
# Slide builders
# ---------------------------------------------------------------------------

def slide_1_title(prs):
    s = new_slide(prs)
    # Eyebrow label
    add_text_box(
        s,
        MARGIN_L,
        Emu(1500000),
        CONTENT_W,
        Emu(300000),
        "CMSC 176, FINAL PROJECT",
        size=11,
        color=ACCENT,
        bold=True,
        font_name=SANS,
    )
    # Big serif title (left-aligned)
    add_text_box(
        s,
        MARGIN_L,
        Emu(1900000),
        CONTENT_W,
        Emu(1600000),
        "PARCHED: When AI Drinks\nYour Town Dry",
        size=54,
        color=INK,
        bold=True,
        font_name=SERIF,
    )
    # Subtitle in serif italic
    add_text_box(
        s,
        MARGIN_L,
        Emu(3850000),
        CONTENT_W,
        Emu(600000),
        "An Agent-Based Model of Hyperscaler Water Competition",
        size=22,
        color=MUTED,
        font_name=SERIF,
        italic=True,
    )

    # Authors (sans, restrained)
    add_text_box(
        s,
        MARGIN_L,
        Emu(4900000),
        CONTENT_W,
        Emu(420000),
        "Sheldon Arthur Sagrado   /   Jed Edison Donaire",
        size=16,
        color=INK,
        bold=True,
        font_name=SANS,
    )
    add_text_box(
        s,
        MARGIN_L,
        Emu(5300000),
        CONTENT_W,
        Emu(350000),
        "smsagrado@up.edu.ph    jjdonaire@up.edu.ph",
        size=11,
        color=MUTED,
        font_name=SANS,
    )
    add_text_box(
        s,
        MARGIN_L,
        Emu(5650000),
        CONTENT_W,
        Emu(300000),
        "Equal contribution.",
        size=10,
        color=MUTED,
        italic=True,
        font_name=SANS,
    )

    add_text_box(
        s,
        MARGIN_L,
        Emu(6150000),
        CONTENT_W,
        Emu(350000),
        "CMSC 176, AY 2025-2026, University of the Philippines Cebu",
        size=11,
        color=MUTED,
        font_name=SANS,
    )
    add_text_box(
        s,
        MARGIN_L,
        Emu(6480000),
        CONTENT_W,
        Emu(300000),
        "May 2026",
        size=11,
        color=MUTED,
        font_name=SANS,
    )

    set_speaker_notes(
        s,
        (
            "Good afternoon. I'm Sheldon, this is Jed, and the title says it all: AI has a "
            "water problem nobody talks about. Today we want to show you how bad it gets, "
            "mathematically. Over the next ten minutes we will walk you through an agent-based "
            "model we built that simulates what happens when multiple hyperscale data centers "
            "share a single freshwater basin with farms, households, and a regulator who is "
            "always a couple of years behind. The headline result is that, under unregulated "
            "growth, every single one of our fifty replicate runs collapsed the basin within "
            "five to eight years, and the collapse is nonlinear in a way that makes reactive "
            "policy structurally useless. We will end with three concrete takeaways and the "
            "public repository if you want to play with the code yourself."
        ),
    )


def slide_2_hook(prs):
    s = new_slide(prs)
    add_title(s, "The Hook")

    # Hero serif stat
    add_text_box(
        s,
        MARGIN_L,
        Emu(2000000),
        CONTENT_W,
        Emu(1500000),
        "3 to 5 million liters",
        size=72,
        color=ACCENT,
        bold=True,
        font_name=SERIF,
    )
    add_text_box(
        s,
        MARGIN_L,
        Emu(3500000),
        CONTENT_W,
        Emu(500000),
        "per day, per hyperscale data center.",
        size=22,
        color=INK,
        font_name=SERIF,
        italic=True,
    )
    # Counterpoint
    add_text_box(
        s,
        MARGIN_L,
        Emu(4700000),
        CONTENT_W,
        Emu(700000),
        "And nobody is modeling the basin-level collisions.",
        size=22,
        color=INK,
        bold=True,
        font_name=SANS,
    )
    add_text_box(
        s,
        MARGIN_L,
        Emu(5500000),
        CONTENT_W,
        Emu(500000),
        "Source: Li et al. (2023), \"Making AI Less Thirsty.\"",
        size=10,
        color=MUTED,
        font_name=SANS,
    )

    set_speaker_notes(
        s,
        (
            "Three to five million liters a day. That is the daily on-site freshwater draw of a "
            "single modern hyperscale data center, and it comes straight from Li and colleagues "
            "2023 paper, Making AI Less Thirsty. Now, the figure itself is shocking, but the "
            "more important point is what is missing from the literature. Almost all current "
            "disclosures are self-reported and single-firm. A given operator reports its own "
            "withdrawals, in isolation, against its own sustainability targets. Nobody models "
            "what happens when three, four, or five operators share the same aquifer with the "
            "farms next door and a hundred thousand residents downstream. That gap is exactly "
            "what we built PARCHED to fill. It is, as far as we can find, the first ABM that "
            "treats basin-level competition between hyperscalers as the primary object of study "
            "rather than as a footnote."
        ),
    )


def slide_3_problem(prs):
    s = new_slide(prs)
    add_title(s, "Problem and Research Question")

    # Left column: setup
    add_text_box(
        s,
        MARGIN_L,
        Emu(1700000),
        Emu(5800000),
        Emu(400000),
        "THE SETUP",
        size=11,
        color=ACCENT,
        bold=True,
        font_name=SANS,
    )
    add_bullets(
        s,
        MARGIN_L,
        Emu(2150000),
        Emu(5800000),
        Emu(3800000),
        [
            "One shared freshwater basin (30 BL capacity)",
            "Multiple data centers competing for cooling water",
            "Residential demand (~100k people, growing each year)",
            "Agriculture (rainfed and irrigated fields)",
            "A regulator with delayed observability",
        ],
        size=16,
        line_spacing=1.45,
    )

    # Right column: question
    add_text_box(
        s,
        Emu(7000000),
        Emu(1700000),
        Emu(5800000),
        Emu(400000),
        "THE QUESTION",
        size=11,
        color=ACCENT,
        bold=True,
        font_name=SANS,
    )
    add_text_box(
        s,
        Emu(7000000),
        Emu(2150000),
        Emu(5800000),
        Emu(2200000),
        "What happens when self-interested data centers, blind to each other, share a finite basin?",
        size=22,
        color=INK,
        bold=True,
        font_name=SERIF,
    )
    add_text_box(
        s,
        Emu(7000000),
        Emu(4700000),
        Emu(5800000),
        Emu(1500000),
        "No coordination. No shared meter. No price signal until things break.",
        size=14,
        color=MUTED,
        font_name=SANS,
        italic=True,
    )

    set_speaker_notes(
        s,
        (
            "Here is the setup we model. One basin, finite, with thirty billion liters of "
            "usable capacity. Multiple data centers, all wanting cooling water, all running "
            "their own dispatch logic. Residential demand from roughly one hundred thousand "
            "people, plus agriculture, both rainfed and irrigated. And a regulator who "
            "observes the basin with delay and reacts after a threshold is crossed. The "
            "research question is short: what happens when self-interested data centers, "
            "blind to each other, share a finite basin? I want to stress those three words, "
            "blind to each other, because that is also the situation in real life. There is "
            "no shared metering protocol, no inter-operator price signal, and the regulator "
            "typically only sees the aggregate after something has gone wrong. That is what "
            "makes basin-level dynamics worth simulating instead of solving analytically."
        ),
    )


def slide_4_objectives(prs):
    s = new_slide(prs)
    add_title(s, "Objectives")
    bullets = [
        "Build a calibrated agent-based model of basin-level water competition",
        "Test three hypotheses about collapse timing, nonlinearity, and policy effect",
        "Compare four policy scenarios under matched stochastic conditions",
    ]
    add_bullets(
        s,
        MARGIN_L,
        Emu(2100000),
        CONTENT_W,
        Emu(3500000),
        bullets,
        size=20,
        line_spacing=1.6,
    )
    # Tag line in serif italic
    add_text_box(
        s,
        MARGIN_L,
        Emu(5800000),
        CONTENT_W,
        Emu(500000),
        "Same seeds, same shocks, different rules.",
        size=18,
        color=ACCENT,
        italic=True,
        font_name=SERIF,
        bold=True,
    )

    set_speaker_notes(
        s,
        (
            "Three objectives, in order. First, we build the model itself. That means agents "
            "for the data centers, farms, residents, and a regulator, plus a basin module "
            "that does the bookkeeping on inflows, withdrawals, and stress. Second, we test "
            "three concrete hypotheses, which I will introduce on the next slide. Third, we "
            "run four policy scenarios, A through D, under matched stochastic conditions. "
            "Matched is the key word: every scenario sees the same fifty random seeds, the "
            "same weather realizations, the same demand shocks. That way, when scenario C "
            "outperforms scenario A, we know the difference is the policy rule and not "
            "stochastic luck. This is a small methodological choice but it is what gives the "
            "comparative results their teeth."
        ),
    )


def slide_5_hypotheses(prs):
    s = new_slide(prs)
    add_title(s, "Hypotheses")

    col_w = Emu(3900000)
    gap = Emu(250000)
    left0 = MARGIN_L
    left1 = Emu(int(left0) + int(col_w) + int(gap))
    left2 = Emu(int(left1) + int(col_w) + int(gap))
    top = Emu(1900000)

    def hyp_card(left, label, headline, detail):
        # Label
        add_text_box(
            s,
            left,
            top,
            col_w,
            Emu(400000),
            label,
            size=11,
            color=ACCENT,
            bold=True,
            font_name=SANS,
        )
        # Headline in serif
        add_text_box(
            s,
            left,
            Emu(int(top) + 450000),
            col_w,
            Emu(2200000),
            headline,
            size=20,
            color=INK,
            bold=True,
            font_name=SERIF,
        )
        # Detail in sans muted, placed close beneath the headline
        add_text_box(
            s,
            left,
            Emu(int(top) + 2350000),
            col_w,
            Emu(1800000),
            detail,
            size=13,
            color=MUTED,
            font_name=SANS,
        )

    hyp_card(
        left0,
        "H1   COLLAPSE",
        "Unregulated growth collapses the basin in 5 to 8 years.",
        "Critical-stress crossing under no policy, across 50 replicate runs.",
    )
    hyp_card(
        left1,
        "H2   TIPPING POINT",
        "Decline becomes nonlinear once basin storage drops below 40%.",
        "Cooling-stress positive feedback amplifies withdrawals as headroom shrinks.",
    )
    hyp_card(
        left2,
        "H3   POLICY",
        "Proactive caps delay critical stress by 40% or more.",
        "Reactive caps and staggered entry do not, once measured against matched seeds.",
    )

    set_speaker_notes(
        s,
        (
            "Three hypotheses. H1 says that under unregulated growth the basin collapses on a "
            "five to eight year timeline. That window is from the back-of-envelope balance "
            "between hyperscaler intake rates and basin recharge. H2 is the most interesting "
            "claim and the one where the ABM earns its keep: we expect a tipping point "
            "around forty percent storage, below which decline is no longer linear. That "
            "happens because cooling-tower efficiency depends on water availability, so "
            "stress feeds back into demand. A static water-balance equation cannot show you "
            "that. H3 says proactive caps, set from day one, will delay critical stress by "
            "at least forty percent compared to reactive caps or no policy at all. Each of "
            "these has a clean test, which is what comes next."
        ),
    )


def slide_6_model_overview(prs):
    s = new_slide(prs)
    add_title(s, "Model Overview")

    # Left: bullets
    add_bullets(
        s,
        MARGIN_L,
        Emu(1800000),
        Emu(5400000),
        Emu(4500000),
        [
            "4 data centers (heterogeneous capacity, expand every ~9 months)",
            "2 farms (rainfed and irrigated, seasonal demand)",
            "1 residential community (growing population, compound growth)",
            "1 regulator (delayed observability, 4 policy modes)",
            "30 BL shared basin, stochastic recharge + nonlinear penalty",
            "DC water restoration: configurable replenishment fraction",
        ],
        size=15,
        line_spacing=1.45,
    )
    add_text_box(
        s,
        MARGIN_L,
        Emu(6000000),
        Emu(5400000),
        Emu(400000),
        "1 tick = 1 day   /   10-year horizon   /   stop on collapse   /   live at jed08-parched.hf.space",
        size=11,
        color=ACCENT,
        bold=True,
        font_name=SANS,
    )

    # Right: screenshot
    img_path = FIG_DIR / "fig_simulation_screenshot.png"
    if img_path.exists():
        from PIL import Image
        with Image.open(img_path) as im:
            w_px, h_px = im.size
        max_w = Emu(6200000)
        max_h = Emu(4900000)
        aspect = w_px / h_px
        tw = int(max_w)
        th = int(tw / aspect)
        if th > int(max_h):
            th = int(max_h)
            tw = int(th * aspect)
        left = Emu(SLIDE_W - 700000 - tw)
        top = Emu(1700000 + (4900000 - th) // 2)
        s.shapes.add_picture(str(img_path), left, top, width=Emu(tw), height=Emu(th))

    set_speaker_notes(
        s,
        (
            "Quick architectural tour. We have four data centers with heterogeneous capacity "
            "that expand on a fixed nine-month schedule, regardless of basin state. Two farms "
            "with seasonal demand, one rainfed and one irrigated. One residential community "
            "that starts at one hundred thousand people and grows at a configurable annual "
            "rate, so its water need compounds over time just like a real city. A regulator "
            "that can issue caps but only sees the basin state with a stochastic delay. And "
            "we also model DC water restoration, where data centers return a fraction of "
            "their daily draw to the basin via funded recharge projects, modeling real-world "
            "water-positive pledges from operators like Microsoft and Google. One tick is one "
            "day, the model runs for ten years or until collapse. The single most important "
            "mechanism is the cooling-stress positive feedback loop, which produces the "
            "nonlinear cliff we will see in H2."
        ),
    )


def slide_7_parameters(prs):
    s = new_slide(prs)
    add_title(s, "Parameters and Scenarios")

    rows = [
        ("A", "Unregulated", "No cap, no oversight."),
        ("B", "Reactive cap", "Cap triggers at 30% basin storage."),
        ("C", "Proactive cap", "15 ML/day from t=0."),
        ("D", "Staggered entry", "DCs come online in years 0, 2, 4, 6."),
    ]

    top0 = 1900000
    row_h = 720000

    for i, (key, name, desc) in enumerate(rows):
        y = top0 + i * row_h
        # Letter in serif accent
        add_text_box(
            s,
            MARGIN_L,
            Emu(y),
            Emu(550000),
            Emu(550000),
            key,
            size=28,
            color=ACCENT,
            bold=True,
            font_name=SERIF,
        )
        # Scenario name
        add_text_box(
            s,
            Emu(int(MARGIN_L) + 800000),
            Emu(y + 60000),
            Emu(3000000),
            Emu(500000),
            name,
            size=20,
            color=INK,
            bold=True,
            font_name=SERIF,
        )
        # Description
        add_text_box(
            s,
            Emu(int(MARGIN_L) + 4000000),
            Emu(y + 90000),
            Emu(8000000),
            Emu(500000),
            desc,
            size=15,
            color=MUTED,
            font_name=SANS,
        )

    # Footnote
    add_text_box(
        s,
        MARGIN_L,
        Emu(5900000),
        CONTENT_W,
        Emu(900000),
        "Matched-seed design: every scenario sees the same 50 random seeds, so differences are policy, not luck.",
        size=14,
        color=ACCENT,
        italic=True,
        font_name=SERIF,
    )

    set_speaker_notes(
        s,
        (
            "Four scenarios. A is unregulated growth, the baseline where nothing stops the "
            "data centers from drawing. B is a reactive cap, meaning the regulator activates "
            "a withdrawal limit only after the basin drops to thirty percent of capacity. C "
            "is a proactive cap, fifteen megaliters per day from day one, applied from the "
            "moment the first data center comes online. And D is staggered entry, where the "
            "four data centers do not arrive simultaneously but spread out over six years. "
            "All four scenarios run on the same fifty random seeds, with the same weather "
            "realizations and the same demand shocks. That means when we compare A to B or "
            "C to D, the only thing varying is the policy rule. Differences in outcomes can "
            "be attributed cleanly to the rule, not to a lucky or unlucky draw."
        ),
    )


def slide_8_use_cases(prs):
    s = new_slide(prs)
    add_title(s, "How To Read The Simulation")

    img_path = FIG_DIR / "fig_basin_timeseries.png"
    if img_path.exists():
        from PIL import Image
        with Image.open(img_path) as im:
            w_px, h_px = im.size
        max_w = Emu(8200000)
        max_h = Emu(4600000)
        aspect = w_px / h_px
        tw = int(max_w)
        th = int(tw / aspect)
        if th > int(max_h):
            th = int(max_h)
            tw = int(th * aspect)
        left = Emu(700000)
        top = Emu(1750000)
        s.shapes.add_picture(str(img_path), left, top, width=Emu(tw), height=Emu(th))

    # Right column: callouts
    cx = Emu(9300000)
    cw = Emu(3500000)
    add_text_box(s, cx, Emu(1800000), cw, Emu(400000), "WHAT TO SEE",
                 size=11, color=ACCENT, bold=True, font_name=SANS)

    add_text_box(s, cx, Emu(2250000), cw, Emu(400000), "A and B",
                 size=17, color=INK, bold=True, font_name=SERIF)
    add_text_box(s, cx, Emu(2600000), cw, Emu(900000),
                 "Identical trajectory. Reactive cap fires after the cliff.",
                 size=12, color=MUTED, font_name=SANS)

    add_text_box(s, cx, Emu(3550000), cw, Emu(400000), "C",
                 size=17, color=INK, bold=True, font_name=SERIF)
    add_text_box(s, cx, Emu(3900000), cw, Emu(900000),
                 "Holds above 90% for the entire decade.",
                 size=12, color=MUTED, font_name=SANS)

    add_text_box(s, cx, Emu(4850000), cw, Emu(400000), "D",
                 size=17, color=INK, bold=True, font_name=SERIF)
    add_text_box(s, cx, Emu(5200000), cw, Emu(900000),
                 "Delays the collapse but the endpoint is unchanged.",
                 size=12, color=MUTED, font_name=SANS)

    set_speaker_notes(
        s,
        (
            "This is the single most useful figure for understanding what the model produces. "
            "Each line is the mean basin storage across fifty runs, with one line per "
            "scenario. Look at A and B. They trace exactly the same line for the first six "
            "years. By the time the reactive cap fires at thirty percent, the system has "
            "already crossed the point of no return. The cap activates but the cliff is "
            "underneath you. C, the proactive cap, stays north of ninety percent the entire "
            "ten years, which is what we want. D, the staggered entry scenario, looks "
            "promising in the early years but converges on the same collapse point as A in "
            "the long run. The lesson here is that delay is not safety, and reactive policy "
            "is structurally too late."
        ),
    )


def slide_9_h1(prs):
    s = new_slide(prs)
    add_title(s, "Result H1: Collapse Timing")

    img_path = FIG_DIR / "fig_time_to_stress.png"
    if img_path.exists():
        from PIL import Image
        with Image.open(img_path) as im:
            w_px, h_px = im.size
        max_w = Emu(7600000)
        max_h = Emu(4900000)
        aspect = w_px / h_px
        tw = int(max_w)
        th = int(tw / aspect)
        if th > int(max_h):
            th = int(max_h)
            tw = int(th * aspect)
        left = Emu(700000)
        top = Emu(1750000)
        s.shapes.add_picture(str(img_path), left, top, width=Emu(tw), height=Emu(th))

    # Right column: hero stat
    cx = Emu(8800000)
    cw = Emu(4100000)
    add_text_box(s, cx, Emu(1850000), cw, Emu(400000), "RESULT",
                 size=11, color=ACCENT, bold=True, font_name=SANS)
    add_text_box(s, cx, Emu(2250000), cw, Emu(1300000), "100%",
                 size=72, color=ACCENT, bold=True, font_name=SERIF)
    add_text_box(s, cx, Emu(3550000), cw, Emu(700000),
                 "of unregulated runs collapsed.",
                 size=16, color=INK, font_name=SERIF, italic=True)

    add_text_box(s, cx, Emu(4500000), cw, Emu(450000),
                 "Mean: 6.07 ± 0.84 years",
                 size=18, color=INK, bold=True, font_name=SANS)
    add_text_box(s, cx, Emu(5000000), cw, Emu(400000),
                 "p < 10⁻²¹",
                 size=14, color=MUTED, font_name=SANS)
    add_text_box(s, cx, Emu(5450000), cw, Emu(400000),
                 "n = 50 replicate runs",
                 size=11, color=MUTED, font_name=SANS)

    set_speaker_notes(
        s,
        (
            "H1, collapse timing. We ran fifty replicates of the unregulated scenario. Every "
            "single one of them crossed the critical-stress threshold within ten years. The "
            "mean time to collapse was six point zero seven years, with a standard deviation "
            "of zero point eight four years. The p-value against the null of no collapse "
            "within the predicted window is below ten to the minus twenty-one, which is to "
            "say, this is not a tail event, this is the mean behavior. The histogram on the "
            "left shows the distribution. Notice how tightly clustered it is. There is no "
            "lucky timeline. There is no run where the model just happens to dodge collapse. "
            "Under the unregulated scenario, collapse is not a risk, it is a prediction. "
            "That is the cleanest of the three results and it sets up everything that "
            "follows."
        ),
    )


def slide_10_h2(prs):
    s = new_slide(prs)
    add_title(s, "Result H2: Tipping Point")

    img_path = FIG_DIR / "fig_tipping_point.png"
    if img_path.exists():
        from PIL import Image
        with Image.open(img_path) as im:
            w_px, h_px = im.size
        max_w = Emu(7600000)
        max_h = Emu(4900000)
        aspect = w_px / h_px
        tw = int(max_w)
        th = int(tw / aspect)
        if th > int(max_h):
            th = int(max_h)
            tw = int(th * aspect)
        left = Emu(700000)
        top = Emu(1750000)
        s.shapes.add_picture(str(img_path), left, top, width=Emu(tw), height=Emu(th))

    cx = Emu(8800000)
    cw = Emu(4100000)
    add_text_box(s, cx, Emu(1850000), cw, Emu(400000), "ACCELERATION",
                 size=11, color=ACCENT, bold=True, font_name=SANS)
    add_text_box(s, cx, Emu(2250000), cw, Emu(1300000), "9.25×",
                 size=72, color=ACCENT, bold=True, font_name=SERIF)
    add_text_box(s, cx, Emu(3550000), cw, Emu(700000),
                 "decline rate after the 40% threshold.",
                 size=14, color=INK, font_name=SERIF, italic=True)

    add_text_box(s, cx, Emu(4400000), cw, Emu(400000),
                 "Pre-tipping: 0.07 / yr",
                 size=15, color=MUTED, font_name=SANS)
    add_text_box(s, cx, Emu(4850000), cw, Emu(400000),
                 "Post-tipping: 0.66 / yr",
                 size=15, color=INK, bold=True, font_name=SANS)
    add_text_box(s, cx, Emu(5450000), cw, Emu(400000),
                 "p < 10⁻⁷⁴",
                 size=14, color=MUTED, font_name=SANS)

    set_speaker_notes(
        s,
        (
            "This is the headline finding, and the one I want you to remember. H2 says the "
            "basin does not decline linearly. The drainage rate before the forty percent "
            "threshold is about zero point zero seven per year, basically a slow drift. "
            "After the basin crosses forty percent, the rate jumps to zero point six six per "
            "year. That is a nine point two five times acceleration, with a p-value below "
            "ten to the minus seventy-four across our replicates. The mechanism is "
            "straightforward and worth pausing on. When the basin is low, evaporative "
            "cooling becomes less efficient, because higher water temperatures and reduced "
            "tower performance mean each megawatt of compute requires more makeup water. The "
            "data centers draw more, which lowers the basin further, which makes cooling "
            "even less efficient. That is the positive feedback loop that gives you the "
            "cliff."
        ),
    )


def slide_11_h3(prs):
    s = new_slide(prs)
    add_title(s, "Result H3: Policy Effectiveness")

    img_path = FIG_DIR / "fig_yield_loss.png"
    if img_path.exists():
        from PIL import Image
        with Image.open(img_path) as im:
            w_px, h_px = im.size
        max_w = Emu(6800000)
        max_h = Emu(4900000)
        aspect = w_px / h_px
        tw = int(max_w)
        th = int(tw / aspect)
        if th > int(max_h):
            th = int(max_h)
            tw = int(th * aspect)
        left = Emu(700000)
        top = Emu(1750000)
        s.shapes.add_picture(str(img_path), left, top, width=Emu(tw), height=Emu(th))

    cx = Emu(8000000)
    cw = Emu(5000000)
    add_text_box(s, cx, Emu(1800000), cw, Emu(400000), "PROACTIVE CAP",
                 size=11, color=ACCENT, bold=True, font_name=SANS)
    add_text_box(s, cx, Emu(2200000), cw, Emu(1100000), "+65%",
                 size=60, color=ACCENT, bold=True, font_name=SERIF)
    add_text_box(s, cx, Emu(3200000), cw, Emu(400000),
                 "delay in critical stress onset.",
                 size=13, color=MUTED, font_name=SANS)

    add_text_box(s, cx, Emu(3900000), cw, Emu(400000), "REACTIVE CAP",
                 size=11, color=MUTED, bold=True, font_name=SANS)
    add_text_box(s, cx, Emu(4300000), cw, Emu(1100000), "+0%",
                 size=60, color=INK, bold=True, font_name=SERIF)
    add_text_box(s, cx, Emu(5300000), cw, Emu(400000),
                 "indistinguishable from no policy.",
                 size=13, color=MUTED, font_name=SANS)

    add_text_box(s, cx, Emu(5850000), cw, Emu(400000),
                 "p < 10⁻³⁵",
                 size=14, color=MUTED, font_name=SANS)

    set_speaker_notes(
        s,
        (
            "H3, policy effectiveness. We compared the four scenarios on time-to-critical-"
            "stress, on yield loss in agriculture, and on residual basin storage at year "
            "ten. The proactive cap, scenario C, delays the onset of critical stress by "
            "sixty-five percent relative to the unregulated baseline. The reactive cap, "
            "scenario B, delays it by exactly zero percent. Statistically and practically, "
            "B is indistinguishable from no policy at all. The reason is mechanical, not "
            "political. Triggering at thirty percent is well past the forty percent tipping "
            "point we identified in H2. By the time the cap activates, the positive-feedback "
            "regime is already running. The proactive policy works because it never lets the "
            "system enter the unstable regime in the first place. Set the cap before the "
            "data centers arrive, and you stay in the linear regime where regulation "
            "actually has leverage."
        ),
    )


def slide_12_discussion(prs):
    s = new_slide(prs)
    add_title(s, "Discussion: What The Model Says")

    bullets = [
        "Self-reporting is insufficient. Basin-level visibility is essential.",
        "Reactive policy at conventional thresholds is structurally equivalent to no policy.",
        "Staggered entry buys time, not safety. Long-run equilibrium is unchanged.",
        "A 9x acceleration means by the time politicians notice, it is already too late.",
    ]
    # Wider text column so bullets do not wrap mid-clause.
    text_w = Emu(6700000)
    add_bullets(
        s,
        MARGIN_L,
        Emu(1900000),
        text_w,
        Emu(4800000),
        bullets,
        size=14,
        line_spacing=1.5,
    )

    # Inset image on the right, shrunk to fit the narrower right column.
    img_path = FIG_DIR / "fig_scenario_compare.png"
    if img_path.exists():
        from PIL import Image
        with Image.open(img_path) as im:
            w_px, h_px = im.size
        right_col_left = Emu(int(MARGIN_L) + int(text_w) + 400000)
        right_col_width = Emu(SLIDE_W - int(right_col_left) - 700000)
        max_w = right_col_width
        max_h = Emu(4100000)
        aspect = w_px / h_px
        tw = int(max_w)
        th = int(tw / aspect)
        if th > int(max_h):
            th = int(max_h)
            tw = int(th * aspect)
        left = Emu(int(right_col_left) + (int(right_col_width) - tw) // 2)
        top = Emu(2000000)
        s.shapes.add_picture(str(img_path), left, top, width=Emu(tw), height=Emu(th))
        add_text_box(s, left, Emu(int(top) + th + 80000), Emu(tw), Emu(400000),
                     "Scenario comparison (A / B / C / D)",
                     size=10, color=MUTED, align=PP_ALIGN.CENTER, font_name=SANS)

    set_speaker_notes(
        s,
        (
            "Pulling back, four discussion points. First, self-reporting from individual "
            "operators cannot tell you what is happening to the basin. You need a shared, "
            "real-time view, basin-level visibility. Second, reactive policy calibrated to "
            "conventional thresholds, like thirty percent storage, is structurally "
            "equivalent to no policy. It just signs off on the collapse a little later. "
            "Third, staggered entry buys time but not safety. The long-run equilibrium is "
            "the same. Fourth, and this is the punchline, the nine-times acceleration we "
            "found in H2 means that by the time politicians and the press are paying "
            "attention, the system is already in the cliff. Real-world parallels are not "
            "hypothetical here, think Phoenix, The Dalles in Oregon, Santiago in Chile. "
            "Real basins also have climate drift and contamination, which our model does "
            "not capture, and those make the situation worse, not better."
        ),
    )


def slide_13_limitations(prs):
    s = new_slide(prs)
    add_title(s, "Limitations and Future Work")

    add_text_box(s, MARGIN_L, Emu(1800000), Emu(5900000), Emu(400000),
                 "LIMITATIONS", size=11, color=ACCENT, bold=True, font_name=SANS)
    add_bullets(
        s,
        MARGIN_L,
        Emu(2250000),
        Emu(5900000),
        Emu(4500000),
        [
            "Synthetic parameters (calibrated, not validated against a specific basin)",
            "No climate-change drift in recharge mean",
            "Single basin, no inter-basin trade",
            "Regulator has perfect observability after delay",
            "DC demand is exogenous (compute growth not price-responsive)",
            "Ag yield loss simplified: below threshold = dead",
        ],
        size=13,
        line_spacing=1.4,
    )

    add_text_box(s, Emu(7100000), Emu(1800000), Emu(5700000), Emu(400000),
                 "FUTURE WORK", size=11, color=ACCENT, bold=True, font_name=SANS)
    add_bullets(
        s,
        Emu(7100000),
        Emu(2250000),
        Emu(5700000),
        Emu(4500000),
        [
            "Inter-basin water trade",
            "Climate-change scenarios (drift in recharge mean)",
            "Real permit-process modeling (political delay curves)",
            "Inter-operator contestation and bidding",
            "Endogenous DC demand response (price / water cost)",
            "Calibrate to a real candidate basin (Pacific NW, Chile)",
        ],
        size=13,
        line_spacing=1.4,
    )

    set_speaker_notes(
        s,
        (
            "Limitations, briefly. Our parameters are synthetic, drawn from the literature "
            "and calibrated for internal consistency, but they are not validated against any "
            "single real basin. We do not model climate-change drift, which would make "
            "recharge less reliable over time. We treat the basin as a closed system with "
            "no inter-basin trade. The regulator, once it observes the basin, has perfect "
            "information. Demand is exogenous, meaning households and farms do not respond "
            "to prices. And our agricultural yield loss is binary in a way real crops are "
            "not. On the future-work side, the most interesting extensions are inter-basin "
            "trade, climate scenarios with drifting recharge, modeling the actual permit "
            "process with the political delays it implies, and a calibration exercise "
            "against a real candidate basin in the Pacific Northwest or in Latin America."
        ),
    )


def slide_14_conclusion(prs):
    s = new_slide(prs)
    add_title(s, "Conclusion and Q&A")

    add_text_box(s, MARGIN_L, Emu(1800000), CONTENT_W, Emu(400000),
                 "THREE TAKEAWAYS", size=11, color=ACCENT, bold=True, font_name=SANS)

    takeaways = [
        ("1", "Unregulated AI growth collapses shared basins on a 5 to 8 year timeline."),
        ("2", "The collapse is nonlinear. Late warnings will not help."),
        ("3", "Proactive caps work. Reactive caps do not."),
    ]
    top0 = 2300000
    for i, (num, text) in enumerate(takeaways):
        y = top0 + i * 800000
        # Number in serif accent
        add_text_box(
            s,
            MARGIN_L,
            Emu(y),
            Emu(550000),
            Emu(600000),
            num,
            size=32,
            color=ACCENT,
            bold=True,
            font_name=SERIF,
        )
        # Takeaway in serif
        add_text_box(
            s,
            Emu(int(MARGIN_L) + 700000),
            Emu(y + 70000),
            Emu(SLIDE_W - 2200000),
            Emu(600000),
            text,
            size=20,
            color=INK,
            bold=True,
            font_name=SERIF,
        )

    # Closing pull-quote in serif italic
    add_text_box(
        s,
        MARGIN_L,
        Emu(5050000),
        CONTENT_W,
        Emu(1000000),
        "\"If you want to keep the water on, you have to cap the draw before anyone asks you to.\"",
        size=20,
        color=ACCENT,
        italic=True,
        font_name=SERIF,
    )

    add_text_box(s, MARGIN_L, Emu(6200000), CONTENT_W, Emu(400000),
                 "Code and data: github.com/cup-noodlehS/ABM-project",
                 size=11, color=MUTED, font_name=SANS)
    add_text_box(s, MARGIN_L, Emu(6600000), CONTENT_W, Emu(400000),
                 "Thank you. Questions?",
                 size=16, color=INK, bold=True, font_name=SANS)

    set_speaker_notes(
        s,
        (
            "To wrap up, three takeaways. First, under our model, unregulated AI growth "
            "collapses shared basins on a five to eight year timeline, not as a tail event "
            "but as the mean behavior. Second, the collapse is nonlinear: a nine times "
            "acceleration in decline rate once the basin crosses forty percent storage. "
            "Late warnings do not help, because by the time the warning fires you are "
            "already on the cliff. Third, the policy implication is unambiguous in our "
            "results: proactive caps work, reactive caps do not. If you want to keep the "
            "water on, you have to cap the draw before anyone asks you to. Thank you all "
            "for your attention. The code, data, and full paper are on the public "
            "repository at github dot com slash cup-noodlehS slash ABM-project. We would "
            "love to take your questions."
        ),
    )


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------

def build():
    prs = Presentation()
    prs.slide_width = SLIDE_W
    prs.slide_height = SLIDE_H

    builders = [
        slide_1_title,
        slide_2_hook,
        slide_3_problem,
        slide_4_objectives,
        slide_5_hypotheses,
        slide_6_model_overview,
        slide_7_parameters,
        slide_8_use_cases,
        slide_9_h1,
        slide_10_h2,
        slide_11_h3,
        slide_12_discussion,
        slide_13_limitations,
        slide_14_conclusion,
    ]
    for fn in builders:
        fn(prs)

    total = len(prs.slides)
    for i, slide in enumerate(prs.slides, start=1):
        add_footer(slide, i, total)

    prs.save(OUT_PATH)
    return OUT_PATH, total


def em_dash_sweep(path: Path) -> int:
    """Open the pptx and count any remaining em-dashes in text frames."""
    p = Presentation(str(path))
    count = 0
    for slide in p.slides:
        for shape in slide.shapes:
            if shape.has_text_frame:
                for para in shape.text_frame.paragraphs:
                    for run in para.runs:
                        if "—" in run.text:
                            count += run.text.count("—")
                            run.text = run.text.replace("—", ", ")
        if slide.has_notes_slide:
            notes_tf = slide.notes_slide.notes_text_frame
            for para in notes_tf.paragraphs:
                for run in para.runs:
                    if "—" in run.text:
                        count += run.text.count("—")
                        run.text = run.text.replace("—", ", ")
    if count:
        p.save(str(path))
    return count


def speaker_note_word_count(path: Path) -> int:
    p = Presentation(str(path))
    total = 0
    for slide in p.slides:
        if slide.has_notes_slide:
            text = slide.notes_slide.notes_text_frame.text
            total += len(text.split())
    return total


if __name__ == "__main__":
    out, n_slides = build()
    em = em_dash_sweep(out)
    notes_words = speaker_note_word_count(out)
    print(f"WROTE: {out}")
    print(f"SLIDES: {n_slides}")
    print(f"EM-DASHES SWEPT: {em}")
    print(f"SPEAKER NOTE WORD COUNT: {notes_words}")
