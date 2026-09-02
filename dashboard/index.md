---
title: Start here
sidebar_position: 0
---

# Two-Fund Stress Test

```sql headline
-- The four headline tiles for the chosen split and mode. Every dollar figure is rescaled to the
-- starting balance typed on the page and, in today's dollars, shrunk by inflation over the
-- whole horizon. The rate has inflation taken out the same way, so tile and grid agree.
WITH settings AS (
    SELECT CASE WHEN try_cast(${inputs.start_balance}::VARCHAR AS DOUBLE) > 0
                THEN try_cast(${inputs.start_balance}::VARCHAR AS DOUBLE)
                ELSE starting_balance END AS start_balance,
           1 + coalesce(try_cast(${inputs.inflation}::VARCHAR AS DOUBLE), 0) / 100.0 AS deflator,
           horizon_years
    FROM run_info
),
s AS (
    SELECT m.*, st.start_balance * m.ending_factor / power(st.deflator, st.horizon_years) AS ending,
           100 * ((1 + m.cagr_pct / 100.0) / st.deflator - 1) AS rate
    FROM mix_summary m CROSS JOIN settings st
    WHERE m.pct_fund_a = coalesce(try_cast(${inputs.split}::VARCHAR AS DOUBLE), 65) AND m.mode = coalesce(nullif(${inputs.mode}::VARCHAR, ''), 'Rebalance every year')
)
SELECT
    (SELECT ending FROM s WHERE is_replay) AS replay_ending,
    (SELECT rate FROM s WHERE is_replay) AS replay_cagr,
    (SELECT max(ending) FROM s) AS best_ending,
    (SELECT min(ending) FROM s) AS worst_ending
```

```sql fan
-- The range band: each year's lowest and highest balance across the six futures, with the
-- history-repeats path through it. The year is text so the chart treats it as a label.
WITH settings AS (
    SELECT CASE WHEN try_cast(${inputs.start_balance}::VARCHAR AS DOUBLE) > 0
                THEN try_cast(${inputs.start_balance}::VARCHAR AS DOUBLE)
                ELSE starting_balance END AS start_balance,
           1 + coalesce(try_cast(${inputs.inflation}::VARCHAR AS DOUBLE), 0) / 100.0 AS deflator,
           horizon_years
    FROM run_info
),
bal AS (
    SELECT p.calendar_year, p.scenario_id,
           st.start_balance * p.growth_factor / power(st.deflator, p.year_index) AS bal,
           st.start_balance
    FROM paths p CROSS JOIN settings st
    WHERE p.pct_fund_a = coalesce(try_cast(${inputs.split}::VARCHAR AS DOUBLE), 65) AND p.mode = coalesce(nullif(${inputs.mode}::VARCHAR, ''), 'Rebalance every year')
)
SELECT calendar_year::VARCHAR AS year,
       min(bal) AS lowest,
       max(bal) AS highest,
       max(CASE WHEN scenario_id = 'replay_2016_2025' THEN bal END) AS history_repeats,
       max(start_balance) AS start_balance
FROM bal
GROUP BY calendar_year
ORDER BY calendar_year
```

```sql six_lines
-- Every future as its own column, one row per year (the chart wants one column per line).
WITH settings AS (
    SELECT CASE WHEN try_cast(${inputs.start_balance}::VARCHAR AS DOUBLE) > 0
                THEN try_cast(${inputs.start_balance}::VARCHAR AS DOUBLE)
                ELSE starting_balance END AS start_balance,
           1 + coalesce(try_cast(${inputs.inflation}::VARCHAR AS DOUBLE), 0) / 100.0 AS deflator,
           horizon_years
    FROM run_info
),
bal AS (
    SELECT p.calendar_year, p.scenario_id,
           st.start_balance * p.growth_factor / power(st.deflator, p.year_index) AS v,
           st.start_balance
    FROM paths p CROSS JOIN settings st
    WHERE p.pct_fund_a = coalesce(try_cast(${inputs.split}::VARCHAR AS DOUBLE), 65) AND p.mode = coalesce(nullif(${inputs.mode}::VARCHAR, ''), 'Rebalance every year')
)
SELECT calendar_year::VARCHAR AS year,
       max(CASE WHEN scenario_id = 'replay_2016_2025'     THEN v END) AS "History repeats",
       max(CASE WHEN scenario_id = 'steady_growth'        THEN v END) AS "Steady growth",
       max(CASE WHEN scenario_id = 'crash_year_3'         THEN v END) AS "Crash in year 3",
       max(CASE WHEN scenario_id = 'us_stalls_world_runs' THEN v END) AS "US stalls / world runs",
       max(CASE WHEN scenario_id = 'world_stalls_us_runs' THEN v END) AS "World stalls / US runs",
       max(CASE WHEN scenario_id = 'lost_decade'          THEN v END) AS "Lost decade",
       max(start_balance) AS start_balance
FROM bal
GROUP BY calendar_year
ORDER BY calendar_year
```

{% notes label="About this page — read this first" %}
Imagine you put **one million dollars** into two big baskets of stocks today. One basket holds
every company in America (VTI). The other holds every company in the rest of the world (VXUS).
Then you wait ten years, from 2026 to 2035. **How much money would you have?** Nobody knows. So
this page tells six different stories about the next ten years and shows what happens to your
money in each one. You can change how the money is split, and a lot more, using the controls
below. Play with them.

**What you are looking at.** Six made-up futures for the next ten years. Each one says how much
each basket goes up or down every year. We take your money, split it the way you choose, and
follow the rules of each future one year at a time. The money that is there at the end of a year
is what grows (or shrinks) the next year. That is called compounding, and it is why a good decade
can more than double your money.

**Where the six futures come from.** They are shaped by what really happened in the past. Over
long stretches, the American basket has grown about 10% a year and the world basket about 5% to
6% a year. In 2008 they fell 37% and 44% in one year. The "Replay 2016-2025" future is not made
up at all: it is exactly what the two baskets did in the last ten years, played again.

**What this page does not do.** It does not tell you which future will happen. It does not
average the six futures together, on purpose: they are not equally likely, and an average of
stories is not a forecast. And it assumes no money goes in or out, and no tax, because this is a
401(k).

**Dividends** (the small cash payments companies make) are included and reinvested in every
number here.

**How this binder is laid out.** Each chapter on the left is one screen: the controls on top, and
the chart or table they change directly underneath. Only the controls that change that chapter
are shown. Each chapter's controls start back at 65/35 and $1,000,000 when you open it, and the
web address remembers what you set on the chapter you are looking at, so copy it to send someone
that exact view.
{% /notes %}

{% glossary label="Words used on this page" %}
| Term | What it means |
| --- | --- |
| **VTI** | A fund that owns a tiny piece of every company traded in the United States. Buying it is like buying the whole American stock market at once. |
| **VXUS** | The same idea for every company outside the United States: Europe, Japan, China, everywhere else. |
| **ETF** | "Exchange-traded fund". A basket of many stocks you can buy as one thing. VTI and VXUS are both ETFs. |
| **Split** | How your money is divided between the two baskets. 65/35 means 65 cents of every dollar in VTI and 35 cents in VXUS. |
| **Total return** | How much a basket grew in a year, counting both the price going up and the dividends it paid. All the yearly numbers here are total returns. |
| **Dividends** | Small cash payments companies send to their owners. Here they are used to buy more of the same basket, so they grow too. |
| **Compounding** | Growth on top of growth. If $100 becomes $110, next year the whole $110 grows, not just the first $100. |
| **Rebalance** | Once a year, sell a little of the basket that grew more and buy the one that grew less, so the split goes back to what you chose. |
| **Never touch it** | Buy once and never trade again. The split drifts toward whichever basket is winning. |
| **Drift** | What happens to your split when you never rebalance. Start at 65/35, and after a great American decade you might be at 75/25 without doing anything. |
| **Scenario / future** | One made-up story of the next ten years: a list of how much each basket goes up or down each year. There are six. |
| **Replay 2016-2025** | The one future that is not made up. It is what the baskets really did from 2016 to 2025, played again from 2026. |
| **Effective yearly rate** | If your money had grown by the exact same percentage every single year to reach the ending balance, what would that percentage be? A fair way to compare any two plans. Advisors call it CAGR. |
| **Worst year** | The single biggest one-year drop in that future. The number that tests your nerves. |
| **Deepest fall** | Measured from the highest balance you ever had to the lowest point after it. Advisors call it maximum drawdown. |
| **Years to recover** | After the deepest fall, how many years until the balance climbs back above where it was before the fall. |
| **Doubling year** | The first year the balance is at least twice what you started with. |
| **Inflation to subtract** | Prices go up a little every year (inflation), so a dollar in 2035 buys less than a dollar now. Slide this above zero and every future number shrinks so it is measured in what money buys today. At zero, the figures are plain future dollars. |
| **Inflation** | How fast prices rise. Around 3% a year is the long-run habit in the United States. Try 3 on the slider. |
| **401(k)** | A retirement account through your employer. Money inside it is not taxed while it grows, which is why this page ignores tax. |
{% /glossary %}

{% notes label="How to use the controls" %}
Drag **Your split** to change how much of the money is in VTI; the rest is in VXUS. Flip
**Rebalance** to see whether tidying up once a year matters. Type any **Starting balance** (leave
it blank and it goes back to $1,000,000). Slide **Inflation** above zero to see every figure in
today's money, which is what it will really buy; at zero the figures are plain future dollars. **Reset** puts everything back. The numbers and the chart
below change as you go.
{% /notes %}

{% slider name="split" title="Your split (% in VTI)" min=0 max=100 step=5 default=65 /%}
{% select name="mode" title="Rebalance" options="Rebalance every year,Never touch it" default="Rebalance every year" /%}
{% number_input name="start_balance" title="Starting balance ($)" default=1000000 /%}
{% slider name="inflation" title="Inflation to subtract (% a year; 0 = plain future dollars)" min=0 max=6 step=0.5 default=0 /%}
{% reset /%}

{% big_value data="$headline" value="replay_ending" title="In 2035 If History Repeats" fmt="usd0" info="Where your money ends up in 2035 if the next ten years look exactly like 2016 to 2025. Compare it with the starting balance: more than double means the money doubled. This is one story, not a promise." /%}
{% big_value data="$headline" value="replay_cagr" title="Yearly Rate If History Repeats" fmt="num1" suffix="%" info="The one steady growth rate per year that would take the starting balance to the ending balance in that story. Anything around 7% to 10% a year is what stocks have done over long stretches; a rate under the inflation slider means the money is not keeping up with prices." /%}
{% big_value data="$headline" value="best_ending" title="Best Of The Six Futures" fmt="usd0" info="The highest ending balance among the six stories, for the split and rebalance choice you have set. This is the ceiling of what this page imagines, not a target." /%}
{% big_value data="$headline" value="worst_ending" title="Worst Of The Six Futures" fmt="usd0" info="The lowest ending balance among the six stories. If this number is below the starting balance, at least one future leaves you with less than you began with after ten years. Ask yourself whether you could live with that before choosing a split." /%}

{% line_chart data="$fan" x="year" y="history_repeats" yLo="lowest" yHi="highest" title="Where Your Money Could Be, Year By Year" yFmt="usd0" yAxisTitle="balance" chartAreaHeight=340 info="The band runs from the worst future to the best future each year; the line is what happens if the last ten years repeat. Read it like a weather forecast: the band is the range of what could happen, not a guarantee. If the band's bottom edge dips below the dotted start line, at least one future has you losing money in that year. A band that keeps widening means the choice of future matters more and more as the years go on." %}
{% reference_line y="start_balance" label="Starting balance" color="#94a3b8" /%}
{% /line_chart %}

{% notes %}
The shaded strip is the range: the bottom edge is the worst of the six futures each year, the
top edge is the best. The line inside it is "history repeats". A wide strip means the future is
very uncertain; a narrow one means every story ends up in about the same place. The dotted line
is the starting balance, so anything below it is a year you would be down.
{% /notes %}

{% line_chart data="$six_lines" x="year" y=["History repeats","Steady growth","Crash in year 3","US stalls / world runs","World stalls / US runs","Lost decade"] title="Each Future As Its Own Line" yFmt="usd0" yAxisTitle="balance" chartAreaHeight=340 legend="bottom" info="The same six stories, each drawn separately, so you can see which one is which. Hover a line to name it. A line that drops sharply then climbs back is a crash-and-recovery story; a line that stays flat near the starting balance is a lost decade. Compare the steepest line with the flattest: that gap is how much the future you get matters, more than any split you choose." %}
{% reference_line y="start_balance" label="Starting balance" color="#94a3b8" /%}
{% /line_chart %}
