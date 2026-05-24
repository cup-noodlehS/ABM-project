"""
PARCHED: When AI Drinks Your Town Dry.
Agent-Based Model of data centers, communities, agriculture and a regulator
competing for a shared water basin.

CMSC 176 Final Project. Authors: Sheldon Arthur Sagrado, Jed Edison Donaire.

Units
-----
- Tick: 1 day
- Water volumes: megalitres (ML). 1 ML = 1 million liters = 1000 cubic meters.
- Basin capacity: 1 BL = 1000 ML.
- Energy: MW (electrical capacity of a data center).

All parameter ranges are synthetic but grounded in the cited literature
(Li et al. 2023; Shehabi et al. 2016; Mekonnen & Hoekstra 2016).
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Optional

import mesa


# -------------------------------------------------------------------------
# Configuration dataclass
# -------------------------------------------------------------------------

@dataclass
class SimConfig:
    """Bundle of parameters that fully define a model run."""

    # Time
    max_ticks: int = 3650           # 10 simulated years
    seed: int = 42

    # Basin (calibrated so unregulated scenario hits critical at 5-8 years)
    basin_capacity_ml: float = 30_000.0          # 30 BL
    basin_initial_frac: float = 0.80
    recharge_mean_ml_per_day: float = 50.0       # mid-stress aquifer
    recharge_amplitude_ml: float = 25.0          # seasonal swing
    recharge_phase_shift: float = 90.0           # peak recharge in wet season
    critical_frac: float = 0.20                  # irreversible damage zone
    stress_frac: float = 0.40                    # complaint trigger; nonlinear recharge below here
    # Below stress_frac, recharge efficiency collapses: real aquifers lose
    # surface-water connection at low levels and the recharge rate falls
    # sharply. This is half the H2 mechanism. 0.10 = 90% reduction.
    nonlinear_recharge_penalty: float = 0.05
    # Daily extraction is also capped by hydraulic capacity. We use
    # max(recharge*2, basin_level * level_to_flow_rate). Above ~30% basin this
    # constraint is non-binding; below it, the basin can no longer sustain
    # peak draws and the lowest-priority users (farms) get rationed.
    level_to_flow_rate: float = 0.012

    # Data center operators (2-4 ML/day base per the proposal teaser).
    # Capacity expands on a fixed semi-annual cadence driven by exogenous compute
    # demand growth, not by water-delivery utilization. Operators are blind to
    # basin state; only the regulator (Scenarios B/C) can throttle them.
    num_data_centers: int = 4
    dc_base_draw_ml_min: float = 1.5
    dc_base_draw_ml_max: float = 3.0
    dc_expansion_step_ml: float = 1.0
    dc_expansion_budget: int = 10                # max expansion events per DC
    dc_expansion_interval: int = 270             # ticks between expansion attempts (~9 months)

    # Temperature / seasonal cooling load
    temp_amplitude: float = 0.40                 # +/- 40% draw modulation
    temp_phase_shift: float = -90.0              # peak draw at ~tick 270 (summer)
    # Cooling-stress feedback: when the basin is depleted, intake water is
    # warmer (less thermal mass), so DCs need more water per MW of compute.
    # This is a positive feedback that creates the H2 tipping point.
    cooling_stress_amplification: float = 4.0    # at basin_frac = 0, demand x (1 + amp)

    # Residential community
    community_population: int = 100_000
    community_l_per_capita_per_day: float = 150.0
    community_stress_tolerance_days: int = 30

    # Agricultural users (1.5 mm/day low-water crops / drip irrigation)
    num_farms: int = 2
    farm_area_ha_min: float = 500.0
    farm_area_ha_max: float = 1500.0
    farm_l_per_ha_dry_season: float = 15_000.0   # ~1.5 mm/day
    farm_l_per_ha_wet_season: float = 1_500.0    # mostly rain-fed
    farm_sustained_cut_days: int = 30
    farm_downsize_factor: float = 0.5            # halves area on permanent cut

    # Regulator
    policy_mode: str = "off"                     # off | reactive | proactive | staggered
    regulator_trigger_frac: float = 0.30
    regulator_delay_min: int = 30                # 1 month delay
    regulator_delay_max: int = 120               # 4 months delay
    regulator_cap_severity: float = 0.40         # cap industrial draw to 1 - severity
    proactive_industrial_budget_ml: float = 15.0 # daily DC total ceiling for Scenario C

    # Staggered entry (Scenario D)
    staggered_entry_ticks: tuple = (0, 730, 1460)  # year 0, 2, 4

    # Bookkeeping
    label: str = "default"


# -------------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------------

def seasonal_factor(tick: int, phase_shift: float = 0.0) -> float:
    """Return a number in [-1, 1] cycling once per simulated year."""
    return math.sin(2 * math.pi * (tick + phase_shift) / 365.0)


def temperature_multiplier(tick: int, cfg: SimConfig) -> float:
    """Multiplier applied to data-center cooling draw. Peaks in summer."""
    return 1.0 + cfg.temp_amplitude * seasonal_factor(tick, cfg.temp_phase_shift)


def seasonal_recharge(tick: int, cfg: SimConfig, basin_frac: float) -> float:
    """Recharge in ML/day, sinusoidal around the mean. Peaks in wet season.
    Applies a nonlinear penalty when basin is below the stress fraction: real
    aquifers lose surface-water connection and recharge efficiency drops once
    levels fall too low."""
    base = cfg.recharge_mean_ml_per_day + cfg.recharge_amplitude_ml * seasonal_factor(
        tick, cfg.recharge_phase_shift
    )
    if basin_frac < cfg.stress_frac:
        base *= cfg.nonlinear_recharge_penalty
    return max(0.0, base)


def farm_demand_per_ha(tick: int, cfg: SimConfig) -> float:
    """Per-hectare demand in L/day. Peaks in dry season (same as DC cooling)."""
    midpoint = (cfg.farm_l_per_ha_dry_season + cfg.farm_l_per_ha_wet_season) / 2.0
    half_range = (cfg.farm_l_per_ha_dry_season - cfg.farm_l_per_ha_wet_season) / 2.0
    return midpoint + half_range * seasonal_factor(tick, cfg.temp_phase_shift)


# -------------------------------------------------------------------------
# Agents
# -------------------------------------------------------------------------

class DataCenterOperator(mesa.Agent):
    """A hyperscaler operator. Knows only its own compute demand growth."""

    def __init__(self, model: "ParchedModel", base_draw_ml: float) -> None:
        super().__init__(model)
        self.base_draw_ml = base_draw_ml
        self.current_capacity_ml = base_draw_ml
        self.expansions_used = 0
        self.expansion_budget = model.cfg.dc_expansion_budget
        self.requested_today = 0.0
        self.received_today = 0.0
        self.entry_tick = 0           # when the DC starts operating
        self.active = True

    def request_draw(self, tick: int) -> float:
        """How much water the DC tries to consume this tick."""
        if not self.active or tick < self.entry_tick:
            self.requested_today = 0.0
            return 0.0
        load = temperature_multiplier(tick, self.model.cfg)
        # Cooling-stress feedback. Above the stress threshold this multiplier
        # is exactly 1; below it, intake water gets warmer and per-MW water
        # demand rises, creating positive feedback into basin depletion.
        cfg = self.model.cfg
        basin_frac = self.model.basin_fraction()
        if basin_frac < cfg.stress_frac:
            shortfall = (cfg.stress_frac - basin_frac) / cfg.stress_frac
            load *= 1.0 + cfg.cooling_stress_amplification * shortfall
        self.requested_today = self.current_capacity_ml * load
        return self.requested_today

    def maybe_expand(self, tick: int) -> None:
        """Expand on the configured cadence, blind to basin state."""
        cfg = self.model.cfg
        if not self.active or tick < self.entry_tick:
            return
        if self.expansions_used >= self.expansion_budget:
            return
        ticks_since_entry = tick - self.entry_tick
        if ticks_since_entry > 0 and ticks_since_entry % cfg.dc_expansion_interval == 0:
            if self.model.expansion_allowed(self):
                self.current_capacity_ml += cfg.dc_expansion_step_ml
                self.expansions_used += 1

    def settle(self, received: float, tick: int) -> None:
        """Record delivery. Capacity decisions are made independently."""
        self.received_today = received


class ResidentialCommunity(mesa.Agent):
    """Aggregate community. Generates complaints when basin is stressed."""

    def __init__(self, model: "ParchedModel") -> None:
        super().__init__(model)
        cfg = model.cfg
        self.daily_need_ml = cfg.community_population * cfg.community_l_per_capita_per_day / 1_000_000.0
        self.shortage_streak = 0
        self.complaints = 0
        self.received_today = 0.0
        self.requested_today = 0.0
        self.cumulative_shortage_days = 0

    def request_draw(self, tick: int) -> float:
        self.requested_today = self.daily_need_ml
        return self.daily_need_ml

    def settle(self, received: float, tick: int) -> None:
        self.received_today = received
        if received < 0.95 * self.daily_need_ml:
            self.shortage_streak += 1
            self.cumulative_shortage_days += 1
        else:
            self.shortage_streak = 0
        if self.model.basin_fraction() < self.model.cfg.stress_frac:
            self.complaints += 1


class AgriculturalUser(mesa.Agent):
    """Irrigation user. Permanently downsizes after sustained cuts."""

    def __init__(self, model: "ParchedModel", area_ha: float) -> None:
        super().__init__(model)
        self.initial_area_ha = area_ha
        self.current_area_ha = area_ha
        self.shortage_streak = 0
        self.received_today = 0.0
        self.requested_today = 0.0
        self.cumulative_shortage_days = 0
        self.yield_loss = 0.0   # fraction permanently lost

    def request_draw(self, tick: int) -> float:
        l_per_ha = farm_demand_per_ha(tick, self.model.cfg)
        need_ml = self.current_area_ha * l_per_ha / 1_000_000.0
        self.requested_today = need_ml
        return need_ml

    def settle(self, received: float, tick: int) -> None:
        self.received_today = received
        if self.requested_today <= 0:
            return
        ratio = received / self.requested_today
        if ratio < 0.9:
            self.shortage_streak += 1
            self.cumulative_shortage_days += 1
        else:
            self.shortage_streak = 0
        if self.shortage_streak >= self.model.cfg.farm_sustained_cut_days:
            downsize = self.model.cfg.farm_downsize_factor
            self.yield_loss += (1.0 - downsize) * (self.current_area_ha / self.initial_area_ha)
            self.current_area_ha *= downsize
            self.shortage_streak = 0


class Regulator(mesa.Agent):
    """The slow, bureaucratic policy actor."""

    def __init__(self, model: "ParchedModel") -> None:
        super().__init__(model)
        self.mode = model.cfg.policy_mode
        self.active_cap = False         # is a reactive cap currently in force?
        self.cap_severity = 0.0
        self.delay_remaining: Optional[int] = None
        self.pending_action: Optional[str] = None

    def step(self, tick: int) -> None:
        cfg = self.model.cfg
        basin_frac = self.model.basin_fraction()

        if self.mode == "reactive":
            if not self.active_cap and basin_frac < cfg.regulator_trigger_frac:
                if self.delay_remaining is None:
                    self.delay_remaining = self.model.rng.randint(
                        cfg.regulator_delay_min, cfg.regulator_delay_max
                    )
                    self.pending_action = "impose_cap"
                else:
                    self.delay_remaining -= 1
                    if self.delay_remaining <= 0 and self.pending_action == "impose_cap":
                        self.active_cap = True
                        self.cap_severity = cfg.regulator_cap_severity
                        self.delay_remaining = None
                        self.pending_action = None
            if self.active_cap and basin_frac > cfg.regulator_trigger_frac + 0.10:
                # relax cap once basin recovers
                self.active_cap = False
                self.cap_severity = 0.0


# -------------------------------------------------------------------------
# The Model
# -------------------------------------------------------------------------

class ParchedModel(mesa.Model):
    """Shared-basin ABM. Agents draw water; the basin recharges seasonally."""

    def __init__(self, cfg: Optional[SimConfig] = None) -> None:
        self.cfg = cfg or SimConfig()
        super().__init__(rng=self.cfg.seed)        # mesa wants an int / seedseq
        self.rng = random.Random(self.cfg.seed)    # separate stdlib RNG for our logic

        # Basin state
        self.basin_capacity_ml = self.cfg.basin_capacity_ml
        self.basin_level_ml = self.basin_capacity_ml * self.cfg.basin_initial_frac
        self.critical_reached_at: Optional[int] = None
        self.tick = 0

        # Industrial-budget tracking (Scenario C)
        self.industrial_budget_remaining = self.cfg.proactive_industrial_budget_ml

        # Spawn agents
        self.data_centers: list[DataCenterOperator] = []
        for i in range(self.cfg.num_data_centers):
            draw = self.rng.uniform(self.cfg.dc_base_draw_ml_min, self.cfg.dc_base_draw_ml_max)
            dc = DataCenterOperator(self, base_draw_ml=draw)
            if self.cfg.policy_mode == "staggered":
                entry = self.cfg.staggered_entry_ticks[i % len(self.cfg.staggered_entry_ticks)]
                dc.entry_tick = entry
            self.data_centers.append(dc)

        self.community = ResidentialCommunity(self)
        self.farms: list[AgriculturalUser] = []
        for _ in range(self.cfg.num_farms):
            area = self.rng.uniform(self.cfg.farm_area_ha_min, self.cfg.farm_area_ha_max)
            self.farms.append(AgriculturalUser(self, area_ha=area))
        self.regulator = Regulator(self)

        # Per-tick history
        self.history: list[dict] = []

    # ---- helpers ---------------------------------------------------------

    def basin_fraction(self) -> float:
        return self.basin_level_ml / self.basin_capacity_ml

    def expansion_allowed(self, dc: DataCenterOperator) -> bool:
        """Used by Scenario C (proactive water budget)."""
        if self.cfg.policy_mode != "proactive":
            return True
        proposed_total = sum(d.current_capacity_ml for d in self.data_centers) + self.cfg.dc_expansion_step_ml
        return proposed_total <= self.cfg.proactive_industrial_budget_ml * 1.5

    # ---- main step -------------------------------------------------------

    def step(self) -> None:
        cfg = self.cfg
        tick = self.tick

        # 1. Each agent computes its request
        dc_requests = [dc.request_draw(tick) for dc in self.data_centers]
        community_request = self.community.request_draw(tick)
        farm_requests = [f.request_draw(tick) for f in self.farms]

        # 2. Apply regulatory cap on industrial draw if active
        cap_factor = 1.0
        if self.regulator.mode == "reactive" and self.regulator.active_cap:
            cap_factor = 1.0 - self.regulator.cap_severity
        elif self.regulator.mode == "proactive":
            # hard ceiling on total industrial draw
            total_dc = sum(dc_requests)
            if total_dc > cfg.proactive_industrial_budget_ml:
                cap_factor = cfg.proactive_industrial_budget_ml / total_dc
        dc_requests_effective = [r * cap_factor for r in dc_requests]

        total_request = sum(dc_requests_effective) + community_request + sum(farm_requests)

        # 3. Determine how much is actually delivered.
        # Priority (commercial water-rights pattern): community first (essential),
        # then DCs (contracted commercial users), farms last. Daily flow is
        # capped by hydraulic capacity = max(recharge, basin_level * rate),
        # so as the basin drops, peak-demand days force rationing onto farms.
        basin_frac_now = self.basin_fraction()
        recharge_now = seasonal_recharge(tick, cfg, basin_frac_now)
        flow_cap = max(recharge_now * 2.0, self.basin_level_ml * cfg.level_to_flow_rate)
        available = min(self.basin_level_ml, flow_cap)

        community_received = min(community_request, available)
        available -= community_received

        if sum(dc_requests_effective) > 0 and available > 0:
            total_dc = sum(dc_requests_effective)
            if available >= total_dc:
                dc_received = list(dc_requests_effective)
                available -= total_dc
            else:
                share = available / total_dc
                dc_received = [r * share for r in dc_requests_effective]
                available = 0.0
        else:
            dc_received = [0.0 for _ in dc_requests_effective]

        farm_received = []
        for req in farm_requests:
            take = min(req, available)
            farm_received.append(take)
            available -= take

        # 4. Update basin
        total_taken = community_received + sum(farm_received) + sum(dc_received)
        self.basin_level_ml -= total_taken
        self.basin_level_ml += seasonal_recharge(tick, cfg, self.basin_fraction())
        self.basin_level_ml = max(0.0, min(self.basin_capacity_ml, self.basin_level_ml))

        # 5. Let agents settle (track shortages, downsize on persistent cuts)
        for dc, recv in zip(self.data_centers, dc_received):
            dc.settle(recv, tick)
        self.community.settle(community_received, tick)
        for farm, recv in zip(self.farms, farm_received):
            farm.settle(recv, tick)
        self.regulator.step(tick)

        # 6. DCs evaluate quarterly expansion (driven by exogenous compute demand)
        for dc in self.data_centers:
            dc.maybe_expand(tick)

        # 7. Track critical-stress event
        if self.critical_reached_at is None and self.basin_fraction() < cfg.critical_frac:
            self.critical_reached_at = tick

        # 8. Record per-tick metrics
        self.history.append(
            {
                "tick": tick,
                "basin_frac": self.basin_fraction(),
                "basin_level_ml": self.basin_level_ml,
                "dc_total_draw_ml": sum(dc_received),
                "community_received_ml": community_received,
                "farm_total_received_ml": sum(farm_received),
                "community_complaints": self.community.complaints,
                "active_cap": int(self.regulator.active_cap),
                "total_dc_capacity_ml": sum(dc.current_capacity_ml for dc in self.data_centers),
            }
        )

        self.tick += 1

    def run(self) -> None:
        for _ in range(self.cfg.max_ticks):
            self.step()
            if self.critical_reached_at is not None and self.basin_fraction() < 0.05:
                # bottom of the basin, stop early
                break

    # ---- output summary --------------------------------------------------

    def summary(self) -> dict:
        return {
            "label": self.cfg.label,
            "seed": self.cfg.seed,
            "policy_mode": self.cfg.policy_mode,
            "num_data_centers": self.cfg.num_data_centers,
            "time_to_critical_stress": self.critical_reached_at if self.critical_reached_at is not None else self.cfg.max_ticks,
            "final_basin_frac": self.basin_fraction(),
            "community_complaints": self.community.complaints,
            "community_shortage_days": self.community.cumulative_shortage_days,
            "farm_yield_loss_mean": sum(f.yield_loss for f in self.farms) / max(len(self.farms), 1),
            "farm_shortage_days_total": sum(f.cumulative_shortage_days for f in self.farms),
            "dc_total_expansions": sum(dc.expansions_used for dc in self.data_centers),
            "dc_total_capacity_ml_final": sum(dc.current_capacity_ml for dc in self.data_centers),
            "ticks_run": self.tick,
        }


if __name__ == "__main__":
    # Smoke test: one default run, print summary
    cfg = SimConfig(label="smoke_test", seed=1)
    model = ParchedModel(cfg)
    model.run()
    summary = model.summary()
    print("Smoke test (default config, seed=1):")
    for k, v in summary.items():
        print(f"  {k:40s} {v}")
