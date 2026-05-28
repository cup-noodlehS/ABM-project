---
title: PARCHED
emoji: 💧
colorFrom: blue
colorTo: red
sdk: docker
pinned: false
---

# PARCHED model

Mesa 3.x simulation of multiple data centers, residential users, farms, and a regulator sharing a single water basin.

## Files

- `parched_model.py` — `SimConfig` dataclass, agent classes (`DataCenterOperator`, `ResidentialCommunity`, `AgriculturalUser`, `Regulator`), and `ParchedModel` (the Mesa `Model`). All numeric parameters live in `SimConfig`.
- `scenarios.py` — four factory functions for scenarios A/B/C/D, plus an `ALL_SCENARIOS` registry.
- `run_batch.py` — runs all four scenarios with 50 replicate seeds each, writes per-run summary CSVs and full per-tick history CSVs to `../results/`.
- `analyze.py` — loads the CSVs, runs the H1/H2/H3 statistical tests, writes 6 figures to `../figures/` and the test report to `../results/hypothesis_tests.json`.

## Key parameters (defaults in `SimConfig`)

| Parameter | Default | Note |
| --- | --- | --- |
| `basin_capacity_ml` | 30 000 | 30 BL aquifer |
| `basin_initial_frac` | 0.80 | start at 80% |
| `basin_critical_frac` | 0.20 | stress threshold for time-to-critical |
| `basin_irreversible_frac` | 0.05 | sim halts here |
| `recharge_mean_ml_day` | 50 | sinusoidal seasonal recharge |
| `recharge_amplitude_ml_day` | 25 | |
| `cooling_stress_amplification` | 4.0 | positive-feedback multiplier on DC draw below stress threshold |
| `nonlinear_recharge_penalty` | 0.05 | aquifer disconnection below 30% basin |
| `num_data_centers` | 4 | |
| `dc_expansion_interval` | 270 ticks (~9 mo) | fixed schedule, exogenous compute growth |
| `community_population` | 100 000 | |
| `community_per_capita_l_day` | 150 | |
| `num_farms` | 2 | |
| `farm_water_l_per_ha_day` | 14 000 | growing-season demand |
| `farm_cut_days_to_fallback` | 30 | sustained cuts kill irrigated area |
| `reactive_basin_trigger_frac` | 0.30 | when reactive regulator activates |
| `reactive_response_delay_min_max` | (2, 4) | stochastic delay in days |
| `proactive_industrial_budget_ml` | 15 ML/day | for scenario C |
| `staggered_entry_ticks` | (0, 730, 1460, 2190) | scenario D entry calendar |
| `n_ticks` | 3650 | 10-year horizon |

## Allocation rule

Each tick:
1. Compute the day's natural recharge (sinusoidal + noise + nonlinear penalty if basin < 30%).
2. All agents register their requested draw for the day.
3. The basin's daily extraction cap is `max(2 * recharge, basin_level * 0.012)`.
4. Allocate available water in priority order: residential community → DC operators → farms.
5. Cut anything that can't be served. Track cut days for farms; convert sustained cuts (>30 days) into permanent area loss.

## Tipping-point mechanism

The nonlinearity comes from two coupled feedbacks:
- **Cooling-stress amplification.** DC water demand is the seasonal base load times `1 + 4 * (stress_frac - basin_frac) / stress_frac` when `basin_frac < stress_frac`. Hotter, dryer, lower water — all push the same direction.
- **Recharge penalty.** Below 30% basin, recharge multiplier decays linearly. The aquifer becomes harder to refill once it disconnects from surface flows.

The combined effect is a smooth pre-collapse phase (rate ~0.07/yr decline) and an abrupt post-40% collapse phase (rate ~0.66/yr).

## Reproducing the headline result

```bash
source .venv/bin/activate
python run_batch.py 50
python analyze.py
cat ../results/hypothesis_tests.json
```
