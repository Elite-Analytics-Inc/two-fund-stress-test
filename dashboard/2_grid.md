---
title: The full grid
sidebar_position: 2
---

# The full grid

```sql grid_balance
-- Ending balance for the five named splits (rows) under each future (columns).
WITH settings AS (
    SELECT CASE WHEN try_cast(${inputs.start_balance}::VARCHAR AS DOUBLE) > 0
                THEN try_cast(${inputs.start_balance}::VARCHAR AS DOUBLE)
                ELSE starting_balance END AS start_balance,
           1 + coalesce(try_cast(${inputs.inflation}::VARCHAR AS DOUBLE), 0) / 100.0 AS deflator,
           horizon_years
    FROM run_info
),
cells AS (
    SELECT n.name AS split, n.pct_fund_a, m.scenario_id,
           st.start_balance * m.ending_factor / power(st.deflator, st.horizon_years) AS v
    FROM mix_summary m
    JOIN named_mixes n ON n.pct_fund_a = m.pct_fund_a
    CROSS JOIN settings st
    WHERE m.mode = coalesce(nullif(${inputs.mode}::VARCHAR, ''), 'Rebalance every year')
)
SELECT split,
       max(CASE WHEN scenario_id = 'replay_2016_2025'     THEN v END) AS replay,
       max(CASE WHEN scenario_id = 'steady_growth'        THEN v END) AS steady,
       max(CASE WHEN scenario_id = 'crash_year_3'         THEN v END) AS crash,
       max(CASE WHEN scenario_id = 'us_stalls_world_runs' THEN v END) AS us_stalls,
       max(CASE WHEN scenario_id = 'world_stalls_us_runs' THEN v END) AS world_stalls,
       max(CASE WHEN scenario_id = 'lost_decade'          THEN v END) AS lost_decade
FROM cells
GROUP BY split, pct_fund_a
ORDER BY pct_fund_a DESC
```

```sql grid_rate
-- The same grid as an effective yearly rate, with inflation taken out in today's dollars.
WITH settings AS (
    SELECT CASE WHEN try_cast(${inputs.start_balance}::VARCHAR AS DOUBLE) > 0
                THEN try_cast(${inputs.start_balance}::VARCHAR AS DOUBLE)
                ELSE starting_balance END AS start_balance,
           1 + coalesce(try_cast(${inputs.inflation}::VARCHAR AS DOUBLE), 0) / 100.0 AS deflator,
           horizon_years
    FROM run_info
),
cells AS (
    SELECT n.name AS split, n.pct_fund_a, m.scenario_id,
           100 * ((1 + m.cagr_pct / 100.0) / st.deflator - 1) AS v
    FROM mix_summary m
    JOIN named_mixes n ON n.pct_fund_a = m.pct_fund_a
    CROSS JOIN settings st
    WHERE m.mode = coalesce(nullif(${inputs.mode}::VARCHAR, ''), 'Rebalance every year')
)
SELECT split,
       max(CASE WHEN scenario_id = 'replay_2016_2025'     THEN v END) AS replay,
       max(CASE WHEN scenario_id = 'steady_growth'        THEN v END) AS steady,
       max(CASE WHEN scenario_id = 'crash_year_3'         THEN v END) AS crash,
       max(CASE WHEN scenario_id = 'us_stalls_world_runs' THEN v END) AS us_stalls,
       max(CASE WHEN scenario_id = 'world_stalls_us_runs' THEN v END) AS world_stalls,
       max(CASE WHEN scenario_id = 'lost_decade'          THEN v END) AS lost_decade
FROM cells
GROUP BY split, pct_fund_a
ORDER BY pct_fund_a DESC
```

{% notes label="About this chapter" %}
Every split against every future in one table. There is no split slider or scenario picker here
because the grid already shows every split and every future.
{% /notes %}

{% select name="mode" title="Rebalance" options="Rebalance every year,Never touch it" default="Rebalance every year" /%}
{% number_input name="start_balance" title="Starting balance ($)" default=1000000 /%}
{% slider name="inflation" title="Inflation to subtract (% a year; 0 = plain future dollars)" min=0 max=6 step=0.5 default=0 /%}
{% reset /%}

{% data_table data="$grid_balance" rowShading=true title="Ending Balance In 2035, By Split And Future" info="Each cell is how much money you have in 2035 for that split (row) in that future (column). Look for the row whose worst cell you could live with, then check its best cell. A split with a great best case and a terrible worst case is a bet; a split whose cells are all decent is a plan." %}
{% column id="split" title="Split (VTI/VXUS)" /%}
{% column id="replay" title="History repeats" fmt="usd0" contentType="colorscale" scaleColor=["#fef3c7", "#15803d"] /%}
{% column id="steady" title="Steady growth" fmt="usd0" contentType="colorscale" scaleColor=["#fef3c7", "#15803d"] /%}
{% column id="crash" title="Crash in year 3" fmt="usd0" contentType="colorscale" scaleColor=["#fef3c7", "#15803d"] /%}
{% column id="us_stalls" title="US stalls" fmt="usd0" contentType="colorscale" scaleColor=["#fef3c7", "#15803d"] /%}
{% column id="world_stalls" title="World stalls" fmt="usd0" contentType="colorscale" scaleColor=["#fef3c7", "#15803d"] /%}
{% column id="lost_decade" title="Lost decade" fmt="usd0" contentType="colorscale" scaleColor=["#fef3c7", "#15803d"] /%}
{% /data_table %}

{% data_table data="$grid_rate" rowShading=true title="Effective Yearly Rate, By Split And Future (%)" info="The same grid as a growth rate per year. This is the number advisors quote: 'you averaged 7% a year'. With inflation set above zero it has been subtracted, so a rate near zero means the money only kept pace with prices. A negative cell means that split lost buying power in that future." %}
{% column id="split" title="Split (VTI/VXUS)" /%}
{% column id="replay" title="History repeats" fmt="num1" contentType="colorscale" scaleColor=["#fef3c7", "#15803d"] /%}
{% column id="steady" title="Steady growth" fmt="num1" contentType="colorscale" scaleColor=["#fef3c7", "#15803d"] /%}
{% column id="crash" title="Crash in year 3" fmt="num1" contentType="colorscale" scaleColor=["#fef3c7", "#15803d"] /%}
{% column id="us_stalls" title="US stalls" fmt="num1" contentType="colorscale" scaleColor=["#fef3c7", "#15803d"] /%}
{% column id="world_stalls" title="World stalls" fmt="num1" contentType="colorscale" scaleColor=["#fef3c7", "#15803d"] /%}
{% column id="lost_decade" title="Lost decade" fmt="num1" contentType="colorscale" scaleColor=["#fef3c7", "#15803d"] /%}
{% /data_table %}

{% notes %}
Every split against every future, in one table. Read across a row to see how one split does in
different futures. Read down a column to see how the futures rank the splits. Darker green is
more money. The second table shows the same thing as a yearly growth rate, which is the fairest
way to compare. Both tables follow the **Rebalance** switch and the money controls above.
{% /notes %}

{% glossary label="Words used on this page" %}
| Term | What it means |
| --- | --- |
| **Split** | How your money is divided between the two baskets. 65/35 means 65 cents of every dollar in VTI and 35 cents in VXUS. |
| **Rebalance** | Once a year, sell a little of the basket that grew more and buy the one that grew less, so the split goes back to what you chose. "Never touch it" means buy once and let it drift. |
| **Scenario / future** | One made-up story of the next ten years. "Replay 2016-2025" is the one that really happened, played again. |
| **Inflation to subtract** | Prices rise a little every year, so a 2035 dollar buys less than one today. Slide this above zero and every future number shrinks to what money buys today. At zero, the figures are plain future dollars. |
| **Effective yearly rate** | The one steady growth rate per year that would produce the same ending balance. Advisors call it CAGR. |
{% /glossary %}
