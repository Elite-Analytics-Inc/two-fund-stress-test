# Two-Fund Stress Test

*A plain summary of this analysis, derived from `spec.md`. If the two ever disagree, `spec.md` is
right — this file is regenerated from it, never edited directly.*

You have $1,000,000 split between two funds: VTI (the whole US stock market) and VXUS (the whole
world outside the US). This analysis asks a simple question: **over the next ten years, 2026 to
2035, how does that money grow or shrink under six different futures, and does the split between
the two funds matter?**

**The six futures.** Steady growth. A 2008-sized crash in year three. The US stalls while the rest
of the world runs. The reverse. A lost decade where nothing moves. And a replay of what actually
happened from 2016 to 2025, read as "what if the next ten years look like the last ten". The
numbers are anchored to real history, dividends included and reinvested, and the account is
treated as a 401(k), so there is no tax to subtract.

**What you can play with.** The dashboard is five short chapters with a sidebar. Each chapter
puts its controls on top and the chart they change right underneath: a slider for your split (0%
to 100% in VTI), a choice between rebalancing every year and never touching it, a scenario
picker, a box for the starting balance, and an inflation slider that shrinks every figure to
today's money. Only the controls that change a chapter appear on it. The web address remembers
your settings, so you can send a colleague "look at 80/20 in the crash".

**What you see.** Your balance year by year under every future, drawn as a shaded band from worst
to best. Whether 65/35 beat 100/0 or 50/50 in the future you picked. A colour-shaded grid of
ending balances and effective yearly rates. How far your mix drifts if you never rebalance. And
the numbers that decide whether someone panics: the worst single year, the deepest fall, how many
years it takes to recover, and the year the money first doubles.

**What it deliberately leaves out.** There is no "average of the six futures". The scenarios are
not equally likely, and averaging them would give a number that looks precise and means little.

**Swapping funds.** VTI and VXUS are settings, not hard-wired. Any fund with ten years of returns
for every scenario can take either seat; the run stops with a clear message if one is missing.

**How it gets onto the platform.** Review and merge the pull request. A small automated build then
packages the analysis into a container image and prints the exact reference to register as a job
definition. The pretend data is not in the image; the real job reads the real data.

**Honesty note.** The scenario returns are assumptions built from history, not forecasts. The
dashboard shows what *would* happen if a future played out that way. It does not say which one will.
