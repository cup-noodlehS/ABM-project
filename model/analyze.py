"""
Statistical analysis and figure generation for PARCHED.

Reads CSVs in release/results/, runs the three hypothesis tests, and writes
publication figures to release/figures/.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats

# -------------------------------------------------------------------------
# Paths / config
# -------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = REPO_ROOT / "results"
FIGURES_DIR = REPO_ROOT / "figures"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

SCENARIOS = ["A_unregulated", "B_reactive", "C_proactive", "D_staggered"]
SCENARIO_LABELS = {
    "A_unregulated": "A. Unregulated",
    "B_reactive": "B. Reactive cap",
    "C_proactive": "C. Proactive budget",
    "D_staggered": "D. Staggered entry",
}
PALETTE = {
    "A_unregulated": "#D9514E",   # red
    "B_reactive":   "#E6A532",    # amber
    "C_proactive":  "#3EE6C5",    # teal
    "D_staggered":  "#6F9CEB",    # blue
}

# Match the proposal deck's dark theme so figures embed cleanly.
plt.rcParams.update(
    {
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "axes.edgecolor": "#222",
        "axes.labelcolor": "#222",
        "xtick.color": "#222",
        "ytick.color": "#222",
        "axes.grid": True,
        "grid.alpha": 0.25,
        "font.family": "DejaVu Sans",
        "savefig.dpi": 200,
        "savefig.bbox": "tight",
    }
)
sns.set_palette([PALETTE[s] for s in SCENARIOS])


# -------------------------------------------------------------------------
# Data loading
# -------------------------------------------------------------------------

def load_all_runs() -> pd.DataFrame:
    frames = []
    for s in SCENARIOS:
        path = RESULTS_DIR / f"scenario_{s}_runs.csv"
        df = pd.read_csv(path)
        df["scenario"] = s
        frames.append(df)
    out = pd.concat(frames, ignore_index=True)
    out["time_to_critical_years"] = out["time_to_critical_ticks"] = out["time_to_critical_stress"] / 365.0
    return out


def load_history(scenario: str, seed: int = 0) -> pd.DataFrame:
    path = RESULTS_DIR / f"scenario_{scenario}_history_seed{seed}.csv"
    return pd.read_csv(path)


# -------------------------------------------------------------------------
# Hypothesis tests
# -------------------------------------------------------------------------

def test_h1_unsustainable(df: pd.DataFrame, out: dict) -> None:
    """H1: Scenario A reaches critical stress within 5-8 simulated years."""
    a = df[df["scenario"] == "A_unregulated"]["time_to_critical_stress"]
    n_reach = (a < 3650).sum()
    frac_reach = n_reach / len(a)
    years = a / 365.0
    # one-sided t-test: mean < 8 years (upper bound of H1 claim)
    t_upper, p_upper = stats.ttest_1samp(years, 8.0, alternative="less")
    # one-sided t-test: mean > 5 years (lower bound)
    t_lower, p_lower = stats.ttest_1samp(years, 5.0, alternative="greater")
    out["H1"] = {
        "n_runs": int(len(a)),
        "frac_reaching_critical": float(frac_reach),
        "mean_years": float(years.mean()),
        "std_years": float(years.std()),
        "p_lt_8yr": float(p_upper),     # H1 says <= 8 years; test mean < 8
        "p_gt_5yr": float(p_lower),     # H1 says >= 5 years; test mean > 5
        "verdict": (
            "supported" if frac_reach >= 0.9 and 4.5 <= years.mean() <= 8.5 else "partial"
        ),
    }


def test_h2_tipping_point(out: dict, df: pd.DataFrame) -> None:
    """H2: The basin appears stable for years, then collapses rapidly once it
    crosses the stress threshold (~40%).

    We measure the trajectory-level rate of decline in the pre-crossing phase
    (start to 40%) versus the post-crossing phase (40% to critical/end). If
    the basin is stable then collapsing, the post-crossing rate should be
    several times steeper than the pre-crossing rate.
    """
    pre_rates = []
    post_rates = []
    cross_years = []
    detail = None
    for seed in range(50):
        path = RESULTS_DIR / f"scenario_A_unregulated_history_seed{seed}.csv"
        if not path.exists():
            continue
        hist = pd.read_csv(path)
        cross_idx = hist[hist["basin_frac"] < 0.40].index
        if cross_idx.empty:
            continue
        cross_pos = int(cross_idx[0])
        cross_tick = int(hist.loc[cross_pos, "tick"])
        # Pre-crossing: full trajectory from tick 0 to the crossing
        if cross_tick <= 30:
            continue
        pre_drop = hist.loc[0, "basin_frac"] - hist.loc[cross_pos, "basin_frac"]
        pre_years = cross_tick / 365.0
        pre_rate = pre_drop / pre_years
        # Post-crossing: from crossing to either end of run or basin = 5%
        post_end_idx = hist[hist["basin_frac"] < 0.05].index
        if post_end_idx.empty:
            continue
        post_end_pos = int(post_end_idx[0])
        post_drop = hist.loc[cross_pos, "basin_frac"] - hist.loc[post_end_pos, "basin_frac"]
        post_years = (hist.loc[post_end_pos, "tick"] - cross_tick) / 365.0
        if post_years <= 0:
            continue
        post_rate = post_drop / post_years
        pre_rates.append(pre_rate)
        post_rates.append(post_rate)
        cross_years.append(cross_tick / 365.0)
        if detail is None:
            # local slopes (for the detail plot only)
            window = 180
            pre_window = hist.iloc[max(0, cross_pos - window):cross_pos]
            post_window = hist.iloc[cross_pos:cross_pos + window]
            s_pre, _, *_ = stats.linregress(pre_window["tick"], pre_window["basin_frac"])
            s_post, _, *_ = stats.linregress(post_window["tick"], post_window["basin_frac"])
            detail = (seed, hist, cross_tick, s_pre, s_post)

    pre_arr = np.array(pre_rates)
    post_arr = np.array(post_rates)
    ratios = post_arr / pre_arr
    # Paired one-sided t-test: post-crossing rate exceeds pre-crossing rate
    t, p = stats.ttest_rel(post_arr, pre_arr, alternative="greater")
    out["H2"] = {
        "n_runs_with_crossing": int(len(pre_arr)),
        "median_pre_rate_per_year": float(np.median(pre_arr)),
        "median_post_rate_per_year": float(np.median(post_arr)),
        "median_rate_ratio_post_over_pre": float(np.median(ratios)),
        "median_crossing_year": float(np.median(cross_years)),
        "paired_t": float(t),
        "paired_p": float(p),
        "verdict": (
            "supported"
            if np.median(ratios) > 1.5 and p < 0.05
            else "partial"
        ),
    }
    seed, hist, cross_tick, s_pre, s_post = detail
    out["_h2_plot"] = {
        "seed": seed,
        "ticks": hist["tick"].tolist(),
        "basin_frac": hist["basin_frac"].tolist(),
        "cross_tick": cross_tick,
        "s_pre": float(s_pre),
        "s_post": float(s_post),
    }


def test_h3_policy(df: pd.DataFrame, out: dict) -> None:
    """H3: Scenario C delays critical stress by >= 40% vs Scenario A."""
    a = df[df["scenario"] == "A_unregulated"]["time_to_critical_stress"]
    c = df[df["scenario"] == "C_proactive"]["time_to_critical_stress"]
    # Welch's t-test (unequal variances)
    t, p = stats.ttest_ind(c, a, equal_var=False, alternative="greater")
    delay = (c.mean() - a.mean()) / a.mean()
    out["H3"] = {
        "mean_A_years": float(a.mean() / 365.0),
        "mean_C_years": float(c.mean() / 365.0),
        "delay_fraction": float(delay),       # >= 0.40 needed for H1
        "welch_t": float(t),
        "welch_p": float(p),
        "verdict": "supported" if delay >= 0.40 and p < 0.05 else "partial",
    }


# -------------------------------------------------------------------------
# Figures
# -------------------------------------------------------------------------

def fig_basin_timeseries() -> None:
    """Per-scenario basin level over time, mean +/- 95% CI band."""
    fig, ax = plt.subplots(figsize=(9, 5))
    for s in SCENARIOS:
        hist = load_history(s, seed=0)
        ax.plot(
            hist["tick"] / 365.0,
            hist["basin_frac"] * 100.0,
            label=SCENARIO_LABELS[s],
            color=PALETTE[s],
            linewidth=2,
        )
    ax.axhline(20, color="#999", linestyle="--", linewidth=1)
    ax.text(0.2, 22, "critical (20%)", color="#666", fontsize=9)
    ax.axhline(40, color="#bbb", linestyle=":", linewidth=1)
    ax.text(0.2, 42, "stress threshold (40%)", color="#888", fontsize=9)
    ax.set_xlabel("Simulated years")
    ax.set_ylabel("Basin level (% of capacity)")
    ax.set_title("Basin trajectory by scenario (representative seed)")
    ax.legend(loc="lower left", frameon=False)
    ax.set_ylim(0, 100)
    fig.savefig(FIGURES_DIR / "fig_basin_timeseries.png")
    plt.close(fig)


def fig_time_to_stress(df: pd.DataFrame) -> None:
    """Boxplot of time-to-critical-stress per scenario."""
    fig, ax = plt.subplots(figsize=(8, 5))
    order = SCENARIOS
    plot_df = df.copy()
    plot_df["years_to_critical"] = plot_df["time_to_critical_stress"] / 365.0
    sns.boxplot(
        data=plot_df,
        x="scenario",
        y="years_to_critical",
        order=order,
        palette=[PALETTE[s] for s in order],
        ax=ax,
        showfliers=False,
        width=0.55,
    )
    sns.stripplot(
        data=plot_df,
        x="scenario",
        y="years_to_critical",
        order=order,
        ax=ax,
        color="#222",
        size=2.5,
        alpha=0.5,
        jitter=0.18,
    )
    ax.set_xticklabels([SCENARIO_LABELS[s] for s in order], rotation=15)
    ax.axhline(10.0, color="#666", linestyle="--", linewidth=1)
    ax.text(0.05, 10.15, "simulation horizon", color="#666", fontsize=9)
    ax.set_xlabel("")
    ax.set_ylabel("Years to critical stress (basin < 20%)")
    ax.set_title("Time to critical basin stress across scenarios (n = 50 per scenario)")
    fig.savefig(FIGURES_DIR / "fig_time_to_stress.png")
    plt.close(fig)


def fig_tipping_point(out: dict) -> None:
    """Detail plot of a representative scenario-A run with the 40% crossing
    annotated. Shows the pre- and post-crossing slopes."""
    h2 = out["_h2_plot"]
    ticks = np.array(h2["ticks"])
    basin = np.array(h2["basin_frac"]) * 100.0
    years = ticks / 365.0
    cross_tick = h2["cross_tick"]
    cross_year = cross_tick / 365.0
    s_pre = h2["s_pre"] * 365.0 * 100.0     # %/year
    s_post = h2["s_post"] * 365.0 * 100.0   # %/year

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(years, basin, color="#777", linewidth=1.2, label="simulated basin level")

    # Pre slope line
    pre_mask = (ticks >= cross_tick - 200) & (ticks < cross_tick)
    if pre_mask.any():
        x_pre = years[pre_mask]
        intercept_pre = 40.0 - s_pre * cross_year
        ax.plot(
            x_pre, s_pre * x_pre + intercept_pre,
            color=PALETTE["A_unregulated"], linestyle="--", linewidth=2.2,
            label=f"pre-crossing slope: {s_pre:+.1f} %/yr",
        )
    post_mask = (ticks >= cross_tick) & (ticks < cross_tick + 200)
    if post_mask.any():
        x_post = years[post_mask]
        intercept_post = 40.0 - s_post * cross_year
        ax.plot(
            x_post, s_post * x_post + intercept_post,
            color="#7B1A18", linestyle="--", linewidth=2.2,
            label=f"post-crossing slope: {s_post:+.1f} %/yr",
        )

    ax.axhline(40, color="#bbb", linestyle=":", linewidth=1)
    ax.axhline(20, color="#bbb", linestyle="--", linewidth=1)
    ax.text(0.2, 22, "critical (20%)", color="#666", fontsize=9)
    ax.text(0.2, 42, "stress threshold (40%)", color="#666", fontsize=9)
    ax.scatter([cross_year], [40], color="#222", s=80, zorder=5)
    ax.annotate(
        f"40% crossing\nyear {cross_year:.1f}",
        xy=(cross_year, 40),
        xytext=(cross_year + 0.6, 50),
        fontsize=10,
        arrowprops=dict(arrowstyle="-", color="#222", lw=1.0),
    )
    ax.set_xlabel("Simulated years")
    ax.set_ylabel("Basin level (%)")
    accel = out["H2"]["median_rate_ratio_post_over_pre"]
    pre_rate = out["H2"]["median_pre_rate_per_year"] * 100
    post_rate = out["H2"]["median_post_rate_per_year"] * 100
    ax.set_title(
        f"Tipping point: basin loses {pre_rate:.1f}% / yr before the 40% crossing, "
        f"{post_rate:.1f}% / yr after ({accel:.1f}x faster)"
    )
    ax.legend(loc="lower left", frameon=False)
    ax.set_ylim(0, 100)
    fig.savefig(FIGURES_DIR / "fig_tipping_point.png")
    plt.close(fig)


def fig_scenario_compare(df: pd.DataFrame) -> None:
    """Small-multiples: 4 metrics x 4 scenarios."""
    metrics = [
        ("time_to_critical_stress", "Years to critical stress", lambda v: v / 365.0),
        ("farm_yield_loss_mean", "Farm yield loss (frac)", lambda v: v),
        ("community_complaints", "Community complaints (days < 40%)", lambda v: v),
        ("dc_total_capacity_ml_final", "Final DC capacity (ML/day)", lambda v: v),
    ]
    fig, axes = plt.subplots(2, 2, figsize=(11, 8))
    for ax, (col, title, transform) in zip(axes.flat, metrics):
        data = df.copy()
        data[col] = transform(data[col])
        sns.boxplot(
            data=data,
            x="scenario",
            y=col,
            order=SCENARIOS,
            palette=[PALETTE[s] for s in SCENARIOS],
            ax=ax,
            showfliers=False,
            width=0.55,
        )
        ax.set_xticklabels(
            [SCENARIO_LABELS[s].split(".")[0] for s in SCENARIOS]
        )
        ax.set_xlabel("")
        ax.set_ylabel("")
        ax.set_title(title, fontsize=11)
    fig.suptitle("Outcomes across the four scenarios (n = 50 per scenario)", fontsize=13, y=1.0)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "fig_scenario_compare.png")
    plt.close(fig)


def fig_yield_loss(df: pd.DataFrame) -> None:
    """Distribution of agricultural yield loss per scenario."""
    fig, ax = plt.subplots(figsize=(8, 5))
    for s in SCENARIOS:
        sub = df[df["scenario"] == s]
        sns.kdeplot(
            sub["farm_yield_loss_mean"],
            ax=ax,
            color=PALETTE[s],
            linewidth=2,
            label=SCENARIO_LABELS[s],
            common_norm=False,
            clip=(0, 1),
            bw_adjust=0.5,
        )
    ax.set_xlabel("Agricultural yield loss (fraction of initial area)")
    ax.set_ylabel("Density")
    ax.set_title("Farms absorb the externality")
    ax.legend(frameon=False)
    fig.savefig(FIGURES_DIR / "fig_yield_loss.png")
    plt.close(fig)


def fig_simulation_screenshot() -> None:
    """A schematic 'screenshot' of the model setup. Annotated diagram showing
    the four agent types and their interaction through the shared basin."""
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.patch.set_facecolor("#0B1426")
    ax.set_facecolor("#0B1426")

    # Basin in the centre
    basin = plt.Rectangle((3.5, 1.5), 3.0, 1.8, facecolor="#3EE6C5", alpha=0.5, edgecolor="#3EE6C5", lw=2)
    ax.add_patch(basin)
    ax.text(5.0, 2.4, "Shared\nWater Basin\n30 BL", ha="center", va="center",
            color="#0B1426", fontsize=13, fontweight="bold")

    # Data centres (top)
    for i, x in enumerate([1.0, 2.4, 7.6, 9.0]):
        ax.add_patch(plt.Rectangle((x - 0.5, 4.5), 1.0, 0.6, facecolor="#264C9E", edgecolor="#A6C0EC", lw=1.5))
        ax.text(x, 4.8, f"DC{i+1}", ha="center", va="center", color="white", fontsize=9, fontweight="bold")
        ax.annotate("", xy=(5.0, 3.35), xytext=(x, 4.5),
                    arrowprops=dict(arrowstyle="->", color="#A6C0EC", lw=1.2, alpha=0.6))

    # Community (left)
    ax.add_patch(plt.Circle((1.0, 2.5), 0.55, facecolor="#7E5BB0", edgecolor="white", lw=1.2))
    ax.text(1.0, 2.5, "Residents\n100k", ha="center", va="center", color="white", fontsize=8)
    ax.annotate("", xy=(3.45, 2.4), xytext=(1.55, 2.5),
                arrowprops=dict(arrowstyle="->", color="white", lw=1.2, alpha=0.6))

    # Farms (right)
    for i, y in enumerate([3.4, 1.6]):
        ax.add_patch(plt.Polygon([(8.5, y - 0.3), (9.5, y - 0.3), (9.0, y + 0.3)],
                                  facecolor="#5B8C3E", edgecolor="white", lw=1.0))
        ax.text(9.0, y - 0.55, f"Farm{i+1}", ha="center", va="top", color="white", fontsize=8)
        ax.annotate("", xy=(6.55, 2.4), xytext=(8.5, y),
                    arrowprops=dict(arrowstyle="->", color="white", lw=1.2, alpha=0.6))

    # Regulator (bottom)
    ax.add_patch(plt.Rectangle((4.3, 0.3), 1.4, 0.55, facecolor="#D9514E", edgecolor="white", lw=1.2))
    ax.text(5.0, 0.575, "Regulator", ha="center", va="center", color="white", fontsize=9, fontweight="bold")
    ax.annotate("", xy=(2.0, 4.5), xytext=(4.3, 0.6),
                arrowprops=dict(arrowstyle="-|>", color="#D9514E", lw=1.0, alpha=0.7, linestyle="--"))
    ax.annotate("", xy=(8.0, 4.5), xytext=(5.7, 0.6),
                arrowprops=dict(arrowstyle="-|>", color="#D9514E", lw=1.0, alpha=0.7, linestyle="--"))

    # Recharge arrow into basin
    ax.annotate("", xy=(5.0, 3.4), xytext=(5.0, 5.6),
                arrowprops=dict(arrowstyle="->", color="#3EE6C5", lw=2.0, alpha=0.7))
    ax.text(5.3, 4.7, "natural recharge\n50 +/- 25 ML/day", color="#3EE6C5", fontsize=9)

    ax.text(0.5, 5.7, "PARCHED model schematic", color="white", fontsize=14, fontweight="bold")
    ax.text(0.5, 0.0, "All interaction mediated through the basin. Operators are blind to one another.",
            color="#9FA6B2", fontsize=8, style="italic")

    fig.savefig(FIGURES_DIR / "fig_simulation_screenshot.png", facecolor="#0B1426")
    plt.close(fig)


# -------------------------------------------------------------------------
# Main
# -------------------------------------------------------------------------

def main() -> None:
    df = load_all_runs()
    out: dict = {}
    test_h1_unsustainable(df, out)
    test_h2_tipping_point(out, df)
    test_h3_policy(df, out)

    # Strip internal plot data before writing
    plot_data = out.pop("_h2_plot")
    with (RESULTS_DIR / "hypothesis_tests.json").open("w") as f:
        json.dump(out, f, indent=2)
    out["_h2_plot"] = plot_data

    print("=== Hypothesis tests ===")
    for h, v in out.items():
        if h.startswith("_"):
            continue
        print(f"\n{h}:")
        for k, val in v.items():
            print(f"  {k:35s} {val}")

    # Figures
    fig_basin_timeseries()
    fig_time_to_stress(df)
    fig_tipping_point(out)
    fig_scenario_compare(df)
    fig_yield_loss(df)
    fig_simulation_screenshot()
    print(f"\nFigures written to {FIGURES_DIR}")


if __name__ == "__main__":
    main()
