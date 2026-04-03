# TradeLoop — Product Strategy

## The Market Reality

| Segment | Size | Pain | Willingness to Pay |
|---------|------|------|-------------------|
| Indian retail traders | 44M active (216M demat accounts) | No serious journal tool with native broker integration | Low ($5-15/mo) but massive volume |
| Prop firm traders globally | 1M+ active, 1.2M funded accounts | 93% fail. Most fail from rule violations, not bad trading | High ($20-50/mo) — a failed $500 challenge makes $20/mo obvious |
| Prop firms themselves (B2B) | 145 active firms, FTMO does $329M/yr | Need tools to reduce trader blowouts and payout disputes | Very high (custom pricing per firm) |
| Crypto/Forex traders | 50M+ on TradingView | Scattered across MT4/MT5, no unified journal | Medium ($15-30/mo) |

## What Nobody Has Built

**TradesViz** ($19-39/mo) comes closest for India but has zero prop firm features.
**PropJournal/PassTraq** have compliance but zero Indian broker support.
**TradeZella** ($29-49/mo) has 500+ broker imports but no counterfactual analysis and no prop compliance engine.
**EdgeWonk** ($197/yr) has psychology tracking but no broker sync and an outdated UI.

The whitespace: **Indian broker auto-sync + prop firm compliance + counterfactual dollar-value insights.** Nobody occupies all three.

## Our Unfair Advantage

**The Counterfactual Engine.** Every other journal says "you revenge traded 12 times." We say "revenge trading cost you exactly $47,230. Here is your equity curve without those trades. Here is how much you save per month if you stop." No competitor does this. This is our TradingView-style "Delta 4" moment — the old way of journaling feels broken after seeing this.

## The TradingView Playbook (Applied to Journals)

TradingView won because of 5 things:

1. **Social network, not a tool** — We add sharable weekly report cards (Grade A-F). Traders share their grade. Viral loop.
2. **Developer ecosystem** — TradingView had Pine Script. We have a prop firm rule engine that firms can customize. Each firm preset is our "Pine Script indicator."
3. **Embeddable distribution** — TradingView put free widgets on 20,000 sites. We make sharable insight cards ("Revenge trading cost me $47K this month") that traders post on X/Reddit.
4. **Freemium with genuinely useful free tier** — 50 trades/month free with full insights. Good enough to get hooked.
5. **Instant time-to-value** — Upload CSV → see your first dollar-valued insight in under 60 seconds. No 30-day wait.

## Year 1 Milestones

| Quarter | Goal | Metric |
|---------|------|--------|
| Q1 | Launch MVP, get first 100 users | 100 registered, 20 paid |
| Q2 | Zerodha Kite Connect live, prop compliance | 1,000 users, 100 paid |
| Q3 | Community features (shareable reports, leaderboard) | 5,000 users, 500 paid |
| Q4 | First prop firm B2B deal, Angel One integration | 10,000 users, 1,000 paid, 1 B2B |

## Revenue Targets

| Tier | Price | Target Users (Y1) | ARR |
|------|-------|-------------------|-----|
| Free | $0 | 8,000 | $0 |
| Pro | $12/mo | 700 | $100,800 |
| Prop Trader | $18/mo | 250 | $54,000 |
| B2B (prop firms) | $500/mo | 2 | $12,000 |
| **Total Y1** | | **~10,000** | **~$167K** |

## What We Build Next (Priority Order)

1. **Make the landing page undeniable** — hero dashboard screenshot, live demo mode, social proof counter
2. **One-click demo** — let visitors explore the full dashboard with sample data without registering
3. **Polish the Insights page** — this is the product. Make it feel like Bloomberg, not Bootstrap
4. **Real broker sync** — Zerodha Kite Connect with actual OAuth flow
5. **Shareable insight cards** — "Revenge trading cost me $47K" as a tweetable image/link
6. **Prop firm compliance alerts** — Telegram/email when approaching limits

## Identity

TradeLoop is not a trading journal. It is a **trading behavior engine** that computes the exact dollar cost of every mistake you make and tells you how to fix it. Other tools show you numbers. We show you money you're leaving on the table and give you the specific change to make tomorrow morning.

**Tagline:** "Stop losing money to yourself."
