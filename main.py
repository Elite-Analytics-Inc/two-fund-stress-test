"""two-fund-stress-test — one starting balance, two funds, ten years, six futures.

**The measurement, stated plainly, because it is the whole analysis.** Take a starting balance,
split it between fund A and fund B, and compound it forward one year at a time using each
scenario's yearly total return (price change plus reinvested dividends). Do that for every split
from 0% to 100% in fund A, in steps of five, and in two ways: rebalanced back to the split every
year, or bought once and never touched. Then read off the numbers a wealth advisor would put on
the table — ending balance, effective yearly rate, worst year, deepest fall, years to recover,
the year the money doubles.

**No money goes in or out after day one, and there is no tax.** The analyst decided the account
is a 401(k), so dividends compound untaxed and the return figures already include them.

**No "average of the six scenarios" is computed anywhere.** The six futures are hand-picked and
not equally likely; an equal-weight average of them would look precise and mean little. The
analyst asked for it to be left out, and the dashboard says so.

**The shape is the Job Definition contract.** `main.py` runs top to bottom — no framework, no
hidden entry points. `parameters.json` beside it declares what varies per run and renders the
launch form. The `dashboard/` directory holds the page that shows the results, uploaded as-is at
the end of the run.

**Every output is one governed query.** The shared derivation is a block of CTEs repeated in each
output's SQL rather than a table materialized locally, so each artifact is produced by a single
statement on the governed connection.
"""

import os

import tarn

#: The deployment names its own workspace catalog; a job reads the name from the environment
#: rather than hardcoding it, so the same repo runs against any install.
CATALOG = os.environ.get("TARN_WORKSPACE_CATALOG", "lake")

#: Typed and constrained in `parameters.json`, which is also what renders the launch form.
#: The two funds are settings, not hard-wired: any ticker with ten years of returns for every
#: scenario can take either seat.
FUND_A = os.environ.get("TARN_PARAM_FUND_A", "VTI").strip().upper()
FUND_B = os.environ.get("TARN_PARAM_FUND_B", "VXUS").strip().upper()
STARTING_BALANCE = float(os.environ.get("TARN_PARAM_STARTING_BALANCE", "1000000"))
START_YEAR = int(os.environ.get("TARN_PARAM_START_YEAR", "2026"))
HORIZON = int(os.environ.get("TARN_PARAM_HORIZON_YEARS", "10"))

#: Splits are computed in steps of five so the dashboard's slider can move without a rerun.
SPLIT_STEP = 5

#: The shared derivation. Reads the two funds' yearly returns for every scenario and compounds
#: them under both rebalancing modes for every split.
#:
#: **Why there is no recursion.** Compounding is a running product, and a running product is
#: exp(running sum of logs). DuckDB's window functions do running sums, so ten years of
#: compounding is one window expression rather than a loop — and the whole thing stays one
#: governed SELECT.
#:
#: **The two modes differ in exactly one place.** Rebalancing means the *portfolio* earns the
#: weighted return each year and compounds that. Never touching it means *each fund* compounds
#: on its own from its share of the start, and the balance is simply the sum — which is why the
#: fund A share drifts in that mode and stays put in the other.
#:
#: **Year 0 is the starting point**, labelled the year before the first forecast year, so the
#: charts begin at the starting balance rather than one year in.
PATHS = f"""
    -- Every split from 0 to 100 in fund A, in steps of {SPLIT_STEP}.
    splits AS (
        SELECT (g * {SPLIT_STEP})::DOUBLE AS pct_fund_a
        FROM range(0, (100 // {SPLIT_STEP}) + 1) t(g)
    ),
    -- Each fund's yearly return in each scenario, as a fraction (0.12 for 12%).
    returns_a AS (
        SELECT scenario_id, year AS year_index, total_return_pct / 100.0 AS r
        FROM {CATALOG}.portfolio.scenario_returns
        WHERE upper(ticker) = '{FUND_A}' AND year BETWEEN 1 AND {HORIZON}
    ),
    returns_b AS (
        SELECT scenario_id, year AS year_index, total_return_pct / 100.0 AS r
        FROM {CATALOG}.portfolio.scenario_returns
        WHERE upper(ticker) = '{FUND_B}' AND year BETWEEN 1 AND {HORIZON}
    ),
    -- One row per scenario-year with both funds' returns side by side. An inner join here is
    -- deliberate: a scenario missing either fund is a data gap the coverage check reports
    -- before this query ever runs.
    scenario_years AS (
        SELECT s.scenario_id, s.name AS scenario_name,
               a.year_index, a.r AS r_a, b.r AS r_b
        FROM {CATALOG}.portfolio.scenarios s
        JOIN returns_a a ON a.scenario_id = s.scenario_id
        JOIN returns_b b ON b.scenario_id = s.scenario_id AND b.year_index = a.year_index
    ),
    -- Each fund compounding alone: how $1 in that fund alone grows by the end of each year.
    fund_growth AS (
        SELECT *,
               exp(sum(ln(1 + r_a)) OVER w) AS cum_a,
               exp(sum(ln(1 + r_b)) OVER w) AS cum_b
        FROM scenario_years
        WINDOW w AS (PARTITION BY scenario_id ORDER BY year_index ROWS UNBOUNDED PRECEDING)
    ),
    -- Mode 1: rebalance every year. The portfolio earns w*r_a + (1-w)*r_b and compounds that.
    rebalanced AS (
        SELECT g.scenario_id, g.scenario_name, sp.pct_fund_a,
               'Rebalance every year' AS mode,
               g.year_index,
               (sp.pct_fund_a / 100.0) * g.r_a + (1 - sp.pct_fund_a / 100.0) * g.r_b AS year_return,
               exp(sum(ln(1 + (sp.pct_fund_a / 100.0) * g.r_a + (1 - sp.pct_fund_a / 100.0) * g.r_b))
                   OVER (PARTITION BY g.scenario_id, sp.pct_fund_a
                         ORDER BY g.year_index ROWS UNBOUNDED PRECEDING)) AS growth_factor,
               -- After rebalancing, fund A holds exactly its target share again.
               (sp.pct_fund_a / 100.0) AS fund_a_share
        FROM fund_growth g CROSS JOIN splits sp
    ),
    -- Mode 2: never touch it. Each fund grows on its own; the balance is the sum of the two.
    held AS (
        SELECT g.scenario_id, g.scenario_name, sp.pct_fund_a,
               'Never touch it' AS mode,
               g.year_index,
               (sp.pct_fund_a / 100.0) * g.cum_a + (1 - sp.pct_fund_a / 100.0) * g.cum_b AS growth_factor,
               (sp.pct_fund_a / 100.0) * g.cum_a AS fund_a_factor
        FROM fund_growth g CROSS JOIN splits sp
    ),
    held_with_returns AS (
        SELECT scenario_id, scenario_name, pct_fund_a, mode, year_index,
               -- This year's portfolio return is how much the balance grew since last year.
               growth_factor / coalesce(lag(growth_factor) OVER (PARTITION BY scenario_id, pct_fund_a
                                                                  ORDER BY year_index), 1.0) - 1 AS year_return,
               growth_factor,
               fund_a_factor / growth_factor AS fund_a_share
        FROM held
    ),
    -- Year 0: the starting point, identical for every mode and split.
    year_zero AS (
        SELECT s.scenario_id, s.name AS scenario_name, sp.pct_fund_a, m.mode,
               0 AS year_index, NULL::DOUBLE AS year_return, 1.0 AS growth_factor,
               sp.pct_fund_a / 100.0 AS fund_a_share
        FROM {CATALOG}.portfolio.scenarios s
        CROSS JOIN splits sp
        CROSS JOIN (SELECT 'Rebalance every year' AS mode UNION ALL SELECT 'Never touch it') m
        WHERE s.scenario_id IN (SELECT scenario_id FROM scenario_years)
    ),
    all_years AS (
        SELECT * FROM year_zero
        UNION ALL SELECT * FROM rebalanced
        UNION ALL SELECT * FROM held_with_returns
    ),
    -- Drawdown: how far below the highest balance seen so far. Zero at a new high.
    paths AS (
        SELECT scenario_id, scenario_name, pct_fund_a, mode, year_index,
               {START_YEAR} - 1 + year_index AS calendar_year,
               year_return * 100 AS year_return_pct,
               growth_factor,
               growth_factor * {STARTING_BALANCE} AS balance,
               growth_factor * fund_a_share * {STARTING_BALANCE} AS fund_a_balance,
               growth_factor * (1 - fund_a_share) * {STARTING_BALANCE} AS fund_b_balance,
               fund_a_share * 100 AS fund_a_share_pct,
               max(growth_factor) OVER (PARTITION BY scenario_id, pct_fund_a, mode
                                        ORDER BY year_index ROWS UNBOUNDED PRECEDING) AS peak_factor,
               100 * (1 - growth_factor / max(growth_factor) OVER (PARTITION BY scenario_id, pct_fund_a, mode
                                                                   ORDER BY year_index ROWS UNBOUNDED PRECEDING)) AS drawdown_pct
        FROM all_years
    )
"""

#: The year-by-year table every chart on the dashboard reads.
PATHS_OUTPUT = f"""
WITH {PATHS}
SELECT scenario_id, scenario_name, pct_fund_a, mode, year_index, calendar_year,
       round(year_return_pct, 2) AS year_return_pct,
       growth_factor,
       round(balance, 2) AS balance,
       round(fund_a_balance, 2) AS fund_a_balance,
       round(fund_b_balance, 2) AS fund_b_balance,
       round(fund_a_share_pct, 2) AS fund_a_share_pct,
       round(drawdown_pct, 2) AS drawdown_pct
FROM paths
ORDER BY scenario_id, pct_fund_a, mode, year_index
"""

#: The advisor numbers, one row per scenario × split × mode.
#:
#: **Recovery time is measured from the deepest trough**, not from the first dip: the question a
#: nervous holder asks is "after the worst of it, how long until I am whole again?". It is blank
#: when the balance never gets back above its earlier peak within the horizon, and zero when the
#: balance never fell at all.
#:
#: **Doubling year is the first calendar year the balance is at least twice the start**, blank
#: if that never happens. The effective yearly rate (CAGR) is the single constant rate that would
#: have produced the same ending balance.
MIX_SUMMARY = f"""
WITH {PATHS},
    ending AS (
        SELECT scenario_id, scenario_name, pct_fund_a, mode, growth_factor AS ending_factor
        FROM paths WHERE year_index = {HORIZON}
    ),
    -- The deepest trough: the earliest year at which the drawdown is at its maximum.
    trough AS (
        SELECT scenario_id, pct_fund_a, mode, year_index AS trough_year, peak_factor AS peak_before,
               drawdown_pct AS max_drawdown_pct
        FROM (
            SELECT *, row_number() OVER (PARTITION BY scenario_id, pct_fund_a, mode
                                         ORDER BY drawdown_pct DESC, year_index) AS rn
            FROM paths
        ) WHERE rn = 1
    ),
    recovery AS (
        SELECT t.scenario_id, t.pct_fund_a, t.mode,
               min(p.year_index) - t.trough_year AS recovery_years
        FROM trough t
        JOIN paths p ON p.scenario_id = t.scenario_id AND p.pct_fund_a = t.pct_fund_a AND p.mode = t.mode
        WHERE p.year_index > t.trough_year AND p.growth_factor >= t.peak_before
        GROUP BY t.scenario_id, t.pct_fund_a, t.mode, t.trough_year
    ),
    doubling AS (
        SELECT scenario_id, pct_fund_a, mode, min(calendar_year) AS doubling_year
        FROM paths WHERE growth_factor >= 2
        GROUP BY scenario_id, pct_fund_a, mode
    ),
    worst AS (
        SELECT scenario_id, pct_fund_a, mode,
               min(year_return_pct) AS worst_year_pct,
               max(year_return_pct) AS best_year_pct
        FROM paths WHERE year_index > 0
        GROUP BY scenario_id, pct_fund_a, mode
    )
SELECT e.scenario_id, e.scenario_name, e.pct_fund_a, e.mode,
       round(e.ending_factor * {STARTING_BALANCE}, 2) AS ending_balance,
       e.ending_factor,
       round(100 * (power(e.ending_factor, 1.0 / {HORIZON}) - 1), 2) AS cagr_pct,
       round(w.worst_year_pct, 2) AS worst_year_pct,
       round(w.best_year_pct, 2) AS best_year_pct,
       round(t.max_drawdown_pct, 2) AS max_drawdown_pct,
       CASE WHEN t.max_drawdown_pct <= 0 THEN 0 ELSE r.recovery_years END AS recovery_years,
       CASE WHEN t.max_drawdown_pct <= 0 THEN 'never fell'
            WHEN r.recovery_years IS NULL THEN 'not within {HORIZON} years'
            WHEN r.recovery_years = 1 THEN '1 year'
            ELSE r.recovery_years || ' years' END AS recovery_text,
       d.doubling_year,
       coalesce(d.doubling_year::VARCHAR, 'not within {HORIZON} years') AS doubling_text,
       e.scenario_id = 'replay_2016_2025' AS is_replay
FROM ending e
JOIN worst w USING (scenario_id, pct_fund_a, mode)
JOIN trough t USING (scenario_id, pct_fund_a, mode)
LEFT JOIN recovery r USING (scenario_id, pct_fund_a, mode)
LEFT JOIN doubling d USING (scenario_id, pct_fund_a, mode)
ORDER BY e.scenario_id, e.pct_fund_a, e.mode
"""

#: The five named mixes, for the grid and the "does the split matter" chart. Their names are
#: written in terms of fund A / fund B so they stay true when the funds are swapped.
NAMED_MIXES = f"""
SELECT mix_id,
       replace(replace(name, 'Fund A', '{FUND_A}'), 'Fund B', '{FUND_B}') AS name,
       pct_fund_a
FROM {CATALOG}.portfolio.mixes
ORDER BY pct_fund_a DESC
"""

#: The scenarios, for the dropdown and the section labels.
SCENARIOS = f"""
SELECT scenario_id, name, description,
       scenario_id = 'replay_2016_2025' AS is_replay
FROM {CATALOG}.portfolio.scenarios
ORDER BY scenario_id
"""

#: One row of run facts the page reads for its labels and its defaults.
RUN_INFO = f"""
SELECT '{FUND_A}' AS fund_a,
       (SELECT name FROM {CATALOG}.portfolio.funds WHERE upper(ticker) = '{FUND_A}') AS fund_a_name,
       '{FUND_B}' AS fund_b,
       (SELECT name FROM {CATALOG}.portfolio.funds WHERE upper(ticker) = '{FUND_B}') AS fund_b_name,
       {STARTING_BALANCE}::DOUBLE AS starting_balance,
       {START_YEAR}::INTEGER AS start_year,
       {START_YEAR} - 1 + {HORIZON} AS end_year,
       {HORIZON}::INTEGER AS horizon_years
"""

#: The coverage check. A fund is usable only if it has a return for every scenario and every
#: year of the horizon; this lists what is missing so the run can stop with a plain message
#: instead of silently dropping a scenario from every chart.
COVERAGE = f"""
WITH wanted AS (
    SELECT s.scenario_id, s.name AS scenario_name, f.ticker, y.year_index
    FROM {CATALOG}.portfolio.scenarios s
    CROSS JOIN (SELECT '{FUND_A}' AS ticker UNION ALL SELECT '{FUND_B}') f
    CROSS JOIN (SELECT range AS year_index FROM range(1, {HORIZON} + 1)) y
),
present AS (
    SELECT scenario_id, upper(ticker) AS ticker, year AS year_index
    FROM {CATALOG}.portfolio.scenario_returns
)
SELECT w.ticker, w.scenario_name, count(*) AS missing_years
FROM wanted w
LEFT JOIN present p USING (scenario_id, ticker, year_index)
WHERE p.ticker IS NULL
GROUP BY w.ticker, w.scenario_name
ORDER BY w.ticker, w.scenario_name
"""

OUTPUTS = (
    ("paths", PATHS_OUTPUT, "balance year by year, every scenario, split and mode"),
    ("mix_summary", MIX_SUMMARY, "the advisor numbers per scenario, split and mode"),
    ("named_mixes", NAMED_MIXES, "the five named splits"),
    ("scenarios", SCENARIOS, "the six futures"),
    ("run_info", RUN_INFO, "the run's funds, balance and years"),
)


def check_coverage() -> None:
    """Stop the run, plainly, if either fund lacks returns for any scenario-year."""
    if FUND_A == FUND_B:
        raise SystemExit(f"fund A and fund B are both {FUND_A} — pick two different funds")
    tarn.fetch("coverage_gaps", COVERAGE)
    gaps = tarn.connect().execute("SELECT * FROM coverage_gaps").fetchall()
    if gaps:
        lines = [f"  {ticker}: {scenario} is missing {n} of {HORIZON} years" for ticker, scenario, n in gaps]
        raise SystemExit(
            "cannot run: a chosen fund does not have returns for every scenario.\n"
            + "\n".join(lines)
            + "\nAdd the missing rows to portfolio.scenario_returns, or choose another fund."
        )


def main() -> None:
    tarn.stage("check")
    tarn.log(
        f"{FUND_A} / {FUND_B}; ${STARTING_BALANCE:,.0f} on day one; "
        f"{HORIZON} years from {START_YEAR}; every split in steps of {SPLIT_STEP}%"
    )
    check_coverage()
    tarn.log("both funds have returns for every scenario and year")

    tarn.stage("analyse")
    for index, (name, sql, what) in enumerate(OUTPUTS, start=1):
        tarn.progress(index / (len(OUTPUTS) + 1), what)
        tarn.save_artifact(name, sql)
        tarn.log(f"wrote {name} — {what}")

    tarn.stage("dashboard")
    # The repo's own `dashboard/` directory, uploaded exactly as shipped — the page the author
    # wrote, never a page generated by the run.
    tarn.save_dashboard()
    tarn.progress(1.0, "dashboard uploaded")

    tarn.stage("done")
    tarn.conclusion(
        f"${STARTING_BALANCE:,.0f} in {FUND_A} and {FUND_B}, compounded {HORIZON} years from "
        f"{START_YEAR} under six futures and every split. The dashboard shows the range of "
        "outcomes, whether the split matters, and what the worst stretches would feel like."
    )


if __name__ == "__main__":
    main()
