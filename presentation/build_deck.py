"""Build PARCHED_final.pptx - dark-theme 16:9 deck for CMSC 176 final project.

Run from the release/presentation/ directory with the release/model/.venv activated.
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

# Theme colors
NAVY = RGBColor(0x0B, 0x14, 0x26)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
TEAL = RGBColor(0x3E, 0xE6, 0xC5)
AMBER = RGBColor(0xE6, 0xA5, 0x32)
RED = RGBColor(0xD9, 0x51, 0x4E)
BLUE = RGBColor(0x6F, 0x9C, 0xEB)
MUTED = RGBColor(0xB6, 0xC2, 0xD9)

FONT = "Calibri"

# Slide dimensions (16:9)
SLIDE_W = 13333333
SLIDE_H = 7500000

# Margins
MARGIN_L = Emu(700000)
MARGIN_T = Emu(500000)
CONTENT_W = Emu(SLIDE_W - 1400000)


def set_background(slide, color: RGBColor) -> None:
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = color


def add_accent_bar(slide) -> None:
    """Thin teal accent bar on the left edge."""
    bar = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Emu(0), Emu(0), Emu(110000), Emu(SLIDE_H)
    )
    bar.line.fill.background()
    bar.fill.solid()
    bar.fill.fore_color.rgb = TEAL


def add_text_box(
    slide,
    left,
    top,
    width,
    height,
    text: str,
    *,
    size: int = 20,
    color: RGBColor = WHITE,
    bold: bool = False,
    align=PP_ALIGN.LEFT,
    anchor=MSO_ANCHOR.TOP,
    font_name: str = FONT,
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
        run.font.color.rgb = color
    return tb


def add_title(slide, text: str, *, color: RGBColor = WHITE, size: int = 36) -> None:
    add_text_box(
        slide,
        MARGIN_L,
        MARGIN_T,
        CONTENT_W,
        Emu(800000),
        text,
        size=size,
        color=color,
        bold=True,
    )


def add_bullets(
    slide,
    left,
    top,
    width,
    height,
    bullets,
    *,
    size: int = 20,
    color: RGBColor = WHITE,
    bullet_color: RGBColor = TEAL,
    line_spacing: float = 1.25,
):
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
        # bullet marker
        marker = p.add_run()
        marker.text = "▸  "  # right-pointing triangle
        marker.font.name = FONT
        marker.font.size = Pt(size)
        marker.font.bold = True
        marker.font.color.rgb = bullet_color
        # bullet text
        run = p.add_run()
        run.text = item
        run.font.name = FONT
        run.font.size = Pt(size)
        run.font.color.rgb = color
    return tb


def add_footer(slide, slide_no: int, total: int) -> None:
    add_text_box(
        slide,
        Emu(SLIDE_W - 2200000),
        Emu(SLIDE_H - 450000),
        Emu(1800000),
        Emu(350000),
        f"PARCHED   |   {slide_no} / {total}",
        size=10,
        color=MUTED,
        align=PP_ALIGN.RIGHT,
    )


def set_speaker_notes(slide, text: str) -> None:
    notes = slide.notes_slide.notes_text_frame
    notes.text = text


def new_slide(prs: Presentation):
    blank = prs.slide_layouts[6]  # blank
    slide = prs.slides.add_slide(blank)
    set_background(slide, NAVY)
    add_accent_bar(slide)
    return slide


def add_image_centered(slide, image_path: Path, top_emu: int, max_w_emu: int, max_h_emu: int):
    """Add an image scaled to fit within max_w x max_h, centered horizontally."""
    from PIL import Image  # bundled with python-pptx via Pillow

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
    # Decorative subtitle band
    add_text_box(
        s,
        MARGIN_L,
        Emu(1600000),
        CONTENT_W,
        Emu(300000),
        "CMSC 176, FINAL PROJECT",
        size=14,
        color=TEAL,
        bold=True,
    )
    add_text_box(
        s,
        MARGIN_L,
        Emu(2000000),
        CONTENT_W,
        Emu(1400000),
        "PARCHED: When AI Drinks Your Town Dry",
        size=54,
        color=WHITE,
        bold=True,
    )
    add_text_box(
        s,
        MARGIN_L,
        Emu(3500000),
        CONTENT_W,
        Emu(700000),
        "An Agent-Based Model of Hyperscaler Water Competition",
        size=24,
        color=MUTED,
    )
    # Divider
    div = s.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, MARGIN_L, Emu(4400000), Emu(1200000), Emu(40000)
    )
    div.line.fill.background()
    div.fill.solid()
    div.fill.fore_color.rgb = TEAL

    add_text_box(
        s,
        MARGIN_L,
        Emu(4650000),
        CONTENT_W,
        Emu(500000),
        "Sheldon Arthur Sagrado  ·  Jed Edison Donaire",
        size=20,
        color=WHITE,
        bold=True,
    )
    add_text_box(
        s,
        MARGIN_L,
        Emu(5200000),
        CONTENT_W,
        Emu(400000),
        "CMSC 176, AY 2025-2026, University of the Philippines Cebu",
        size=16,
        color=MUTED,
    )
    add_text_box(
        s,
        MARGIN_L,
        Emu(5650000),
        CONTENT_W,
        Emu(400000),
        "May 2026",
        size=16,
        color=MUTED,
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
    add_text_box(
        s,
        MARGIN_L,
        Emu(2000000),
        CONTENT_W,
        Emu(1800000),
        "3 to 5 million liters",
        size=88,
        color=TEAL,
        bold=True,
    )
    add_text_box(
        s,
        MARGIN_L,
        Emu(3700000),
        CONTENT_W,
        Emu(500000),
        "per day, per hyperscale data center",
        size=24,
        color=WHITE,
    )

    add_text_box(
        s,
        MARGIN_L,
        Emu(4850000),
        CONTENT_W,
        Emu(900000),
        "And nobody is modeling the basin-level collisions.",
        size=28,
        color=AMBER,
        bold=True,
    )
    add_text_box(
        s,
        MARGIN_L,
        Emu(5800000),
        CONTENT_W,
        Emu(900000),
        "Source: Li et al. (2023), \"Making AI Less Thirsty\"",
        size=14,
        color=MUTED,
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
        Emu(1500000),
        Emu(5800000),
        Emu(400000),
        "THE SETUP",
        size=14,
        color=TEAL,
        bold=True,
    )
    add_bullets(
        s,
        MARGIN_L,
        Emu(1950000),
        Emu(5800000),
        Emu(3800000),
        [
            "One shared freshwater basin (30 BL capacity)",
            "Multiple data centers competing for cooling water",
            "Residential demand (~100k people)",
            "Agriculture (rainfed and irrigated fields)",
            "A regulator with delayed observability",
        ],
        size=20,
    )

    # Right column: question
    add_text_box(
        s,
        Emu(7000000),
        Emu(1500000),
        Emu(5800000),
        Emu(400000),
        "THE QUESTION",
        size=14,
        color=AMBER,
        bold=True,
    )
    add_text_box(
        s,
        Emu(7000000),
        Emu(1950000),
        Emu(5800000),
        Emu(2500000),
        "What happens when self-interested data centers, blind to each other, share a finite basin?",
        size=26,
        color=WHITE,
        bold=True,
    )
    add_text_box(
        s,
        Emu(7000000),
        Emu(4700000),
        Emu(5800000),
        Emu(1500000),
        "No coordination. No shared meter. No price signal until things break.",
        size=18,
        color=MUTED,
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
        Emu(2000000),
        CONTENT_W,
        Emu(4000000),
        bullets,
        size=26,
        line_spacing=1.6,
    )
    # Tag line
    add_text_box(
        s,
        MARGIN_L,
        Emu(6000000),
        CONTENT_W,
        Emu(500000),
        "Same seeds, same shocks, different rules.",
        size=18,
        color=TEAL,
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

    col_w = Emu(4000000)
    gap = Emu(200000)
    left0 = MARGIN_L
    left1 = Emu(left0 + col_w + gap)
    left2 = Emu(left1 + col_w + gap)
    top = Emu(1700000)
    h = Emu(4400000)

    def hyp_card(left, label, color, headline, detail):
        card = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, col_w, h)
        card.line.color.rgb = color
        card.line.width = Pt(1.5)
        card.fill.solid()
        card.fill.fore_color.rgb = RGBColor(0x12, 0x1F, 0x36)
        # Label
        add_text_box(
            s,
            Emu(left + 250000),
            Emu(top + 200000),
            Emu(col_w - 500000),
            Emu(500000),
            label,
            size=16,
            color=color,
            bold=True,
        )
        add_text_box(
            s,
            Emu(left + 250000),
            Emu(top + 750000),
            Emu(col_w - 500000),
            Emu(1500000),
            headline,
            size=22,
            color=WHITE,
            bold=True,
        )
        add_text_box(
            s,
            Emu(left + 250000),
            Emu(top + 2400000),
            Emu(col_w - 500000),
            Emu(1800000),
            detail,
            size=15,
            color=MUTED,
        )

    hyp_card(
        left0,
        "H1   COLLAPSE",
        RED,
        "Unregulated growth collapses the basin in 5 to 8 years.",
        "Critical-stress crossing under no policy, across 50 replicate runs.",
    )
    hyp_card(
        left1,
        "H2   TIPPING POINT",
        AMBER,
        "Decline becomes nonlinear once basin storage drops below 40%.",
        "Cooling-stress positive feedback amplifies withdrawals as headroom shrinks.",
    )
    hyp_card(
        left2,
        "H3   POLICY",
        TEAL,
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
        Emu(1600000),
        Emu(5600000),
        Emu(4500000),
        [
            "4 data centers (heterogeneous capacity)",
            "2 farms (rainfed + irrigated)",
            "100k residents (consumption from demand curve)",
            "1 regulator (delayed observability)",
            "30 BL shared basin, with stochastic recharge",
            "All interactions mediated through the basin",
        ],
        size=18,
    )
    add_text_box(
        s,
        MARGIN_L,
        Emu(6100000),
        Emu(5600000),
        Emu(400000),
        "1 tick = 1 day   ·   10-year horizon   ·   stop on collapse",
        size=14,
        color=TEAL,
        bold=True,
    )

    # Right: screenshot
    img_path = FIG_DIR / "fig_simulation_screenshot.png"
    if img_path.exists():
        from PIL import Image
        with Image.open(img_path) as im:
            w_px, h_px = im.size
        max_w = Emu(6300000)
        max_h = Emu(5000000)
        aspect = w_px / h_px
        tw = int(max_w)
        th = int(tw / aspect)
        if th > int(max_h):
            th = int(max_h)
            tw = int(th * aspect)
        left = Emu(SLIDE_W - 700000 - tw)
        top = Emu(1500000 + (5000000 - th) // 2)
        s.shapes.add_picture(str(img_path), left, top, width=Emu(tw), height=Emu(th))

    set_speaker_notes(
        s,
        (
            "Quick architectural tour. We have four data centers with heterogeneous capacity, "
            "so they do not all draw the same. Two farms, one rainfed and one irrigated, "
            "which gives us a non-DC consumer with very different demand seasonality. One "
            "hundred thousand residents, whose draw follows a temperature-modulated demand "
            "curve. A regulator that can issue caps but only sees the basin state with a "
            "configurable delay. And the basin itself, thirty billion liters of usable "
            "capacity with stochastic recharge from rainfall. One tick is one day, the model "
            "runs for ten years or until collapse, whichever comes first. The single most "
            "important mechanism is the cooling-stress positive feedback loop, which is what "
            "produces the nonlinear regime, and we will see it light up in the H2 result."
        ),
    )


def slide_7_parameters(prs):
    s = new_slide(prs)
    add_title(s, "Parameters and Scenarios")

    # Table-like rows
    rows = [
        ("A", "Unregulated", "No cap, no oversight", RED),
        ("B", "Reactive cap", "Cap triggers at 30% basin storage", AMBER),
        ("C", "Proactive cap", "15 ML/day from t=0", TEAL),
        ("D", "Staggered entry", "DCs come online in years 0, 2, 4, 6", BLUE),
    ]

    top = 1700000
    row_h = 700000
    left_label = MARGIN_L
    left_name = Emu(left_label + 800000)
    left_desc = Emu(left_label + 3400000)

    # Header strip
    hdr = s.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, left_label, Emu(top - 100000), Emu(SLIDE_W - 1400000), Emu(50000)
    )
    hdr.line.fill.background()
    hdr.fill.solid()
    hdr.fill.fore_color.rgb = TEAL

    for i, (key, name, desc, col) in enumerate(rows):
        y = top + 200000 + i * row_h
        # Key chip
        chip = s.shapes.add_shape(
            MSO_SHAPE.OVAL, left_label, Emu(y), Emu(550000), Emu(550000)
        )
        chip.line.fill.background()
        chip.fill.solid()
        chip.fill.fore_color.rgb = col
        # chip text
        ctf = chip.text_frame
        ctf.margin_left = Emu(0)
        ctf.margin_right = Emu(0)
        ctf.margin_top = Emu(0)
        ctf.margin_bottom = Emu(0)
        ctf.vertical_anchor = MSO_ANCHOR.MIDDLE
        cp = ctf.paragraphs[0]
        cp.alignment = PP_ALIGN.CENTER
        cr = cp.add_run()
        cr.text = key
        cr.font.name = FONT
        cr.font.size = Pt(22)
        cr.font.bold = True
        cr.font.color.rgb = NAVY

        add_text_box(
            s, left_name, Emu(y + 50000), Emu(2400000), Emu(500000),
            name, size=22, color=WHITE, bold=True,
        )
        add_text_box(
            s, left_desc, Emu(y + 70000), Emu(8000000), Emu(500000),
            desc, size=18, color=MUTED,
        )

    # Footnote
    add_text_box(
        s,
        MARGIN_L,
        Emu(5700000),
        CONTENT_W,
        Emu(900000),
        "Matched-seed design: every scenario sees the same 50 random seeds, so differences are policy, not luck.",
        size=16,
        color=TEAL,
        bold=True,
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
        max_w = Emu(8500000)
        max_h = Emu(4800000)
        aspect = w_px / h_px
        tw = int(max_w)
        th = int(tw / aspect)
        if th > int(max_h):
            th = int(max_h)
            tw = int(th * aspect)
        left = Emu(700000)
        top = Emu(1500000)
        s.shapes.add_picture(str(img_path), left, top, width=Emu(tw), height=Emu(th))

    # Right column: callouts
    cx = Emu(9500000)
    cw = Emu(3500000)
    add_text_box(s, cx, Emu(1600000), cw, Emu(400000), "WHAT TO SEE", size=14, color=TEAL, bold=True)

    add_text_box(s, cx, Emu(2050000), cw, Emu(400000), "A and B", size=18, color=RED, bold=True)
    add_text_box(s, cx, Emu(2400000), cw, Emu(900000),
                 "Identical trajectory. Reactive cap fires after the cliff.",
                 size=14, color=MUTED)

    add_text_box(s, cx, Emu(3450000), cw, Emu(400000), "C", size=18, color=TEAL, bold=True)
    add_text_box(s, cx, Emu(3800000), cw, Emu(900000),
                 "Holds above 90% for the entire decade.",
                 size=14, color=MUTED)

    add_text_box(s, cx, Emu(4800000), cw, Emu(400000), "D", size=18, color=BLUE, bold=True)
    add_text_box(s, cx, Emu(5150000), cw, Emu(900000),
                 "Delays the collapse but the endpoint is unchanged.",
                 size=14, color=MUTED)

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
        max_w = Emu(7800000)
        max_h = Emu(5200000)
        aspect = w_px / h_px
        tw = int(max_w)
        th = int(tw / aspect)
        if th > int(max_h):
            th = int(max_h)
            tw = int(th * aspect)
        left = Emu(700000)
        top = Emu(1500000)
        s.shapes.add_picture(str(img_path), left, top, width=Emu(tw), height=Emu(th))

    # Right side big stat
    cx = Emu(9000000)
    cw = Emu(4000000)
    add_text_box(s, cx, Emu(1700000), cw, Emu(400000), "RESULT", size=14, color=TEAL, bold=True)
    add_text_box(s, cx, Emu(2100000), cw, Emu(1200000), "100%", size=80, color=RED, bold=True)
    add_text_box(s, cx, Emu(3400000), cw, Emu(700000),
                 "of unregulated runs collapsed", size=18, color=WHITE)

    add_text_box(s, cx, Emu(4350000), cw, Emu(600000),
                 "Mean: 6.07 ± 0.84 years", size=22, color=WHITE, bold=True)
    add_text_box(s, cx, Emu(5000000), cw, Emu(500000),
                 "p < 10⁻²¹", size=20, color=TEAL, bold=True)
    add_text_box(s, cx, Emu(5550000), cw, Emu(500000),
                 "n = 50 replicate runs", size=14, color=MUTED)

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
        max_w = Emu(7800000)
        max_h = Emu(5200000)
        aspect = w_px / h_px
        tw = int(max_w)
        th = int(tw / aspect)
        if th > int(max_h):
            th = int(max_h)
            tw = int(th * aspect)
        left = Emu(700000)
        top = Emu(1500000)
        s.shapes.add_picture(str(img_path), left, top, width=Emu(tw), height=Emu(th))

    cx = Emu(9000000)
    cw = Emu(4000000)
    add_text_box(s, cx, Emu(1700000), cw, Emu(400000), "ACCELERATION", size=14, color=AMBER, bold=True)
    add_text_box(s, cx, Emu(2100000), cw, Emu(1200000), "9.25×", size=80, color=AMBER, bold=True)
    add_text_box(s, cx, Emu(3400000), cw, Emu(700000),
                 "decline rate after 40% threshold", size=16, color=WHITE)

    add_text_box(s, cx, Emu(4250000), cw, Emu(400000),
                 "Pre-tipping: 0.07 / yr", size=18, color=MUTED)
    add_text_box(s, cx, Emu(4700000), cw, Emu(400000),
                 "Post-tipping: 0.66 / yr", size=18, color=WHITE, bold=True)
    add_text_box(s, cx, Emu(5300000), cw, Emu(500000),
                 "p < 10⁻⁷⁴", size=20, color=TEAL, bold=True)

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
        max_w = Emu(7000000)
        max_h = Emu(5200000)
        aspect = w_px / h_px
        tw = int(max_w)
        th = int(tw / aspect)
        if th > int(max_h):
            th = int(max_h)
            tw = int(th * aspect)
        left = Emu(700000)
        top = Emu(1500000)
        s.shapes.add_picture(str(img_path), left, top, width=Emu(tw), height=Emu(th))

    cx = Emu(8200000)
    cw = Emu(4800000)
    add_text_box(s, cx, Emu(1600000), cw, Emu(400000), "PROACTIVE CAP", size=14, color=TEAL, bold=True)
    add_text_box(s, cx, Emu(2000000), cw, Emu(900000), "+65%", size=64, color=TEAL, bold=True)
    add_text_box(s, cx, Emu(3000000), cw, Emu(400000),
                 "delay in critical stress onset", size=15, color=MUTED)

    add_text_box(s, cx, Emu(3700000), cw, Emu(400000), "REACTIVE CAP", size=14, color=RED, bold=True)
    add_text_box(s, cx, Emu(4100000), cw, Emu(900000), "+0%", size=64, color=RED, bold=True)
    add_text_box(s, cx, Emu(5100000), cw, Emu(400000),
                 "indistinguishable from no policy", size=15, color=MUTED)

    add_text_box(s, cx, Emu(5700000), cw, Emu(500000),
                 "p < 10⁻³⁵", size=18, color=TEAL, bold=True)

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
        "Self-reporting is insufficient; basin-level visibility is essential",
        "Reactive policy at conventional thresholds is structurally equivalent to no policy",
        "Staggered entry buys time, not safety; long-run equilibrium is unchanged",
        "A 9x acceleration means by the time politicians notice, it is already too late",
    ]
    # Bullets get the left half; image gets the right half. Clean gap between.
    text_w = Emu(6500000)
    add_bullets(
        s,
        MARGIN_L,
        Emu(1700000),
        text_w,
        Emu(5000000),
        bullets,
        size=18,
        line_spacing=1.5,
    )

    # Inset: scenario comparison figure on the right half
    img_path = FIG_DIR / "fig_scenario_compare.png"
    if img_path.exists():
        from PIL import Image
        with Image.open(img_path) as im:
            w_px, h_px = im.size
        # Right column starts after text column + 500000 gap
        right_col_left = Emu(MARGIN_L + text_w + Emu(500000))
        right_col_width = Emu(SLIDE_W - int(right_col_left) - 600000)
        max_w = right_col_width
        max_h = Emu(4200000)
        aspect = w_px / h_px
        tw = int(max_w)
        th = int(tw / aspect)
        if th > int(max_h):
            th = int(max_h)
            tw = int(th * aspect)
        # Center horizontally in the right column
        left = Emu(int(right_col_left) + (int(right_col_width) - tw) // 2)
        top = Emu(1700000)
        s.shapes.add_picture(str(img_path), left, top, width=Emu(tw), height=Emu(th))
        add_text_box(s, left, Emu(top + th + 50000), Emu(tw), Emu(400000),
                     "Scenario comparison (A/B/C/D)",
                     size=12, color=MUTED, align=PP_ALIGN.CENTER)

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

    # Two columns
    add_text_box(s, MARGIN_L, Emu(1600000), Emu(6000000), Emu(400000),
                 "LIMITATIONS", size=14, color=AMBER, bold=True)
    add_bullets(
        s,
        MARGIN_L,
        Emu(2050000),
        Emu(6000000),
        Emu(4500000),
        [
            "Synthetic parameters (calibrated, not validated against a specific basin)",
            "No climate-change drift",
            "Single basin, no inter-basin trade",
            "Regulator has perfect observability after delay",
            "Demand is exogenous",
            "Ag yield loss simplified: below threshold = dead",
        ],
        size=16,
        bullet_color=AMBER,
        line_spacing=1.3,
    )

    add_text_box(s, Emu(7100000), Emu(1600000), Emu(5700000), Emu(400000),
                 "FUTURE WORK", size=14, color=TEAL, bold=True)
    add_bullets(
        s,
        Emu(7100000),
        Emu(2050000),
        Emu(5700000),
        Emu(4500000),
        [
            "Inter-basin water trade",
            "Climate-change scenarios (drift in recharge)",
            "Real permit-process modeling",
            "Inter-operator contestation and bidding",
            "Endogenous demand response (price elasticity)",
            "Calibrate to a real candidate basin",
        ],
        size=16,
        bullet_color=TEAL,
        line_spacing=1.3,
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

    add_text_box(s, MARGIN_L, Emu(1600000), CONTENT_W, Emu(400000),
                 "THREE TAKEAWAYS", size=14, color=TEAL, bold=True)

    takeaways = [
        ("1", "Unregulated AI growth collapses shared basins on a 5 to 8 year timeline.", RED),
        ("2", "The collapse is nonlinear. Late warnings will not help.", AMBER),
        ("3", "Proactive caps work. Reactive caps do not.", TEAL),
    ]
    top0 = 2100000
    for i, (num, text, col) in enumerate(takeaways):
        y = top0 + i * 800000
        # Number chip
        chip = s.shapes.add_shape(MSO_SHAPE.OVAL, MARGIN_L, Emu(y), Emu(520000), Emu(520000))
        chip.line.fill.background()
        chip.fill.solid()
        chip.fill.fore_color.rgb = col
        ctf = chip.text_frame
        ctf.vertical_anchor = MSO_ANCHOR.MIDDLE
        cp = ctf.paragraphs[0]
        cp.alignment = PP_ALIGN.CENTER
        cr = cp.add_run()
        cr.text = num
        cr.font.name = FONT
        cr.font.size = Pt(22)
        cr.font.bold = True
        cr.font.color.rgb = NAVY

        add_text_box(s, Emu(MARGIN_L + 750000), Emu(y + 60000),
                     Emu(SLIDE_W - 2200000), Emu(600000), text,
                     size=22, color=WHITE, bold=True)

    # Big closing line
    add_text_box(
        s,
        MARGIN_L,
        Emu(5000000),
        CONTENT_W,
        Emu(1100000),
        "\"If you want to keep the water on, you have to cap the draw before anyone asks you to.\"",
        size=24,
        color=TEAL,
        bold=True,
    )

    add_text_box(s, MARGIN_L, Emu(6300000), CONTENT_W, Emu(400000),
                 "Code and data: github.com/cup-noodlehS/ABM-project",
                 size=14, color=MUTED)
    add_text_box(s, MARGIN_L, Emu(6700000), CONTENT_W, Emu(400000),
                 "Thank you. Questions?",
                 size=18, color=WHITE, bold=True)

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

    # Footers (added after so we know the total)
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
