"""
PARCHED – Single-page, non-scrollable interactive dashboard.

Run with:
    solara run app.py --port 8765
"""

from __future__ import annotations
import threading, time
import mesa, solara
import matplotlib
matplotlib.use("agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

from parched_model import ParchedModel, SimConfig

# ── Palette ──────────────────────────────────────────────────────────────────
BG      = "#0d1117"
SURFACE = "#161b22"
SURFACE2 = "#1c2128"
BORDER  = "#30363d"
TEXT    = "#e6edf3"
MUTED   = "#7d8590"
BLUE    = "#1f6feb"

def _status_color(pct: float) -> str:
    if pct > 60: return "#238636"
    if pct > 40: return "#9e6a03"
    if pct > 20: return "#bd561d"
    return "#da3633"

# ── Scenario registry ─────────────────────────────────────────────────────────
SCENARIOS = [
    "A \u2014 Unregulated",
    "B \u2014 Reactive",
    "C \u2014 Proactive",
    "D \u2014 Staggered",
]
_POLICY_MAP = {"A": "off", "B": "reactive", "C": "proactive", "D": "staggered"}

def _make_model(scenario: str, seed: int, num_dcs: int, basin_pct: int,
                alpha: float, recharge: float, budget: float,
                restore: int, pop_growth: float) -> ParchedModel:
    key    = scenario[0]
    policy = _POLICY_MAP.get(key, "off")
    cfg    = SimConfig(
        seed=int(seed),
        policy_mode=policy,
        num_data_centers=int(num_dcs),
        basin_initial_frac=basin_pct / 100.0,
        cooling_stress_amplification=float(alpha),
        recharge_mean_ml_per_day=float(recharge),
        proactive_industrial_budget_ml=float(budget),
        dc_restoration_frac=restore / 100.0,
        population_growth_rate_pct=float(pop_growth),
        label="viz_" + key,
    )
    if policy == "staggered":
        cfg.staggered_entry_ticks = tuple(i * 730 for i in range(cfg.num_data_centers))
    return ParchedModel(cfg)

# ── Global reactive state ─────────────────────────────────────────────────────
_scenario  = solara.reactive("A \u2014 Unregulated")
_seed      = solara.reactive(42)
_num_dcs   = solara.reactive(4)
_basin_pct = solara.reactive(80)
_alpha     = solara.reactive(4.0)
_recharge  = solara.reactive(50.0)
_budget    = solara.reactive(15.0)
_restore   = solara.reactive(0)
_pop_growth = solara.reactive(1.0)

_tick      = solara.reactive(0)       # incremented each step → triggers chart re-renders
_playing   = solara.reactive(False)
_version   = solara.reactive(0)       # bumped on reset to invalidate stale play loops
_speed     = solara.reactive(1)       # 1×–20× playback multiplier
_model     = solara.reactive(
    _make_model("A \u2014 Unregulated", 42, 4, 80, 4.0, 50.0, 15.0, 0, 1.0)
)

# ── Simulation controls ───────────────────────────────────────────────────────
def _do_step() -> None:
    m = _model.value
    if m is None:
        return
    m.step()
    _tick.value += 1


def _play_loop(version: int) -> None:
    while _playing.value and _version.value == version:
        speed = _speed.value
        m = _model.value
        if m is None:
            break
        # Run `speed` model ticks in one burst, then trigger a single redraw.
        # This is what actually makes high speeds feel fast — fewer renders,
        # more simulation steps per render.
        steps_taken = 0
        for _ in range(speed):
            if not _playing.value or _version.value != version:
                break
            m.step()
            steps_taken += 1
        if steps_taken:
            _tick.value += steps_taken   # one UI redraw for all steps
        time.sleep(0.08)                 # ~12 renders/sec regardless of speed
    _playing.value = False


def _toggle_play() -> None:
    if _playing.value:
        _playing.value = False
    else:
        _playing.value = True
        v = _version.value
        threading.Thread(target=_play_loop, args=(v,), daemon=True).start()


def _do_reset(scenario: str, seed: int, num_dcs: int, basin_pct: int,
              alpha: float, recharge: float, budget: float,
              restore: int, pop_growth: float) -> None:
    _playing.value = False
    _version.value += 1
    _scenario.value  = scenario
    _seed.value      = seed
    _num_dcs.value   = num_dcs
    _basin_pct.value = basin_pct
    _alpha.value     = alpha
    _recharge.value  = recharge
    _budget.value    = budget
    _restore.value   = restore
    _pop_growth.value = pop_growth
    _model.value = _make_model(scenario, seed, num_dcs, basin_pct, alpha, recharge, budget, restore, pop_growth)
    _tick.value  = 0

# ── Chart helpers ─────────────────────────────────────────────────────────────
def _fig(w: float, h: float, ncols: int = 1) -> tuple:
    fig, axes = plt.subplots(1, ncols, figsize=(w, h))
    fig.patch.set_facecolor(SURFACE2)
    axlist = axes if ncols > 1 else [axes]
    for ax in axlist:
        ax.set_facecolor(BG)
        ax.tick_params(colors=MUTED, labelsize=7)
        for sp in ax.spines.values():
            sp.set_color(BORDER)
    return fig, axes

def _render(fig) -> None:
    solara.FigureMatplotlib(fig)
    plt.close(fig)

# ── Chart components ──────────────────────────────────────────────────────────

@solara.component
def _Placeholder(msg: str = "Press \u25b6 to run"):
    with solara.Column(style={
        "align-items":      "center",
        "justify-content":  "center",
        "height":           "100%",
        "gap":              "6px",
        "background":       SURFACE2,
        "width":            "100%",
    }):
        solara.Text("📊", style={"font-size": "28px"})
        solara.Text(msg, style={"color": MUTED, "font-size": "12px"})


@solara.component
def BasinTimeseries():
    _ = _tick.value
    m = _model.value
    if not m or not m.history:
        _Placeholder(); return

    h     = list(m.history)
    years = [x["tick"] / 365 for x in h]
    bpct  = [x["basin_frac"] * 100 for x in h]
    s, c  = m.cfg.stress_frac * 100, m.cfg.critical_frac * 100

    fig, ax = _fig(5.0, 2.65)
    ax.axhspan(0, c, color="#da3633", alpha=0.10)
    ax.axhspan(c, s, color="#bd561d", alpha=0.07)
    ax.plot(years, bpct, color="#58a6ff", lw=1.8)
    ax.axhline(s, color="#e3b341", lw=1.0, ls="--", alpha=0.7, label=f"Stress {s:.0f}%")
    ax.axhline(c, color="#da3633", lw=1.0, ls="--", alpha=0.7, label=f"Critical {c:.0f}%")
    ax.set_xlim(0, max(years[-1], 0.1)); ax.set_ylim(0, 105)
    ax.set_xlabel("Year", color=MUTED, fontsize=7)
    ax.set_ylabel("Basin %", color=MUTED, fontsize=7)
    ax.set_title("Basin Level", color=TEXT, fontsize=9, fontweight="bold", pad=4)
    ax.legend(fontsize=6, facecolor=SURFACE, edgecolor=BORDER, labelcolor=TEXT, loc="upper right")
    fig.tight_layout(pad=0.5)
    _render(fig)


@solara.component
def WaterAlloc():
    _ = _tick.value
    m = _model.value
    if not m or not m.history:
        _Placeholder(); return

    h     = list(m.history)
    years = [x["tick"] / 365 for x in h]
    fig, ax = _fig(5.0, 2.65)
    ax.stackplot(
        years,
        [x["community_received_ml"]  for x in h],
        [x["dc_total_draw_ml"]       for x in h],
        [x["farm_total_received_ml"] for x in h],
        labels=["Community", "Data Centers", "Farms"],
        colors=["#58a6ff", "#f85149", "#3fb950"],
        alpha=0.82,
    )
    ax.set_xlim(0, max(years[-1], 0.1))
    ax.set_xlabel("Year", color=MUTED, fontsize=7)
    ax.set_ylabel("ML / day", color=MUTED, fontsize=7)
    ax.set_title("Water Allocation", color=TEXT, fontsize=9, fontweight="bold", pad=4)
    ax.legend(fontsize=6, facecolor=SURFACE, edgecolor=BORDER, labelcolor=TEXT,
              loc="upper left")
    fig.tight_layout(pad=0.5)
    _render(fig)


@solara.component
def BasinGauge():
    _ = _tick.value
    m = _model.value
    if not m: return

    bp = m.basin_fraction() * 100
    s, c = m.cfg.stress_frac * 100, m.cfg.critical_frac * 100

    # Net daily water balance (recharge + restoration - all draws)
    h_last  = m.history[-1] if m.history else None
    net_ml  = (m.cfg.recharge_mean_ml_per_day
               + (h_last["dc_restoration_ml"])
               - (h_last["dc_total_draw_ml"] + h_last["community_received_ml"]
                  + h_last["farm_total_received_ml"]) if h_last else 0)

    fig, ax = _fig(3.2, 2.65)
    ax.barh(0, 100, height=0.55, color=BORDER,            edgecolor="none")
    ax.barh(0, bp,  height=0.55, color=_status_color(bp), edgecolor="none")
    ax.axvline(s, color="#e3b341", lw=1.5, ls="--")
    ax.axvline(c, color="#da3633", lw=1.5, ls="--")
    # value label inside bar
    ax.text(min(bp, 97), 0, f" {bp:.1f}%",
            va="center", ha="left" if bp < 50 else "right",
            color="white", fontsize=9, fontweight="bold")
    # threshold labels below bar
    ax.text(s, -0.42, f"Stress\n{s:.0f}%", ha="center", va="top",
            color="#e3b341", fontsize=6.5)
    ax.text(c, -0.42, f"Crit\n{c:.0f}%",  ha="center", va="top",
            color="#da3633", fontsize=6.5)
    # net balance annotation
    net_color = "#3fb950" if net_ml >= 0 else "#f85149"
    net_sign  = "+" if net_ml >= 0 else ""
    ax.text(50, -0.82, f"Net: {net_sign}{net_ml:.1f} ML/day",
            ha="center", va="top", color=net_color, fontsize=7)

    ax.set_xlim(0, 100)
    ax.set_ylim(-1.05, 0.55)
    ax.set_yticks([])
    ax.xaxis.set_major_formatter(mticker.PercentFormatter())
    ax.set_title("Aquifer Gauge", color=TEXT, fontsize=9, fontweight="bold", pad=4)
    fig.tight_layout(pad=0.5)
    _render(fig)


@solara.component
def FarmHealth():
    _ = _tick.value
    m = _model.value
    if not m: return

    farms  = m.farms
    labels = [f"F{i+1}" for i in range(len(farms))]
    areas  = [f.current_area_ha / f.initial_area_ha * 100 for f in farms]
    losses = [f.yield_loss * 100 for f in farms]

    fig, (a1, a2) = _fig(3.2, 2.65, ncols=2)
    a1.bar(labels, areas,  color=[_status_color(p) for p in areas],  alpha=0.85)
    a1.set_ylim(0, 115)
    a1.set_title("Area %",      color=TEXT, fontsize=8, fontweight="bold", pad=3)

    a2.bar(labels, losses,
           color=["#da3633" if l > 50 else "#bd561d" if l > 25 else "#238636" for l in losses],
           alpha=0.85)
    a2.set_ylim(0, 115)
    a2.set_title("Yield Loss %", color=TEXT, fontsize=8, fontweight="bold", pad=3)

    for ax in (a1, a2):
        ax.tick_params(colors=MUTED, labelsize=7)

    fig.suptitle("Farm Health", color=TEXT, fontsize=9, fontweight="bold")
    fig.tight_layout(pad=0.4)
    _render(fig)


@solara.component
def DCCapacity():
    _ = _tick.value
    m = _model.value
    if not m or not m.history:
        _Placeholder(); return

    h     = list(m.history)
    years = [x["tick"] / 365 for x in h]
    cap   = [x["total_dc_capacity_ml"] for x in h]

    fig, ax = _fig(3.2, 2.65)
    ax.fill_between(years, cap, color="#f85149", alpha=0.18)
    ax.plot(years, cap, color="#f85149", lw=1.8)
    if m.cfg.policy_mode == "proactive":
        b = m.cfg.proactive_industrial_budget_ml
        ax.axhline(b, color="#e3b341", lw=1.2, ls="--", label=f"Cap {b:.0f} ML")
        ax.legend(fontsize=6, facecolor=SURFACE, edgecolor=BORDER, labelcolor=TEXT)
    ax.set_xlim(0, max(years[-1], 0.1))
    ax.set_xlabel("Year",    color=MUTED, fontsize=7)
    ax.set_ylabel("ML / day", color=MUTED, fontsize=7)
    ax.set_title("DC Capacity", color=TEXT, fontsize=9, fontweight="bold", pad=4)
    fig.tight_layout(pad=0.5)
    _render(fig)


# ── KPI row ───────────────────────────────────────────────────────────────────

@solara.component
def KPIRow():
    _ = _tick.value
    m = _model.value
    if not m: return

    bp    = m.basin_fraction() * 100
    year  = m.tick / 365
    dc    = sum(dc.current_capacity_ml for dc in m.data_centers)
    yl    = sum(f.yield_loss for f in m.farms) / max(len(m.farms), 1) * 100
    comp  = m.community.complaints
    s, c  = m.cfg.stress_frac * 100, m.cfg.critical_frac * 100
    phase, pcol = (
        ("Stable",   "#238636") if bp > s else
        ("Stressed", "#9e6a03") if bp > c else
        ("Critical", "#da3633")
    )

    def _card(val: str, label: str, bg: str):
        with solara.Column(style={
            "background":    bg,
            "border-radius": "6px",
            "padding":       "8px 12px",
            "flex":          "1",
            "min-width":     "88px",
            "align-items":   "center",
            "gap":           "1px",
        }):
            solara.Text(val,   style={"font-size": "17px", "font-weight": "700",
                                      "color": "white", "line-height": "1.2"})
            solara.Text(label, style={"font-size": "9px",  "color": "rgba(255,255,255,0.65)",
                                      "text-transform": "uppercase", "letter-spacing": "0.6px"})

    with solara.Row(style={
        "gap":         "6px",
        "padding":     "6px 10px",
        "flex-shrink": "0",
        "align-items": "stretch",
    }):
        _card(f"{year:.1f} yr", "Year",       BLUE)
        _card(f"{bp:.1f}%",    "Basin",      _status_color(bp))
        _card(phase,            "Phase",      pcol)
        _card(f"{dc:.1f} ML",  "DC Cap",     "#1565c0")
        _card(f"{yl:.1f}%",    "Yield Loss", "#4e342e" if yl < 25 else "#da3633")
        _card(f"{comp:,}",     "Complaints", "#4a148c" if comp < 100 else "#da3633")


# ── Agent status panel ────────────────────────────────────────────────────────

@solara.component
def AgentStatus():
    _ = _tick.value
    m = _model.value
    if not m: return

    tick = m.tick
    rows: list[tuple[str, str]] = []   # (label, value)

    for i, dc in enumerate(m.data_centers):
        if dc.active and tick >= dc.entry_tick:
            status = "active"
        else:
            status = f"yr {dc.entry_tick / 365:.1f}"
        fill = dc.received_today / dc.requested_today * 100 if dc.requested_today > 0 else 0
        rows.append((f"DC{i+1}", f"{dc.current_capacity_ml:.1f} ML  {fill:.0f}%  {status}"))

    comm = m.community
    # Derive current population from daily need (need_ml * 1e6 / L_per_cap)
    cur_pop = int(comm.daily_need_ml * 1_000_000 / m.cfg.community_l_per_capita_per_day)
    rows.append(("Comm", f"{comm.daily_need_ml:.2f} ML/d  pop:{cur_pop:,}"))

    for i, f in enumerate(m.farms):
        rows.append((f"Farm{i+1}",
                     f"{f.current_area_ha:.0f}/{f.initial_area_ha:.0f} ha  "
                     f"{f.yield_loss * 100:.0f}% loss"))

    reg = m.regulator
    if reg.mode == "reactive":
        rows.append(("Reg", "CAP ACTIVE" if reg.active_cap else "watching"))
    elif reg.mode == "proactive":
        rows.append(("Reg", f"budget {m.cfg.proactive_industrial_budget_ml:.0f} ML"))
    elif reg.mode == "staggered":
        rows.append(("Reg", "staggered"))

    with solara.Column(style={"gap": "3px"}):
        solara.Text("AGENTS", style={
            "font-size": "9px", "font-weight": "700",
            "color": MUTED, "letter-spacing": "1px", "margin-bottom": "4px",
        })
        for label, val in rows:
            with solara.Row(style={"gap": "4px", "align-items": "baseline"}):
                solara.Text(label, style={"font-size": "10px", "color": "#58a6ff",
                                          "font-weight": "600", "min-width": "36px"})
                solara.Text(val,   style={"font-size": "10px", "color": MUTED,
                                          "font-family": "monospace"})


# ── Left sidebar ──────────────────────────────────────────────────────────────

@solara.component
def Sidebar():
    scenario,   set_scenario   = solara.use_state(_scenario.value)
    seed,       set_seed       = solara.use_state(int(_seed.value))
    num_dcs,    set_num_dcs    = solara.use_state(int(_num_dcs.value))
    basin_pct,  set_basin_pct  = solara.use_state(int(_basin_pct.value))
    alpha,      set_alpha      = solara.use_state(float(_alpha.value))
    recharge,   set_recharge   = solara.use_state(float(_recharge.value))
    budget,     set_budget     = solara.use_state(float(_budget.value))
    restore,    set_restore    = solara.use_state(int(_restore.value))
    pop_growth, set_pop_growth = solara.use_state(float(_pop_growth.value))

    def _label(text: str):
        solara.Text(text, style={
            "font-size": "9px", "font-weight": "700",
            "color": MUTED, "letter-spacing": "0.9px",
            "text-transform": "uppercase", "margin-top": "8px",
        })

    def _divider():
        solara.HTML(tag="div", style={
            "height": "1px", "background": BORDER,
            "margin": "8px 0", "width": "100%",
        })

    with solara.Column(style={
        "width":       "210px",
        "min-width":   "210px",
        "background":  SURFACE,
        "border-right": f"1px solid {BORDER}",
        "padding":     "12px 10px",
        "overflow-y":  "auto",
        "gap":         "4px",
        # no explicit height — align-self:stretch fills the main body row
    }):
        _label("Scenario")
        solara.Select(label="", value=scenario, values=SCENARIOS, on_value=set_scenario,
                      style={"width": "100%", "font-size": "13px"})

        _divider()
        _label("Parameters")

        solara.SliderInt("Seed",           value=seed,      min=0,    max=999,  on_value=set_seed)
        solara.SliderInt("Data Centers",   value=num_dcs,   min=1,    max=8,    on_value=set_num_dcs)
        solara.SliderInt("Initial Basin %",value=basin_pct, min=20,   max=100,  step=5,   on_value=set_basin_pct)
        solara.SliderFloat("Stress α",     value=alpha,     min=0.0,  max=10.0, step=0.5, on_value=set_alpha)
        solara.SliderFloat("Recharge ML/d",value=recharge,  min=10.0, max=100.0,step=5.0, on_value=set_recharge)
        solara.SliderFloat("DC Budget ML", value=budget,    min=5.0,  max=50.0, step=1.0, on_value=set_budget)
        solara.SliderInt("DC Restore %",   value=restore,    min=0,   max=150,  step=5,   on_value=set_restore)
        solara.SliderFloat("Pop Growth %/yr", value=pop_growth, min=0.0, max=4.0, step=0.5, on_value=set_pop_growth)

        with solara.Row(style={"margin-top": "10px"}):
            solara.Button(
                "↺  Apply & Reset",
                on_click=lambda: _do_reset(scenario, seed, num_dcs, basin_pct,
                                           alpha, recharge, budget, restore, pop_growth),
                color="primary",
                style={"width": "100%", "font-size": "12px"},
            )

        _divider()
        AgentStatus()


# ── Main Page ─────────────────────────────────────────────────────────────────

@solara.component
def Page():
    playing = _playing.value   # subscribe so play-button icon updates

    # ── Kill all scrollbars and force full-page dark layout via CSS ───────────
    solara.Style(f"""
        html, body {{
            overflow: hidden !important;
            height: 100% !important;
            margin: 0;
            background: {BG} !important;
        }}
        .v-application {{
            height: 100vh !important;
            overflow: hidden !important;
            background: {BG} !important;
        }}
        .v-application--wrap {{
            height: 100vh !important;
            overflow: hidden !important;
            min-height: unset !important;
            background: {BG} !important;
        }}
        .v-main {{
            height: 100vh !important;
            overflow: hidden !important;
            padding: 0 !important;
            background: {BG} !important;
        }}
        .v-main__wrap {{
            height: 100% !important;
            overflow: hidden !important;
            display: flex;
            flex-direction: column;
            background: {BG} !important;
        }}
        /* hide "This website runs on Solara" — absolutely-positioned banner */
        div[style*="position: absolute"][style*="bottom: 0"] {{ display: none !important; }}
        /* kill every overflow:auto Solara injects into the content chain */
        .v-content__wrap,
        .v-content__wrap > div {{
            overflow: hidden !important;
            height: 100% !important;
        }}
        /* Solara's autorouter and its immediate v-sheet child must be dark
           and fill the full viewport so no white bleeds through */
        .solara-autorouter-content {{
            height:     100% !important;
            min-height: 0   !important;
            overflow:   hidden !important;
            background: {BG} !important;
        }}
        .solara-autorouter-content > .v-sheet {{
            height:     100% !important;
            min-height: 0   !important;
            overflow:   hidden !important;
            background: {BG} !important;
            row-gap:    0   !important;
        }}
        /* wrapper Solara injects around FigureMatplotlib:
           switch from height:100% (content-relative) to flex:1 (fills panel) */
        div[style="height: 100%;"] {{
            flex:         1 1 0% !important;
            height:       0 !important;    /* base=0, grows via flex */
            min-height:   0 !important;
            width:        100% !important;
            display:      flex !important;
            align-items:  stretch !important;
        }}
        /* image: fill the wrapper completely; object-fit:contain keeps
           aspect-ratio and the SURFACE2 letterbox is invisible (same bg) */
        img.widget-image {{
            width:       100% !important;
            height:      100% !important;
            display:     block !important;
            object-fit:  contain !important;
            flex:        1 1 0% !important;
            min-height:  0 !important;
        }}
        /* thin custom scrollbars */
        ::-webkit-scrollbar {{ width: 4px; height: 4px; }}
        ::-webkit-scrollbar-track {{ background: {BG}; }}
        ::-webkit-scrollbar-thumb {{ background: {BORDER}; border-radius: 2px; }}
        /* ensure chart panel cells stay dark */
        .parched-panel {{
            background: {SURFACE2} !important;
            border: 1px solid {BORDER};
            border-radius: 8px;
            overflow: hidden;
            flex: 1;
            min-width: 0;
        }}
    """)

    with solara.Column(style={
        "height":       "100%",
        "max-height":   "100vh",
        "overflow":     "hidden",
        "background":   BG,
        "color":        TEXT,
        "gap":          "0",
        "display":      "flex",
        "flex-direction": "column",
    }):

        # ── Header bar ────────────────────────────────────────────────────────
        with solara.Row(style={
            "background":    SURFACE,
            "border-bottom": f"1px solid {BORDER}",
            "padding":       "0 14px",
            "height":        "50px",
            "align-items":   "center",
            "gap":           "10px",
            "flex-shrink":   "0",
        }):
            solara.Text("💧", style={"font-size": "20px"})
            solara.Text("PARCHED", style={
                "font-size": "15px", "font-weight": "700",
                "color": TEXT, "letter-spacing": "1.2px",
            })
            solara.Text("When AI Drinks Your Town Dry", style={
                "font-size": "11px", "color": MUTED, "flex": "1",
            })
            # speed slider
            solara.Text("Speed", style={"font-size": "10px", "color": MUTED, "white-space": "nowrap"})
            with solara.Column(style={"min-width": "110px", "max-width": "140px", "justify-content": "center"}):
                solara.SliderInt(
                    label="", value=_speed.value, min=1, max=40,
                    on_value=lambda v: setattr(_speed, "value", v),
                )
            solara.Text(f"{_speed.value}×", style={"font-size": "11px", "color": TEXT, "min-width": "24px"})
            # play / step controls
            solara.Button(
                "⏸  Pause" if playing else "▶  Play",
                on_click=_toggle_play,
                color="warning" if playing else "success",
                style={"font-size": "12px", "min-width": "90px"},
            )
            solara.Button(
                "▶|  Step",
                on_click=_do_step,
                style={"font-size": "12px", "min-width": "72px"},
            )

        # ── KPI strip ─────────────────────────────────────────────────────────
        with solara.Column(style={
            "background":    SURFACE2,
            "border-bottom": f"1px solid {BORDER}",
            "flex-shrink":   "0",
        }):
            KPIRow()

        # ── Main body: sidebar + charts ───────────────────────────────────────
        with solara.Row(style={
            "flex":        "1",
            "overflow":    "hidden",
            "min-height":  "0",
            "height":      "100%",  # makes height definite so children's height:100% resolves
            "background":  BG,
            "gap":         "0",
        }):

            # Left sidebar
            Sidebar()

            # Chart grid — no explicit height: align-self:stretch fills the row
            with solara.Column(style={
                "flex":           "1",
                "min-height":     "0",
                "overflow":       "hidden",
                "padding":        "8px",
                "gap":            "7px",
                "min-width":      "0",
                "background":     BG,
            }):

                # Row 1 — two wide charts
                with solara.Row(style={
                    "flex":       "1",
                    "gap":        "7px",
                    "min-height": "0",
                    "overflow":   "hidden",
                }):
                    with solara.Column(style={
                        "flex": "1", "background": SURFACE2,
                        "border": f"1px solid {BORDER}",
                        "border-radius": "8px",
                        "padding": "8px",
                        "overflow": "hidden",
                        "min-width": "0",
                    }):
                        BasinTimeseries()

                    with solara.Column(style={
                        "flex": "1", "background": SURFACE2,
                        "border": f"1px solid {BORDER}",
                        "border-radius": "8px",
                        "padding": "8px",
                        "overflow": "hidden",
                        "min-width": "0",
                    }):
                        WaterAlloc()

                # Row 2 — three compact charts
                with solara.Row(style={
                    "flex":       "1",
                    "gap":        "7px",
                    "min-height": "0",
                    "overflow":   "hidden",
                }):
                    with solara.Column(style={
                        "flex": "1", "background": SURFACE2,
                        "border": f"1px solid {BORDER}",
                        "border-radius": "8px",
                        "padding": "8px",
                        "overflow": "hidden",
                        "min-width": "0",
                    }):
                        BasinGauge()

                    with solara.Column(style={
                        "flex": "1", "background": SURFACE2,
                        "border": f"1px solid {BORDER}",
                        "border-radius": "8px",
                        "padding": "8px",
                        "overflow": "hidden",
                        "min-width": "0",
                    }):
                        FarmHealth()

                    with solara.Column(style={
                        "flex": "1", "background": SURFACE2,
                        "border": f"1px solid {BORDER}",
                        "border-radius": "8px",
                        "padding": "8px",
                        "overflow": "hidden",
                        "min-width": "0",
                    }):
                        DCCapacity()
