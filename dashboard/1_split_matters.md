---
title: Does the split matter?
sidebar_position: 1
---

# Does the split matter?

```sql split_matters
-- The chosen future, five named splits as columns, one row per year.
WITH settings AS (
    SELECT CASE WHEN try_cast(${inputs.start_balance}::VARCHAR AS DOUBLE) > 0
                THEN try_cast(${inputs.start_balance}::VARCHAR AS DOUBLE)
                ELSE starting_balance END AS start_balance,
           1 + coalesce(try_cast(${inputs.inflation}::VARCHAR AS DOUBLE), 0) / 100.0 AS deflator,
           horizon_years
    FROM run_info
),
bal AS (
    SELECT p.calendar_year, p.pct_fund_a,
           st.start_balance * p.growth_factor / power(st.deflator, p.year_index) AS v,
           st.start_balance
    FROM paths p CROSS JOIN settings st
    WHERE p.scenario_name = coalesce(nullif(${inputs.scenario}::VARCHAR, ''), 'Replay 2016-2025') AND p.mode = coalesce(nullif(${inputs.mode}::VARCHAR, ''), 'Rebalance every year')
      AND p.pct_fund_a IN (SELECT pct_fund_a FROM named_mixes)
)
SELECT calendar_year::VARCHAR AS year,
       max(CASE WHEN pct_fund_a = 100 THEN v END) AS "100/0",
       max(CASE WHEN pct_fund_a = 80  THEN v END) AS "80/20",
       max(CASE WHEN pct_fund_a = 65  THEN v END) AS "65/35",
       max(CASE WHEN pct_fund_a = 50  THEN v END) AS "50/50",
       max(CASE WHEN pct_fund_a = 35  THEN v END) AS "35/65",
       max(start_balance) AS start_balance
FROM bal
GROUP BY calendar_year
ORDER BY calendar_year
```

{% notes label="About this chapter" %}
Same money, same future, five different splits. Pick a **Scenario** and watch which split wins,
then pick another and watch it change. The split slider is not here because this chart always
shows all five splits.
{% /notes %}

{% select name="scenario" title="Scenario" options="Replay 2016-2025,Steady growth,Crash in year 3,US stalls / world runs,World stalls / US runs,Lost decade" default="Replay 2016-2025" /%}
{% select name="mode" title="Rebalance" options="Rebalance every year,Never touch it" default="Rebalance every year" /%}
{% number_input name="start_balance" title="Starting balance ($)" default=1000000 /%}
{% slider name="inflation" title="Inflation to subtract (% a year; 0 = plain future dollars)" min=0 max=6 step=0.5 default=0 /%}
{% reset /%}

{% line_chart data="$split_matters" x="year" y=["100/0","80/20","65/35","50/50","35/65"] title="Five Splits In The Chosen Future" yFmt="usd0" yAxisTitle="balance" chartAreaHeight=340 legend="bottom" info="Five ways of dividing the same money, all living through the future you picked. The order of the lines at the right edge is the ranking for that future. Do not pick the winner of one story: flip through all six and look for the split that is never the worst. That is what diversification buys, not the top spot." %}
{% reference_line y="start_balance" label="Starting balance" color="#94a3b8" /%}
{% /line_chart %}

{% notes %}
Pick a **Scenario** in the controls above. This chart shows five different splits living through
that same future. If the lines are close together, the split barely matters in that story. If
they fan out, it matters a lot, and the top line tells you which split won. Try "US stalls / world
runs" and then "World stalls / US runs": the winner flips, which is the whole reason people hold
both baskets.
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
