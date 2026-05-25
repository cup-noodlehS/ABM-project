"""
PARCHED Interactive Visualization.

Run with:
    solara run app.py

Opens a browser dashboard at http://localhost:8765 where you can:
- Pick a scenario (A / B / C / D) and tweak every key parameter
- Watch the basin drain (or survive) tick by tick
- See live charts for water balance, agent draws, farm health, and DC growth
"""

import mesa
import solara
import matplotlib
matplotlib.use("agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

from mesa.visualization import SolaraViz, make_plot_component
from mesa.visualization.utils import update_counter

from parched_model import ParchedModel, SimConfig


# -----------------------------------------------------------------------
# Wrapper model: bridges SolaraViz keyword-arg interface -> SimConfig
# -----------------------------------------------------------------------

class ParchedVizModel(ParchedModel):
    """Thin wrapper that accepts SolaraViz model_params as kwargs."""

    def __init__(
        self,
        scenario="A — Unregulated",
        seed=42,
        num_data_centers=4,
        basin_initial_pct=80,
        cooling_stress_amplification=4.0,
        recharge_mean_ml_per_day=50.0,
        proactive_budget_ml=15.0,
    ):
        scenario_key = scenario.split("\u2014")[0].strip() if "\u2014" in scenario else scenario
        policy_map = {
            "A": "off",
            "B": "reactive",
            "C": "proactive",
            "D": "staggered",
        }
        policy = policy_map.get(scenario_key, "off")

        cfg = SimConfig(
            seed=int(seed),
            policy_mode=policy,
            num_data_centers=int(num_data_centers),
            basin_initial_frac=basin_initial_pct / 100.0,
            cooling_stress_amplification=cooling_stress_amplification,
            recharge_mean_ml_per_day=recharge_mean_ml_per_day,
            proactive_industrial_budget_ml=proactive_budget_ml,
            label="viz_" + scenario_key,
        )

        if policy == "staggered":
            entries = tuple(i * 730 for i in range(cfg.num_data_centers))
            cfg.staggered_entry_ticks = entries

        super().__init__(cfg)

        # Mesa DataCollector drives make_plot_component
        self.datacollector = mesa.DataCollector(
            model_reporters={
                "Basin Level (%)": lambda m: m.basin_fraction() * 100,
                "DC Total Draw (ML)": lambda m: (
                    m.history[-1]["dc_total_draw_ml"] if m.history else 0
                ),
                "Community Draw (ML)": lambda m: (
                    m.history[-1]["community_received_ml"] if m.history else 0
                ),
                "Farm Draw (ML)": lambda m: (
                    m.history[-1]["farm_total_received_ml"] if m.history else 0
                ),
                "DC Capacity (ML)": lambda m: sum(
                    dc.current_capacity_ml for dc in m.data_centers
                ),
                "Farm Yield Loss (%)": lambda m: (
                    sum(f.yield_loss for f in m.farms)
                    / max(len(m.farms), 1)
                    * 100
                ),
                "Community Complaints": lambda m: m.community.complaints,
            },
        )

    def step(self):
        super().step()
        self.datacollector.collect(self)


# -----------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------

def _status_color(basin_pct):
    if basin_pct > 60:
        return "#2e7d32"   # green
    if basin_pct > 40:
        return "#f9a825"   # amber
    if basin_pct > 20:
        return "#e65100"   # orange
    return "#b71c1c"       # red


SCENARIO_LABELS = {
    "off": "A \u2014 Unregulated",
    "reactive": "B \u2014 Reactive",
    "proactive": "C \u2014 Proactive",
    "staggered": "D \u2014 Staggered",
}


# -----------------------------------------------------------------------
# Custom Solara components
# All use @solara.component + update_counter.get() so Mesa re-renders them
# -----------------------------------------------------------------------

@solara.component
def DashboardHeader(model):
    """Top-row KPI cards."""
    update_counter.get()

    tick = model.tick
    year = tick / 365.0
    basin_pct = model.basin_fraction() * 100
    complaints = model.community.complaints
    yield_loss = (
        sum(f.yield_loss for f in model.farms) / max(len(model.farms), 1) * 100
    )
    dc_cap = sum(dc.current_capacity_ml for dc in model.data_centers)
    status = _status_color(basin_pct)

    stress_frac = model.cfg.stress_frac * 100
    critical_frac = model.cfg.critical_frac * 100

    if basin_pct > stress_frac:
        phase = "Stable"
    elif basin_pct > critical_frac:
        phase = "Stressed"
    else:
        phase = "Critical"

    scenario_name = SCENARIO_LABELS.get(model.cfg.policy_mode, model.cfg.policy_mode)

    with solara.Row(
        style={
            "gap": "12px",
            "flex-wrap": "wrap",
            "margin-bottom": "4px",
        }
    ):
        _kpi_card(scenario_name, "Year **{:.1f}** (tick {})".format(year, tick), "#263238")
        _kpi_card("Basin **{:.1f}%**".format(basin_pct), "Phase: **{}**".format(phase), status)
        _kpi_card("DC Capacity", "**{:.1f} ML/day**".format(dc_cap), "#1565c0")
        _kpi_card("Farm Yield Loss", "**{:.1f}%**".format(yield_loss),
                  "#4e342e" if yield_loss < 25 else "#b71c1c")
        _kpi_card("Complaints", "**{:,}**".format(complaints),
                  "#4a148c" if complaints < 100 else "#b71c1c")


def _kpi_card(line1, line2, bg):
    with solara.Card(
        style={
            "flex": "1 1 160px",
            "min-width": "140px",
            "text-align": "center",
            "background": bg,
            "color": "white",
            "padding": "8px",
        }
    ):
        solara.Markdown(line1 + "  \n" + line2)


@solara.component
def BasinGauge(model):
    """Horizontal progress bar showing current basin level with thresholds."""
    update_counter.get()

    basin_pct = model.basin_fraction() * 100
    stress_pct = model.cfg.stress_frac * 100
    critical_pct = model.cfg.critical_frac * 100

    fig, ax = plt.subplots(figsize=(7, 2.0))
    fig.patch.set_facecolor("#1e1e1e")
    ax.set_facecolor("#1e1e1e")

    ax.barh(0, 100, height=0.6, color="#37474f", edgecolor="none")
    color = _status_color(basin_pct)
    ax.barh(0, basin_pct, height=0.6, color=color, edgecolor="none")

    ax.axvline(stress_pct, color="#ffeb3b", linewidth=2, linestyle="--",
               label="Stress ({:.0f}%)".format(stress_pct))
    ax.axvline(critical_pct, color="#ff1744", linewidth=2, linestyle="--",
               label="Critical ({:.0f}%)".format(critical_pct))

    ax.set_xlim(0, 100)
    ax.set_ylim(-0.5, 0.5)
    ax.set_yticks([])
    ax.set_xlabel("Basin Level (%)", color="white", fontsize=10)
    ax.tick_params(colors="white")
    ax.xaxis.set_major_formatter(mticker.PercentFormatter())
    ax.legend(loc="upper right", fontsize=8, facecolor="#263238",
              edgecolor="none", labelcolor="white")
    ax.set_title("Aquifer Basin Level", color="white", fontsize=12, fontweight="bold")
    for spine in ax.spines.values():
        spine.set_visible(False)

    fig.tight_layout()
    solara.FigureMatplotlib(fig)
    plt.close(fig)


@solara.component
def BasinTimeseriesChart(model):
    """Basin fraction over time with threshold bands."""
    update_counter.get()

    history = list(model.history)  # snapshot to avoid mid-render mutations
    if not history:
        solara.Markdown("*Waiting for first step...*")
        return

    years = [h["tick"] / 365.0 for h in history]
    basin_pct = [h["basin_frac"] * 100 for h in history]
    stress_pct = model.cfg.stress_frac * 100
    critical_pct = model.cfg.critical_frac * 100

    fig, ax = plt.subplots(figsize=(7, 3.2))
    fig.patch.set_facecolor("#1e1e1e")
    ax.set_facecolor("#1e1e1e")

    ax.axhspan(0, critical_pct, color="#b71c1c", alpha=0.15, label="Critical zone")
    ax.axhspan(critical_pct, stress_pct, color="#e65100", alpha=0.10, label="Stress zone")
    ax.plot(years, basin_pct, color="#29b6f6", linewidth=2, label="Basin level")
    ax.axhline(stress_pct, color="#ffeb3b", linewidth=1, linestyle="--", alpha=0.7)
    ax.axhline(critical_pct, color="#ff1744", linewidth=1, linestyle="--", alpha=0.7)

    ax.set_xlim(0, max(years[-1], 0.1))
    ax.set_ylim(0, 100)
    ax.set_xlabel("Year", color="white", fontsize=10)
    ax.set_ylabel("Basin Level (%)", color="white", fontsize=10)
    ax.set_title("Basin Level Over Time", color="white", fontsize=12, fontweight="bold")
    ax.tick_params(colors="white")
    ax.legend(loc="upper right", fontsize=8, facecolor="#263238",
              edgecolor="none", labelcolor="white")
    for spine in ax.spines.values():
        spine.set_color("#555")

    fig.tight_layout()
    solara.FigureMatplotlib(fig)
    plt.close(fig)


@solara.component
def WaterBalanceChart(model):
    """Stacked area chart: who is drawing how much water over time."""
    update_counter.get()

    history = list(model.history)  # snapshot
    if not history:
        solara.Markdown("*Waiting for first step...*")
        return

    years = [h["tick"] / 365.0 for h in history]
    dc_draw = [h["dc_total_draw_ml"] for h in history]
    comm_draw = [h["community_received_ml"] for h in history]
    farm_draw = [h["farm_total_received_ml"] for h in history]

    fig, ax = plt.subplots(figsize=(7, 3.2))
    fig.patch.set_facecolor("#1e1e1e")
    ax.set_facecolor("#1e1e1e")

    ax.stackplot(
        years, comm_draw, dc_draw, farm_draw,
        labels=["Community", "Data Centers", "Farms"],
        colors=["#42a5f5", "#ef5350", "#66bb6a"],
        alpha=0.85,
    )

    ax.set_xlabel("Year", color="white", fontsize=10)
    ax.set_ylabel("Water Delivered (ML/day)", color="white", fontsize=10)
    ax.set_title("Daily Water Allocation by Sector", color="white", fontsize=12, fontweight="bold")
    ax.tick_params(colors="white")
    ax.legend(loc="upper right", fontsize=8, facecolor="#263238",
              edgecolor="none", labelcolor="white")
    for spine in ax.spines.values():
        spine.set_color("#555")

    fig.tight_layout()
    solara.FigureMatplotlib(fig)
    plt.close(fig)


@solara.component
def DCCapacityChart(model):
    """DC total capacity growth over time."""
    update_counter.get()

    history = list(model.history)  # snapshot
    if not history:
        solara.Markdown("*Waiting for first step...*")
        return

    years = [h["tick"] / 365.0 for h in history]
    dc_cap = [h["total_dc_capacity_ml"] for h in history]

    fig, ax = plt.subplots(figsize=(7, 2.6))
    fig.patch.set_facecolor("#1e1e1e")
    ax.set_facecolor("#1e1e1e")

    ax.fill_between(years, dc_cap, color="#ef5350", alpha=0.3)
    ax.plot(years, dc_cap, color="#ef5350", linewidth=2, label="Total DC Capacity")

    if model.cfg.policy_mode == "proactive":
        budget_line = model.cfg.proactive_industrial_budget_ml * 1.5
        ax.axhline(budget_line, color="#ffeb3b", linewidth=1.5, linestyle="--",
                    label="Proactive cap ({:.0f} ML)".format(budget_line))

    ax.set_xlabel("Year", color="white", fontsize=10)
    ax.set_ylabel("Capacity (ML/day)", color="white", fontsize=10)
    ax.set_title("Data Center Capacity Growth", color="white", fontsize=12, fontweight="bold")
    ax.tick_params(colors="white")
    ax.legend(loc="upper left", fontsize=8, facecolor="#263238",
              edgecolor="none", labelcolor="white")
    for spine in ax.spines.values():
        spine.set_color("#555")

    fig.tight_layout()
    solara.FigureMatplotlib(fig)
    plt.close(fig)


@solara.component
def FarmHealthChart(model):
    """Farm irrigated area and yield loss side by side."""
    update_counter.get()

    farms = model.farms
    labels = ["Farm {}".format(i + 1) for i in range(len(farms))]
    areas_current = [f.current_area_ha for f in farms]
    areas_initial = [f.initial_area_ha for f in farms]
    yield_losses = [f.yield_loss * 100 for f in farms]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7, 2.6))
    fig.patch.set_facecolor("#1e1e1e")

    ax1.set_facecolor("#1e1e1e")
    ax1.bar(labels, areas_initial, color="#4a635a", alpha=0.4, label="Initial")
    ax1.bar(labels, areas_current, color="#66bb6a", alpha=0.85, label="Current")
    ax1.set_ylabel("Hectares", color="white", fontsize=9)
    ax1.set_title("Irrigated Area", color="white", fontsize=11, fontweight="bold")
    ax1.tick_params(colors="white")
    ax1.legend(fontsize=7, facecolor="#263238", edgecolor="none", labelcolor="white")
    for spine in ax1.spines.values():
        spine.set_color("#555")

    ax2.set_facecolor("#1e1e1e")
    colors = ["#66bb6a" if yl < 25 else "#e65100" if yl < 50 else "#b71c1c" for yl in yield_losses]
    ax2.bar(labels, yield_losses, color=colors, alpha=0.85)
    ax2.set_ylabel("Yield Loss (%)", color="white", fontsize=9)
    ax2.set_title("Permanent Yield Loss", color="white", fontsize=11, fontweight="bold")
    ax2.set_ylim(0, 100)
    ax2.tick_params(colors="white")
    for spine in ax2.spines.values():
        spine.set_color("#555")

    fig.tight_layout()
    solara.FigureMatplotlib(fig)
    plt.close(fig)


@solara.component
def AgentStatusTable(model):
    """Detailed per-agent status panel."""
    update_counter.get()

    tick = model.tick

    with solara.Card(
        style={"background": "#263238", "color": "white", "margin-top": "4px"}
    ):
        solara.Markdown("### Agent Status")

        solara.Markdown("**Data Centers**")
        for i, dc in enumerate(model.data_centers):
            if dc.active and tick >= dc.entry_tick:
                active = "Active"
            else:
                active = "Entry yr {:.1f}".format(dc.entry_tick / 365.0)
            fill_pct = (dc.received_today / dc.requested_today * 100) if dc.requested_today > 0 else 0
            solara.Markdown(
                "- DC {}: cap **{:.1f} ML** | exp {}/{} | fill {:.0f}% | {}".format(
                    i + 1, dc.current_capacity_ml, dc.expansions_used,
                    dc.expansion_budget, fill_pct, active
                )
            )

        comm = model.community
        solara.Markdown("**Community**")
        solara.Markdown(
            "- Pop {:,} | need {:.1f} ML/day | shortage streak {} d | total shortage {} d".format(
                model.cfg.community_population, comm.daily_need_ml,
                comm.shortage_streak, comm.cumulative_shortage_days
            )
        )

        solara.Markdown("**Farms**")
        for i, f in enumerate(model.farms):
            solara.Markdown(
                "- Farm {}: {:.0f}/{:.0f} ha | loss {:.1f}% | streak {} d".format(
                    i + 1, f.current_area_ha, f.initial_area_ha,
                    f.yield_loss * 100, f.shortage_streak
                )
            )

        reg = model.regulator
        if reg.mode != "off":
            solara.Markdown("**Regulator**")
            if reg.mode == "reactive":
                cap_status = "CAP ACTIVE" if reg.active_cap else "monitoring"
                delay = " (delay: {} ticks)".format(reg.delay_remaining) if reg.delay_remaining else ""
                solara.Markdown("- Reactive: {}{}".format(cap_status, delay))
            elif reg.mode == "proactive":
                solara.Markdown(
                    "- Proactive: budget {} ML/day".format(model.cfg.proactive_industrial_budget_ml)
                )
            elif reg.mode == "staggered":
                solara.Markdown("- Staggered entry: {}".format(model.cfg.staggered_entry_ticks))


# -----------------------------------------------------------------------
# Model parameters (interactive controls)
# -----------------------------------------------------------------------

model_params = {
    "scenario": {
        "type": "Select",
        "value": "A \u2014 Unregulated",
        "values": [
            "A \u2014 Unregulated",
            "B \u2014 Reactive",
            "C \u2014 Proactive",
            "D \u2014 Staggered",
        ],
        "label": "Scenario",
    },
    "seed": {
        "type": "SliderInt",
        "value": 42,
        "min": 0,
        "max": 999,
        "step": 1,
        "label": "Random Seed",
    },
    "num_data_centers": {
        "type": "SliderInt",
        "value": 4,
        "min": 1,
        "max": 8,
        "step": 1,
        "label": "Number of Data Centers",
    },
    "basin_initial_pct": {
        "type": "SliderInt",
        "value": 80,
        "min": 20,
        "max": 100,
        "step": 5,
        "label": "Initial Basin Level (%)",
    },
    "cooling_stress_amplification": {
        "type": "SliderFloat",
        "value": 4.0,
        "min": 0.0,
        "max": 10.0,
        "step": 0.5,
        "label": "Cooling Stress Amplification",
    },
    "recharge_mean_ml_per_day": {
        "type": "SliderFloat",
        "value": 50.0,
        "min": 10.0,
        "max": 100.0,
        "step": 5.0,
        "label": "Mean Recharge (ML/day)",
    },
    "proactive_budget_ml": {
        "type": "SliderFloat",
        "value": 15.0,
        "min": 5.0,
        "max": 50.0,
        "step": 1.0,
        "label": "Proactive DC Budget (ML/day)",
    },
}


# -----------------------------------------------------------------------
# Assemble the page
# -----------------------------------------------------------------------

model = ParchedVizModel()

page = SolaraViz(
    model,
    components=[
        DashboardHeader,
        BasinGauge,
        BasinTimeseriesChart,
        WaterBalanceChart,
        DCCapacityChart,
        FarmHealthChart,
        AgentStatusTable,
    ],
    model_params=model_params,
    name="PARCHED: When AI Drinks Your Town Dry",
    play_interval=50,
)
