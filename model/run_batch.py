"""
Batch runner: 4 scenarios x 50 runs.

Outputs:
- release/results/scenario_<X>_runs.csv    : summary metrics per run
- release/results/scenario_<X>_history_seed0.csv : full per-tick trace for first seed (visual)
- release/results/summary_stats.csv        : aggregated stats per scenario
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import pandas as pd

from parched_model import ParchedModel
from scenarios import ALL_SCENARIOS


def run_one(cfg_factory, seed: int) -> tuple[dict, list[dict]]:
    cfg = cfg_factory(seed)
    model = ParchedModel(cfg)
    model.run()
    summary = model.summary()
    history = model.history
    return summary, history


def run_scenario(name: str, factory, n_runs: int, results_dir: Path, save_history_for: tuple[int, ...] = (0,)) -> pd.DataFrame:
    print(f"\n=== Scenario {name}: {n_runs} runs ===")
    rows = []
    t0 = time.time()
    for i in range(n_runs):
        seed = i  # seed 0..n_runs-1 for reproducibility
        summary, history = run_one(factory, seed)
        rows.append(summary)
        if seed in save_history_for:
            hist_df = pd.DataFrame(history)
            hist_df.to_csv(results_dir / f"scenario_{name}_history_seed{seed}.csv", index=False)
        if (i + 1) % 10 == 0:
            elapsed = time.time() - t0
            print(f"  ...{i+1}/{n_runs} done ({elapsed:.1f}s)")
    df = pd.DataFrame(rows)
    out = results_dir / f"scenario_{name}_runs.csv"
    df.to_csv(out, index=False)
    print(f"  wrote {out} ({len(df)} rows, {time.time()-t0:.1f}s total)")
    return df


def main(n_runs: int = 50) -> None:
    repo_root = Path(__file__).resolve().parent.parent
    results_dir = repo_root / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    all_summaries = {}
    for name, factory in ALL_SCENARIOS.items():
        # Save all histories for A (needed for the H2 tipping-point test) plus
        # the seed-0 history of every other scenario for the figure.
        if name == "A_unregulated":
            save_seeds = tuple(range(n_runs))
        else:
            save_seeds = (0,)
        df = run_scenario(name, factory, n_runs, results_dir, save_history_for=save_seeds)
        all_summaries[name] = df

    # Aggregate stats per scenario
    summary_rows = []
    for name, df in all_summaries.items():
        ttc = df["time_to_critical_stress"]
        summary_rows.append(
            {
                "scenario": name,
                "n_runs": len(df),
                "mean_time_to_critical_ticks": ttc.mean(),
                "median_time_to_critical_ticks": ttc.median(),
                "std_time_to_critical_ticks": ttc.std(),
                "mean_time_to_critical_years": ttc.mean() / 365.0,
                "median_time_to_critical_years": ttc.median() / 365.0,
                "frac_reaching_critical": (ttc < 3650).mean(),
                "mean_final_basin_frac": df["final_basin_frac"].mean(),
                "mean_farm_yield_loss": df["farm_yield_loss_mean"].mean(),
                "mean_community_complaints": df["community_complaints"].mean(),
                "mean_dc_capacity_final": df["dc_total_capacity_ml_final"].mean(),
            }
        )
    summary_df = pd.DataFrame(summary_rows)
    summary_df.to_csv(results_dir / "summary_stats.csv", index=False)
    print("\n=== Summary across all scenarios ===")
    print(summary_df.to_string(index=False))


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 50
    main(n_runs=n)
