"""
Scenario factories for PARCHED.

Each function returns a SimConfig with the right policy mode and parameters.
The seed is the only thing that varies across replicates within a scenario.
"""

from __future__ import annotations

from parched_model import SimConfig


def scenario_A_unregulated(seed: int) -> SimConfig:
    """A: Unregulated growth. No regulator action. Baseline collapse trajectory."""
    return SimConfig(
        policy_mode="off",
        seed=seed,
        label="A_unregulated",
    )


def scenario_B_reactive(seed: int) -> SimConfig:
    """B: Reactive regulation. Cap kicks in after delay once basin < 30%."""
    return SimConfig(
        policy_mode="reactive",
        seed=seed,
        label="B_reactive",
    )


def scenario_C_proactive(seed: int) -> SimConfig:
    """C: Proactive water budget. Industrial draw hard-capped from t=0."""
    return SimConfig(
        policy_mode="proactive",
        seed=seed,
        label="C_proactive",
        # Cap total DC draw at 15 ML/day from the start, well below the
        # ~50 ML/day recharge mean. Expansion can still happen but the
        # combined output is throttled.
        proactive_industrial_budget_ml=15.0,
    )


def scenario_D_staggered(seed: int) -> SimConfig:
    """D: Staggered entry. DCs come online at year 0, 2, 4 instead of all at t=0."""
    return SimConfig(
        policy_mode="staggered",
        seed=seed,
        label="D_staggered",
        num_data_centers=4,
        # 4 DCs entering at years 0, 2, 4, 6 (in ticks)
        staggered_entry_ticks=(0, 730, 1460, 2190),
    )


ALL_SCENARIOS = {
    "A_unregulated": scenario_A_unregulated,
    "B_reactive": scenario_B_reactive,
    "C_proactive": scenario_C_proactive,
    "D_staggered": scenario_D_staggered,
}
