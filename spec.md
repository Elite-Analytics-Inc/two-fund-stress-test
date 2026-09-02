# Two-Fund Stress Test — specification

*The living source of truth for this analysis. Updated as decisions land.*

## What it does

Takes a two-fund portfolio of VTI (US total market) and VXUS (international ex-US) and shows how a
starting balance grows or shrinks over ten years, compounding yearly, under several market
scenarios and several allocation mixes. The dashboard shows exposure over the years: how much
money sits in each fund, and how much could be lost in a bad stretch.

## Decisions so far

- **Starting balance:** $1,000,000. No yearly contributions or withdrawals.
- **Horizon:** a forecast. Ten years forward from a start year (default 2026, a run parameter),
  compounding once a year. The dashboard labels calendar years 2026-2035.
- **Mixes compared (approved):** Yours 65/35, All US 100/0, US tilt 80/20, Even split 50/50,
  World tilt 35/65 (VTI/VXUS).
- **Rebalancing:** show both — rebalance to target once a year, and buy-and-hold with drift.
- **Project name:** Two-Fund Stress Test (approved).
- **Account type:** treated as a 401(k). No tax drag on dividends or growth.
- **Dividends:** reinvested. Every yearly return is a total return (price change plus dividends).
- **Scenarios:** anchored to real history (VTI ~10%/yr long run, VXUS ~5-6%/yr since 2011,
  2008: US about -37%, international about -44%). Proposed set: steady growth, crash in year 3,
  US stalls / world runs, world stalls / US runs, lost decade, plus a replay of the actual
  2016-2025 returns, read as "what if the next ten years look like the last ten".
- **Data approved** by the analyst (2026-09-02), including two deliberate rough edges: VOO has
  returns for the replay scenario only, and BND's dividend yield is blank.

- **Two funds at a time, chosen at run time.** Fund A and fund B are run parameters (today VTI
  and VXUS). The data is keyed by ticker so other ETFs can be added without changing code.
- **Every run exercises every scenario, every mix, both rebalancing modes, all ten years.**
- **Democratized dashboard (required):** a plain-words "what this is about" note, a glossary for
  every term of art, and an ⓘ on every chart and tile saying what it shows and how to judge it.

## Inputs — `data/lake/portfolio/`

| Table | Key | Columns |
|---|---|---|
| `funds` | ticker | name, region, launch year, dividend yield |
| `scenarios` | scenario_id | name, one-line description |
| `scenario_returns` | scenario_id + ticker + year | total return % for that fund, that year |
| `mixes` | mix_id | name, percent in fund A |

`scenario_returns` references `funds` (ticker) and `scenarios` (scenario_id). A fund is usable
only if it has ten rows for every scenario; the analysis checks this before running.

## Parameters (what varies per run)

| Parameter | What it means | Default | Bounds |
| --- | --- | --- | --- |
| `fund_a` | ticker of the first fund | VTI | must exist in `funds` |
| `fund_b` | ticker of the second fund | VXUS | must exist in `funds` |
| `starting_balance` | dollars invested on day one | 1,000,000 | > 0 |
| `start_year` | the first forecast year | 2026 | 2000-2100 |
| `horizon_years` | how many years forward | 10 | 1-10 (the data holds ten years per scenario) |

Before computing anything, the run checks that both funds have a return for every scenario and
every year in the horizon, and stops with a plain message naming the gap if not.

## The dashboard (agreed 2026-09-02; reshaped into chapters the same day)

A five-chapter binder with a sidebar, so each chapter is one screen: the controls on top and the
chart or table they change directly underneath. The analyst asked for this after finding that on
one long page you cannot see which chart a control changed.

| Chapter | File | What it holds |
| --- | --- | --- |
| Start here | `index.md` | intro, about, full glossary, controls, headline tiles, the range band, the six lines |
| Does the split matter? | `1_split_matters.md` | controls, five named splits in the chosen scenario |
| The full grid | `2_grid.md` | controls, ending-balance grid, effective-rate grid |
| Drift | `3_drift.md` | controls, fund A share by year if never rebalanced |
| The bad years | `4_bad_years.md` | controls, worst year / deepest fall / recovery / doubling |

**Known limitation (renderer):** controls restore from the web address only on first load, so
switching chapters puts the controls back to their defaults. Each chapter carries its own
control bar; a link with settings plus a chapter opens correctly. The intro says so plainly.

Written so a 12-year-old can follow it: a plain "about this page" note, a glossary of
every term, and an ⓘ on every tile and chart saying what it shows and how to judge it.
**No "average of the six scenarios" anywhere** — the analyst decided an equal-weight average of
hand-picked futures misleads more than it informs.

**Controls.** Each chapter shows only the controls that change it (the analyst's rule: every
control on a chapter must visibly do something), and the chart sits directly under them:

| Control | Kind | Default | Shown on |
| --- | --- | --- | --- |
| Your split (% in VTI) | slider 0-100 step 5 | 65 | Start here, Drift, The bad years |
| Rebalance | dropdown: Rebalance every year / Never touch it | rebalance | all but Drift |
| Scenario | dropdown over the six (fixed list) | Replay 2016-2025 | Does the split matter? |
| Starting balance ($) | number box | 1,000,000 | all but Drift |
| Inflation to subtract (% a year) | slider 0-6 step 0.5 | 0 | all but Drift |
| Reset | button | | every chapter |

The inflation slider replaced an earlier "Future dollars / Today's dollars" switch: with the
switch, the slider did nothing until the switch was flipped, which failed the every-control-
does-something rule. At 0 the figures are plain future dollars; above 0 every dollar figure is
divided by (1 + inflation)^years and every rate has inflation taken out.

**Robustness.** Every money query starts from a `settings` CTE that sanitises the controls: a
blank, zero, negative or non-numeric starting balance falls back to the run's own starting
balance; a blank dropdown falls back to its default. Verified in a browser: no chart breaks.

**Header space.** Nothing wordy above the controls. The intro, the "how this binder is laid
out" note and the reading guidance all live inside closed pills ("About this page", "Words used
on this page", "How to use the controls"; "About this chapter" on the other chapters), so a
reader who knows the page sees controls and charts at the top of the viewport.

**Pending platform request.** The analyst has filed a change request with the platform team for
tabs or collapsible sections on a page. When that lands, the chapters may fold back into one page.

**Sections, in reading order:**

- **Headline tiles** for the chosen split and mode: balance at the end if history repeats, in the
  best scenario, in the worst scenario, and the effective yearly rate if history repeats (with
  inflation taken out when "Today's dollars" is on, the same way the grid does it).
- **1. Your money, six futures.** A fan: shaded band from worst to best scenario each year, with
  the history-repeats line through it, plus one line per scenario. A reference line at the
  starting balance.
- **2. Does the split matter?** For the chosen scenario: five named mixes (65/35, 100/0, 80/20,
  50/50, 35/65) as lines over the ten years.
- **3. The full grid.** Ending balance for the five named mixes (rows) by scenario (columns),
  colour-shaded, for the chosen rebalance mode. A second table with the effective yearly rate.
- **4. Drift.** For "never touch it" and the chosen split: the share in fund A each year, one line
  per scenario, with a reference line at the chosen split. Ignores the rebalance switch on purpose.
  The y axis fits the data rather than being pinned to 0-100, so the drift is readable.
- **5. Worst moments.** Per scenario for the chosen split: worst single year, deepest
  peak-to-bottom fall, years to recover, and the year the balance first doubles.

**Advisor additions (all agreed):** the range band (1), the effective yearly rate (tiles, 3, 5),
purchasing power (the inflation slider applies to every dollar figure and rate), recovery time
and doubling year (5).

## Outputs (the results the dashboard reads)

Every split from 0 to 100 in steps of 5 is computed so the slider works; the five named mixes are
a labelled subset. `growth_factor` is balance ÷ starting balance, so the dashboard can rescale to
any starting balance without a rerun.

| Output | Grain | Columns |
| --- | --- | --- |
| `paths` | one row per scenario × split × mode × year (year 0 = start) | scenario_id, scenario_name, pct_fund_a, mode, year_index, calendar_year, year_return_pct, growth_factor, balance, fund_a_balance, fund_b_balance, fund_a_share_pct, drawdown_pct |
| `mix_summary` | one row per scenario × split × mode | scenario_id, scenario_name, pct_fund_a, mode, ending_balance, ending_factor, cagr_pct, worst_year_pct, max_drawdown_pct, recovery_years, doubling_year, is_replay |
| `named_mixes` | one row per named mix | mix_id, name, pct_fund_a |
| `scenarios` | one row per scenario | scenario_id, name, description, is_replay |
| `run_info` | one row | fund_a, fund_a_name, fund_b, fund_b_name, starting_balance, start_year, horizon_years |

How the numbers are made (all in SQL, one query per output):

- **Rebalance every year:** the portfolio's return each year is the weighted return of the two
  funds; the balance compounds that.
- **Never touch it:** each fund compounds on its own from its share of the start; the balance is
  the sum, and the fund A share drifts.
- **Drawdown:** balance against the highest balance seen so far. **Recovery years:** from the
  deepest trough to the first later year back above that prior peak; blank if never within the
  horizon. **Doubling year:** first calendar year with growth_factor ≥ 2; blank if never.
- **CAGR (effective yearly rate):** ending_factor ^ (1/years) − 1.
- **Inflation:** the dashboard divides by (1 + inflation) ^ years elapsed; at 0% nothing changes.

## Build notes (2026-09-02)

- Built by Save-As from `example/`; first full run and browser check passed the same day.
- Dashboard charts read the year as text so it plots as labels, and multi-line charts are
  shaped one column per line (the renderer's wide form). Every control value is cast in SQL.
- Scenario names avoid commas ("US stalls / world runs") because the dropdown's option list is
  comma-separated.
- Interactive check in a browser (2026-09-02): every control redraws the tiles, charts and
  tables; the web address carries the settings both ways; Reset restores the defaults.
- The coverage check was exercised: choosing VOO stops the run and lists the missing scenarios.

## Dependencies

The platform SDK (`tarn`) and DuckDB, both already in the project. No other packages.

## Promotion: how this becomes a job on the platform (agreed 2026-09-02)

The analyst's review path: open a pull request, review it, merge to `main`. A GitHub workflow
(`.github/workflows/job.yml`) then builds the job image from the `Dockerfile` and pushes it to
the organisation's registry (`ghcr.io/<org>/two-fund-stress-test`), and its run summary prints
the reference to register as the job definition. On a pull request the workflow only builds, as
a check that the recipe still works.

- **The image** is the platform's public base (`tarn-job-base:0.8.14`, the same release as
  `uv.lock`) plus `main.py`, `parameters.json` and `dashboard/`. The pretend data stays out: a
  promoted job reads the governed lake.
- **Register by digest, never by tag.** The platform refuses a tag because a tag can be moved;
  the workflow prints `ghcr.io/<org>/two-fund-stress-test@sha256:…` for exactly this reason.
- **Once:** make the package public in the organisation's package settings, so the platform can
  pull it without a credential. The workflow summary links to that page.
- Verified locally: the image builds, `main.py` parses inside it, the SDK imports, and
  `parameters.json` is valid.
