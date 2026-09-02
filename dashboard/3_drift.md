---
title: Drift
sidebar_position: 3
---

# Drift: what happens if you never rebalance

```sql drift
-- If you never rebalance, the share of the money in fund A each year, in every future.
WITH bal AS (
    SELECT calendar_year, scenario_id, fund_a_share_pct AS v, pct_fund_a
    FROM paths
    WHERE pct_fund_a = coalesce(try_cast(${inputs.split}::VARCHAR AS DOUBLE), 65) AND mode = 'Never touch it'
)
SELECT calendar_year::VARCHAR AS year,
       max(CASE WHEN scenario_id = 'replay_2016_2025'     THEN v END) AS "History repeats",
       max(CASE WHEN scenario_id = 'steady_growth'        THEN v END) AS "Steady growth",
       max(CASE WHEN scenario_id = 'crash_year_3'         THEN v END) AS "Crash in year 3",
       max(CASE WHEN scenario_id = 'us_stalls_world_runs' THEN v END) AS "US stalls / world runs",
       max(CASE WHEN scenario_id = 'world_stalls_us_runs' THEN v END) AS "World stalls / US runs",
       max(CASE WHEN scenario_id = 'lost_decade'          THEN v END) AS "Lost decade",
       max(pct_fund_a) AS target_share
FROM bal
GROUP BY calendar_year
ORDER BY calendar_year
```

{% notes label="About this chapter" %}
Start at the split on the slider, never trade again, and watch where each future takes it. Only
the split matters here: the chart always shows "never touch it", because that is the point of it,
and it is about shares of the money, not dollars.
{% /notes %}

{% slider name="split" title="Your split (% in VTI)" min=0 max=100 step=5 default=65 /%}
{% reset /%}

{% line_chart data="$drift" x="year" y=["History repeats","Steady growth","Crash in year 3","US stalls / world runs","World stalls / US runs","Lost decade"] title="Share Of Your Money In VTI, If Never Rebalanced" yFmt="num0" yAxisTitle="% in VTI" chartAreaHeight=360 legend="bottom" info="How the split drifts when you never trade. Lines climbing above the dotted target mean VTI has been winning and you now own more America than you chose; lines falling below mean the world basket has been winning. Rebalancing once a year would pull every line back to the dotted line. Drift is not automatically bad: it means you kept riding the winner. But it does mean your risk has changed without you deciding it." %}
{% reference_line y="target_share" label="Your chosen split" color="#94a3b8" /%}
{% /line_chart %}

{% notes %}
This chart ignores the Rebalance switch on purpose: it always shows "never touch it". You start
at the split on the slider. Each line shows how much of your money is in VTI at the end of each
year in one future. The dotted line is the split you chose. The further a line wanders from it,
the more your portfolio has quietly turned into something you did not pick.
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
