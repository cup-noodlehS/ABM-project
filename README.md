# PARCHED: When AI Drinks Your Town Dry

An agent-based model of hyperscaler water competition in a shared basin.

- **Course:** CMSC 176 (Agent-Based Modeling), AY 2025–2026, University of the Philippines Cebu
- **Authors:** Sheldon Arthur Sagrado, Jed Edison Donaire (equal contribution)
- **Stack:** Python 3.12, Mesa 3.x, NumPy, SciPy, Pandas, Matplotlib, python-pptx

## Repository layout

```
release/
├── model/                          # simulation code
│   ├── parched_model.py            # Mesa Model + agent classes
│   ├── scenarios.py                # 4 scenario factories (A/B/C/D)
│   ├── run_batch.py                # batch runner: 4 scenarios x 50 runs
│   ├── analyze.py                  # statistical tests + figure generation
│   ├── requirements.txt
│   └── README.md
├── results/                        # CSV output (one file per scenario, plus summary)
│   ├── scenario_A_unregulated_runs.csv
│   ├── scenario_B_reactive_runs.csv
│   ├── scenario_C_proactive_runs.csv
│   ├── scenario_D_staggered_runs.csv
│   ├── scenario_*_history_seed*.csv  # per-tick traces (all 50 for A, seed 0 for others)
│   ├── summary_stats.csv
│   └── hypothesis_tests.json
├── figures/                        # publication PNGs (used by paper and deck)
│   ├── fig_basin_timeseries.png
│   ├── fig_time_to_stress.png
│   ├── fig_tipping_point.png
│   ├── fig_scenario_compare.png
│   ├── fig_yield_loss.png
│   └── fig_simulation_screenshot.png
├── paper/                          # ACM sigconf LaTeX paper
│   ├── main.tex
│   ├── refs.bib
│   ├── main.pdf                    # compiled output
│   └── (ACM template files)
└── presentation/
    ├── build_deck.py
    └── PARCHED_final.pptx
```

## Reproduce the results

### 1. Set up the Python environment

```bash
cd release/model
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Run the batch (4 scenarios, 50 runs each)

```bash
python run_batch.py 50
```

Wall time on a 2024 M-series laptop: ~3 minutes. Writes everything into `release/results/`.

### 3. Generate figures and run hypothesis tests

```bash
python analyze.py
```

Writes 6 PNGs into `release/figures/` and `release/results/hypothesis_tests.json` with the full statistical results.

### 4. Compile the paper

```bash
cd ../paper
latexmk -pdf main.tex
```

Produces `main.pdf`.

### 5. Rebuild the deck (optional, the .pptx is already in the repo)

```bash
cd ../presentation
python build_deck.py
```

## Headline results

| Hypothesis | Claim | Result | p |
| --- | --- | --- | --- |
| **H1** | Unregulated growth collapses the basin in 5–8 yr | 100% of runs collapse, mean 6.07 ± 0.84 yr | < 10⁻²¹ |
| **H2** | Decline accelerates near the 40% threshold | 9.25× faster post-crossing (0.07/yr → 0.66/yr) | < 10⁻⁷⁴ |
| **H3** | A proactive cap delays collapse by ≥40% | C delays by 65% vs A (10.0 yr vs 6.07 yr) | < 10⁻³⁵ |

Side finding: scenarios A (unregulated) and B (reactive cap at 30% basin) produced statistically identical outcomes. By the time the reactive trigger fires, the cooling-stress feedback has already locked in the collapse. A 30%-threshold reactive policy is functionally equivalent to no policy at all.

## Repository

GitHub: [`cup-noodlehS/ABM-project`](https://github.com/cup-noodlehS/ABM-project)
