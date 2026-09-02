---
title: The bad years
sidebar_position: 4
---

# The bad years: what you would have to sit through

```sql worst
-- The numbers that decide whether someone panics, for the chosen split and mode.
WITH settings AS (
    SELECT CASE WHEN try_cast(${inputs.start_balance}::VARCHAR AS DOUBLE) > 0
                THEN try_cast(${inputs.start_balance}::VARCHAR AS DOUBLE)
                ELSE starting_balance END AS start_balance,
           1 + coalesce(try_cast(${inputs.inflation}::VARCHAR AS DOUBLE), 0) / 100.0 AS deflator,
           horizon_years
    FROM run_info
)
SELECT m.scenario_name,
       st.start_balance * m.ending_factor / power(st.deflator, st.horizon_years) AS ending,
       m.worst_year_pct, m.max_drawdown_pct, m.recovery_text, m.doubling_text
FROM mix_summary m CROSS JOIN settings st
WHERE m.pct_fund_a = coalesce(try_cast(${inputs.split}::VARCHAR AS DOUBLE), 65) AND m.mode = coalesce(nullif(${inputs.mode}::VARCHAR, ''), 'Rebalance every year')
ORDER BY m.is_replay DESC, m.ending_factor DESC
```

{% notes label="About this chapter" %}
Growth is the easy part to look at. This is the hard part: for your split and rebalance choice,
what each future would put you through on the way.
{% /notes %}

{% slider name="split" title="Your split (% in VTI)" min=0 max=100 step=5 default=65 /%}
{% select name="mode" title="Rebalance" options="Rebalance every year,Never touch it" default="Rebalance every year" /%}
{% number_input name="start_balance" title="Starting balance ($)" default=1000000 /%}
{% slider name="inflation" title="Inflation to subtract (% a year; 0 = plain future dollars)" min=0 max=6 step=0.5 default=0 /%}
{% reset /%}

{% data_table data="$worst" rowShading=true title="The Bad Years, By Future" info="Worst year is the biggest one-year drop. Deepest fall is measured from the highest balance you ever had to the lowest point after it, which is usually bigger than any single year. Years to recover counts from that low point back to the old high. Read the deepest-fall column first and ask: would I have held on? Then read the recovery column and ask: for that long?" %}
{% column id="scenario_name" title="Future" /%}
{% column id="ending" title="Balance in 2035" fmt="usd0" /%}
{% column id="worst_year_pct" title="Worst year %" fmt="num1" contentType="colorscale" scaleColor=["#dc2626", "#fef3c7"] /%}
{% column id="max_drawdown_pct" title="Deepest fall %" fmt="num1" contentType="colorscale" scaleColor=["#fef3c7", "#dc2626"] /%}
{% column id="recovery_text" title="Years to recover" /%}
{% column id="doubling_text" title="Money doubled in" /%}
{% /data_table %}

{% notes %}
Growth is the easy part to look at. This table is the hard part. For your chosen split and
rebalance choice, each row is one future: the worst single year, the deepest fall from a high
point, how many years it took to climb back, and the year the money doubled (if it ever did).
An advisor's rule of thumb: if the deepest fall would make you sell, the split is too aggressive
for you, whatever the ending balance says.
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
