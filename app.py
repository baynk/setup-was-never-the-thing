"""
Interactive companion demos for "Nobody can teach you trading the way retail wants it taught"
================================================================================================

Five Plotly simulations matched to the article's image markers.

Run modes
---------
1. As a Streamlit app (recommended for Substack readers):
       pip install streamlit plotly numpy
       streamlit run app.py

   Deploy free on Streamlit Community Cloud (streamlit.io/cloud) and link from each
   section of the Substack post.

2. Generate self-contained HTML files for hosting on GitHub Pages, Netlify, Vercel:
       python app.py --export-html

   Outputs ./html/<demo>.html — each is a single file with Plotly bundled, no server
   needed. Iframe these from Substack if your plan supports custom embeds.

3. Generate static PNGs for inline Substack images:
       pip install kaleido
       python app.py --export-png

   Outputs ./png/<demo>.png at 1600x900. Drop these directly into Substack as images.

Demos
-----
1. short_run_vs_long_run        → [IMAGE: short run lies, long run reveals]
2. fixed_vs_dynamic_edge        → [IMAGE: fixed edge vs dynamic edge]
3. policy_makes_the_path        → [IMAGE: policy changes wealth path]
4. sizing_and_ruin              → [IMAGE: sizing and ruin]
5. state_action_ev_heatmap      → [IMAGE: state-action EV heatmap]
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# ---------------------------------------------------------------------------
# Shared styling — clean look that reads on Substack's white background
# ---------------------------------------------------------------------------

COLOR_A = "rgba(0, 200, 200, 0.9)"   # cyan — "good" trader / positive EV / professional
COLOR_B = "rgba(220, 60, 90, 0.9)"   # red — "bad" trader / negative EV / retail
COLOR_THEORY = "rgba(120, 120, 120, 0.7)"  # dashed reference line for true EV
COLOR_CASINO = "rgba(40, 180, 90, 0.9)"  # green — casino / house

LAYOUT_DEFAULTS = dict(
    plot_bgcolor="white",
    paper_bgcolor="white",
    font=dict(color="#1a1a1a", family="Inter, system-ui, sans-serif"),
    margin=dict(l=60, r=40, t=70, b=60),
)

AXIS_DEFAULTS = dict(
    showgrid=True,
    gridwidth=1,
    gridcolor="rgba(0,0,0,0.08)",
    zeroline=True,
    zerolinewidth=1,
    zerolinecolor="rgba(0,0,0,0.15)",
    linecolor="rgba(0,0,0,0.3)",
    ticks="outside",
    tickcolor="rgba(0,0,0,0.3)",
)


def _apply_axes(fig, n_cols=1):
    for i in range(1, n_cols + 1):
        fig.update_xaxes(**AXIS_DEFAULTS, row=1, col=i)
        fig.update_yaxes(**AXIS_DEFAULTS, row=1, col=i)


# ---------------------------------------------------------------------------
# Demo 1 — Short run lies, long run reveals
# ---------------------------------------------------------------------------

def short_run_vs_long_run(
    n_trades: int = 50,
    edge_a_per_trade: float = 1.0,   # positive expected value per trade ($)
    edge_b_per_trade: float = -1.0,  # negative expected value per trade ($)
    win_size: float = 100.0,
    starting_wealth: float = 10_000.0,
    seed: int = 40,
) -> go.Figure:
    """
    Two traders. Same starting wealth. Same trade size. Different underlying edge.
    Slider n_trades from ~20 (noise dominates) to ~2000 (edge dominates).

    Trader A has small positive edge per trade.
    Trader B has small negative edge per trade.

    The whole point: at n_trades=50, the curves can cross or look indistinguishable.
    At n_trades=2000, the edge is undeniable. Short run lies. Long run reveals.
    """
    rng = np.random.default_rng(seed)

    # Solve for win prob given edge: edge = p * win - (1-p) * win  =>  p = 0.5 + edge / (2*win)
    p_a = 0.5 + edge_a_per_trade / (2 * win_size)
    p_b = 0.5 + edge_b_per_trade / (2 * win_size)

    outcomes_a = (rng.random(n_trades) < p_a).astype(int) * 2 - 1
    outcomes_b = (rng.random(n_trades) < p_b).astype(int) * 2 - 1

    pnl_a = np.concatenate([[starting_wealth], starting_wealth + np.cumsum(outcomes_a * win_size)])
    pnl_b = np.concatenate([[starting_wealth], starting_wealth + np.cumsum(outcomes_b * win_size)])

    x = np.arange(n_trades + 1)
    theoretical_a = starting_wealth + edge_a_per_trade * x
    theoretical_b = starting_wealth + edge_b_per_trade * x

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=(
            f"Trader A — true edge ≈ ${edge_a_per_trade:+.2f}/trade",
            f"Trader B — true edge ≈ ${edge_b_per_trade:+.2f}/trade",
        ),
        horizontal_spacing=0.10,
    )

    fig.add_trace(go.Scatter(x=x, y=pnl_a, mode="lines",
                             line=dict(color=COLOR_A, width=2),
                             name="Realized wealth", showlegend=False), row=1, col=1)
    fig.add_trace(go.Scatter(x=x, y=theoretical_a, mode="lines",
                             line=dict(color=COLOR_THEORY, width=2, dash="dash"),
                             name="True EV line", showlegend=False), row=1, col=1)

    fig.add_trace(go.Scatter(x=x, y=pnl_b, mode="lines",
                             line=dict(color=COLOR_B, width=2),
                             showlegend=False), row=1, col=2)
    fig.add_trace(go.Scatter(x=x, y=theoretical_b, mode="lines",
                             line=dict(color=COLOR_THEORY, width=2, dash="dash"),
                             showlegend=False), row=1, col=2)

    fig.update_layout(
        height=460, **LAYOUT_DEFAULTS,
        title=dict(
            text=f"Short run lies, long run reveals — n = {n_trades} trades",
            font=dict(size=18),
        ),
    )
    _apply_axes(fig, n_cols=2)
    fig.update_xaxes(title_text="Number of trades", row=1, col=1)
    fig.update_xaxes(title_text="Number of trades", row=1, col=2)
    fig.update_yaxes(title_text="Wealth ($)", row=1, col=1)
    return fig


# ---------------------------------------------------------------------------
# Demo 2 — Fixed edge vs dynamic edge
# ---------------------------------------------------------------------------

def fixed_vs_dynamic_edge(
    n_bets: int = 1000,
    n_players: int = 10,
    starting_wealth: float = 10_000.0,
    bet_size: float = 100.0,
    seed: int = 7,
) -> go.Figure:
    """
    Left panel: 10 players grinding on roulette (American wheel, p_win = 18/38).
    The casino's positive EV expresses itself with the regularity of physics.

    Right panel: 10 traders in the same market, but edge is state-conditioned —
    regime flips every 200 bars. Favorable regime: +0.7%/trade. Unfavorable: -0.4%/trade.
    On average across regimes the market is mildly positive, but a trader who can't
    distinguish the regime is forced to take both, eating the bad with the good.
    The point: in a fixed-edge game the wheel does the work; in a dynamic-edge game
    the trader has to read state to capture the edge that's actually there.
    """
    rng = np.random.default_rng(seed)

    # ---- Roulette (fixed negative edge) ----
    p_win = 18 / 38
    player_paths = np.full((n_players, n_bets + 1), starting_wealth, dtype=float)
    active = np.ones(n_players, dtype=bool)

    for t in range(n_bets):
        for p in range(n_players):
            if active[p] and player_paths[p, t] >= bet_size:
                won = rng.random() < p_win
                delta = bet_size if won else -bet_size
                player_paths[p, t + 1] = player_paths[p, t] + delta
            else:
                active[p] = False
                player_paths[p, t + 1] = player_paths[p, t]

    # ---- Trading (dynamic, state-conditioned edge) ----
    # Regime alternates every 200 bars. Favorable: +0.7%/trade. Unfavorable: -0.4%/trade.
    # Mean across regimes ≈ +0.15%/trade, so edge is genuinely there on average — but
    # only captured by a trader who acts on state. A blind trader gets the average
    # eaten by vol drag.
    regime = (np.arange(n_bets) // 200) % 2  # 0,0,...,1,1,...,0,0,...
    edges_pct = np.where(regime == 1, 0.007, -0.004)

    trader_paths = np.full((n_players, n_bets + 1), starting_wealth, dtype=float)
    for p in range(n_players):
        rets = rng.normal(loc=edges_pct, scale=0.02, size=n_bets)
        trader_paths[p, 1:] = starting_wealth * np.exp(np.cumsum(rets))

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=(
            "Roulette — fixed negative edge (the wheel doesn't care)",
            "Trading — edge depends on the regime you're in",
        ),
        horizontal_spacing=0.10,
    )

    x = np.arange(n_bets + 1)
    for p in range(n_players):
        fig.add_trace(go.Scatter(x=x, y=player_paths[p], mode="lines",
                                 line=dict(color=COLOR_B, width=1.2),
                                 opacity=0.5, showlegend=False), row=1, col=1)

    expected_player = starting_wealth + (p_win * bet_size - (1 - p_win) * bet_size) * x
    fig.add_trace(go.Scatter(x=x, y=expected_player, mode="lines",
                             line=dict(color=COLOR_THEORY, width=2, dash="dash"),
                             showlegend=False), row=1, col=1)

    for p in range(n_players):
        fig.add_trace(go.Scatter(x=x, y=trader_paths[p], mode="lines",
                                 line=dict(color=COLOR_A, width=1.2),
                                 opacity=0.5, showlegend=False), row=1, col=2)

    # Shade the favorable regime windows on the right panel
    for k in range(n_bets // 200):
        if k % 2 == 1:  # favorable
            fig.add_vrect(x0=k * 200, x1=(k + 1) * 200,
                          fillcolor="rgba(0, 180, 120, 0.06)",
                          layer="below", line_width=0,
                          row=1, col=2)

    fig.update_layout(
        height=460, **LAYOUT_DEFAULTS,
        title=dict(text="Fixed edge vs dynamic edge", font=dict(size=18)),
    )
    _apply_axes(fig, n_cols=2)
    fig.update_xaxes(title_text="Number of bets", row=1, col=1)
    fig.update_xaxes(title_text="Number of trades", row=1, col=2)
    fig.update_yaxes(title_text="Wealth ($)", row=1, col=1)
    return fig


# ---------------------------------------------------------------------------
# Demo 3 — Policy makes the wealth path
# ---------------------------------------------------------------------------

def policy_makes_the_path(
    n_hands: int = 1000,
    bet_size: float = 10.0,
    starting_wealth: float = 10_000.0,
    seed: int = 11,
) -> go.Figure:
    """
    Same blackjack environment, two policies.
    π_1: stay at 16+
    π_2: hit until 20

    Both are losing policies in absolute terms, but π_1 loses noticeably less.
    The point isn't blackjack. The point is: the policy you choose changes the
    distribution you sample from. Same game, same cards, different action rule,
    different wealth path.
    """
    rng = np.random.default_rng(seed)

    def hand_value(hand):
        total = sum(11 if c == 1 else min(c, 10) for c in hand)
        aces = sum(1 for c in hand if c == 1)
        while total > 21 and aces > 0:
            total -= 10
            aces -= 1
        return total

    def play_one_policy(deck, stay_threshold):
        """Play one hand from the given deck (mutates the deck copy passed in)."""
        if len(deck) < 4:
            return 0
        player = [deck.pop(), deck.pop()]
        dealer = [deck.pop(), deck.pop()]
        while hand_value(player) < stay_threshold and deck:
            player.append(deck.pop())
        if hand_value(player) > 21:
            return -1
        while hand_value(dealer) < 17 and deck:
            dealer.append(deck.pop())
        if hand_value(dealer) > 21:
            return 1
        if hand_value(player) > hand_value(dealer):
            return 1
        if hand_value(player) < hand_value(dealer):
            return -1
        return 0

    wealth_pi1 = np.full(n_hands + 1, starting_wealth, dtype=float)
    wealth_pi2 = np.full(n_hands + 1, starting_wealth, dtype=float)
    for i in range(n_hands):
        # Same shuffled deck for both policies — honest apples-to-apples comparison.
        deck = [v for v in range(1, 14)] * 4
        rng.shuffle(deck)
        wealth_pi1[i + 1] = wealth_pi1[i] + bet_size * play_one_policy(list(deck), 16)
        wealth_pi2[i + 1] = wealth_pi2[i] + bet_size * play_one_policy(list(deck), 20)

    ev_pi1 = (wealth_pi1[-1] - starting_wealth) / n_hands
    ev_pi2 = (wealth_pi2[-1] - starting_wealth) / n_hands

    x = np.arange(n_hands + 1)
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=(
            f"π₁: stay at 16+    realized EV ≈ ${ev_pi1:+.2f}/hand",
            f"π₂: hit until 20  realized EV ≈ ${ev_pi2:+.2f}/hand",
        ),
        horizontal_spacing=0.10,
    )
    fig.add_trace(go.Scatter(x=x, y=wealth_pi1, mode="lines",
                             line=dict(color=COLOR_A, width=2),
                             showlegend=False), row=1, col=1)
    fig.add_trace(go.Scatter(x=x, y=wealth_pi2, mode="lines",
                             line=dict(color=COLOR_B, width=2),
                             showlegend=False), row=1, col=2)

    fig.update_layout(
        height=460, **LAYOUT_DEFAULTS,
        title=dict(text="Same game, different policy, different wealth path",
                   font=dict(size=18)),
    )
    _apply_axes(fig, n_cols=2)
    fig.update_xaxes(title_text="Number of hands", row=1, col=1)
    fig.update_xaxes(title_text="Number of hands", row=1, col=2)
    fig.update_yaxes(title_text="Wealth ($)", row=1, col=1)
    return fig


# ---------------------------------------------------------------------------
# Demo 4 — Sizing and ruin
# ---------------------------------------------------------------------------

def sizing_and_ruin(
    edge_per_trade: float = 0.01,     # 1% raw mean return — small but real edge
    vol_per_trade: float = 0.20,      # 20% raw sigma per trade (realistic for risk assets)
    fraction_of_bankroll: float = 0.50,  # SLIDER — fraction risked per trade
    n_trades: int = 300,
    n_paths: int = 250,
    starting_wealth: float = 10_000.0,
    ruin_floor: float = 1_000.0,      # consider <10% of starting capital as "ruined"
    seed: int = 99,
) -> go.Figure:
    """
    Identical edge. Identical underlying signal. The ONLY thing that changes
    is bet sizing. Slider for fraction_of_bankroll from 1% to 100%.

    At small fractions, the edge expresses itself cleanly.
    At large fractions, drawdowns become path-dependent and many sample paths
    get ruined before convergence — even though the average return is still
    positive in theory.

    This is the single sharpest empirical demonstration that "sizing is policy,
    not decoration."
    """
    rng = np.random.default_rng(seed)

    # Per-trade signal is N(edge, vol) — these are the underlying market returns when
    # you bet the full bankroll. fraction_of_bankroll scales every trade linearly:
    # at fraction=1.0 you take the raw return, at fraction=0.5 you take half, etc.
    # The clip is symmetric so we don't introduce a bias on either tail. At fraction=1.0
    # a -100% trade wipes the account, which is the whole pedagogical point.
    paths = np.full((n_paths, n_trades + 1), starting_wealth, dtype=float)
    for p in range(n_paths):
        for t in range(n_trades):
            if paths[p, t] <= 0:
                paths[p, t + 1] = 0
                continue
            ret = rng.normal(loc=edge_per_trade, scale=vol_per_trade)
            scaled = ret * fraction_of_bankroll
            scaled = np.clip(scaled, -fraction_of_bankroll, fraction_of_bankroll)
            paths[p, t + 1] = paths[p, t] * (1 + scaled)

    final = paths[:, -1]
    median = np.median(final)
    ruin_rate = float(np.mean(final < ruin_floor))

    fig = make_subplots(rows=1, cols=2,
                        subplot_titles=(
                            f"{n_paths} sample wealth paths "
                            f"(risking {fraction_of_bankroll*100:.0f}% per trade)",
                            "Distribution of final wealth",
                        ),
                        column_widths=[0.62, 0.38],
                        horizontal_spacing=0.12)

    x = np.arange(n_trades + 1)
    for p in range(n_paths):
        ruined = final[p] < ruin_floor
        fig.add_trace(go.Scatter(
            x=x, y=paths[p], mode="lines",
            line=dict(color=COLOR_B if ruined else COLOR_A, width=0.8),
            opacity=0.25,
            showlegend=False,
        ), row=1, col=1)

    fig.add_hline(y=ruin_floor, line=dict(color="rgba(0,0,0,0.4)", width=1, dash="dot"),
                  row=1, col=1, annotation_text="ruin floor", annotation_position="bottom right")

    # Floor zero/near-zero finals at 1 so they show on the log axis as the "ruined" bin.
    final_for_hist = np.where(final < 1, 1, final)
    fig.add_trace(go.Histogram(
        y=np.log10(final_for_hist), nbinsy=40,
        marker=dict(color=COLOR_A, line=dict(color="rgba(0,0,0,0.2)", width=0.5)),
        showlegend=False,
    ), row=1, col=2)

    fig.update_layout(
        height=520, **LAYOUT_DEFAULTS,
        title=dict(
            text=(f"Sizing and ruin — edge {edge_per_trade*100:+.2f}%/trade, "
                  f"σ {vol_per_trade*100:.1f}%, ruin rate {ruin_rate*100:.1f}%, "
                  f"median final ${median:,.0f}"),
            font=dict(size=16),
        ),
        bargap=0.05,
    )
    _apply_axes(fig, n_cols=2)
    fig.update_xaxes(title_text="Number of trades", row=1, col=1)
    fig.update_yaxes(title_text="Wealth ($)", row=1, col=1, type="log")
    fig.update_xaxes(title_text="Path count", row=1, col=2)
    fig.update_yaxes(
        title_text="Final wealth ($, log scale)", row=1, col=2,
        tickvals=[0, 1, 2, 3, 4, 5, 6],
        ticktext=["$1", "$10", "$100", "$1k", "$10k", "$100k", "$1M"],
    )
    return fig


# ---------------------------------------------------------------------------
# Demo 5 — State-action EV heatmap
# ---------------------------------------------------------------------------

def state_action_ev_heatmap() -> go.Figure:
    """
    A toy Q(s, a) heatmap to make the article's claim concrete:
    edge doesn't live in the pattern, it lives in the (state, action) pair.

    Rows: states defined by (volatility regime, prior move).
    Cols: actions (buy breakout, fade breakout, no trade, reduce, etc.).
    Cell color: expected value in basis points per trade.

    The same "buy breakout" action is brilliantly +EV in some states and
    sharply -EV in others. The same state has multiple +EV actions in some
    cases and zero +EV actions in others (where 'no trade' is correct).
    """
    states = [
        "Compression + low vol",
        "Compression + high vol",
        "Trend day, early",
        "Trend day, late",
        "Range + thin liquidity",
        "Post-catalyst, dust settling",
        "Drawdown + tilted",
        "Pre-FOMC, 30 min out",
    ]
    actions = [
        "Buy breakout",
        "Fade breakout",
        "Buy pullback",
        "Reduce",
        "No trade",
    ]

    # EV in basis points per trade. Hand-curated to illustrate the article's claim.
    ev = np.array([
        # Buy BO   Fade BO   Buy PB   Reduce   No trade
        [   45,     -55,       30,       0,       -2 ],   # Compression + low vol
        [   18,     -40,       12,       0,       -2 ],   # Compression + high vol
        [   60,     -85,       40,       0,       -3 ],   # Trend day, early
        [  -25,      35,       -5,      10,       -2 ],   # Trend day, late
        [  -30,      20,      -10,       5,        0 ],   # Range + thin liquidity
        [    8,      -8,        4,       0,        0 ],   # Post-catalyst
        [  -40,     -45,      -25,      25,       10 ],   # Drawdown + tilted
        [  -10,     -10,      -10,      15,       15 ],   # Pre-FOMC, 30 min out
    ])

    fig = go.Figure(data=go.Heatmap(
        z=ev, x=actions, y=states,
        colorscale=[
            [0.0, "rgba(180, 40, 60, 1)"],
            [0.5, "rgba(245, 245, 245, 1)"],
            [1.0, "rgba(20, 130, 150, 1)"],
        ],
        zmid=0,
        text=ev,
        texttemplate="%{text:+d}",
        textfont=dict(color="black", size=12),
        colorbar=dict(title="EV (bps)"),
        hovertemplate="State: %{y}<br>Action: %{x}<br>EV: %{z:+d} bps<extra></extra>",
    ))

    fig.update_layout(
        height=520, **LAYOUT_DEFAULTS,
        title=dict(
            text="Where expected value lives — Q(s, a) is the unit of analysis",
            font=dict(size=18),
        ),
    )
    fig.update_xaxes(title_text="Action", **AXIS_DEFAULTS)
    fig.update_yaxes(title_text="State", autorange="reversed", **AXIS_DEFAULTS)
    return fig


# ---------------------------------------------------------------------------
# Streamlit app — the main user-facing surface
# ---------------------------------------------------------------------------

def streamlit_app():
    import streamlit as st

    st.set_page_config(
        page_title="The setup was never the thing — interactive demos",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("The setup was never the thing")
    st.caption(
        "Interactive companion to the essay. Pick a demo. Move the sliders."
    )

    # Deep-link support: ?demo=short_run / fixed_edge / policy / sizing / heatmap
    demo_options = [
        "1. Short run lies, long run reveals",
        "2. Fixed edge vs dynamic edge",
        "3. Policy makes the wealth path",
        "4. Sizing and ruin",
        "5. Where expected value lives",
    ]
    query_to_index = {
        "short_run": 0, "1": 0,
        "fixed_edge": 1, "dynamic": 1, "2": 1,
        "policy": 2, "3": 2,
        "sizing": 3, "ruin": 3, "4": 3,
        "heatmap": 4, "ev": 4, "5": 4,
    }
    qp = st.query_params.get("demo", "")
    default_idx = query_to_index.get(qp.lower(), 0)
    section = st.sidebar.radio("Pick a demo", demo_options, index=default_idx)

    if section.startswith("1"):
        st.subheader("Short run lies, long run reveals")
        st.markdown(
            "Two traders. Same starting wealth. Same trade size. Trader A has a small "
            "positive edge. Trader B has a small negative edge. The dashed line is "
            "where each trader should be on average. The colored line is one actual run."
        )
        st.markdown(
            "Set trades to 50. Click the **+** on Random sample a few times. Sometimes "
            "B beats A. Sometimes neither line goes anywhere. Now drag trades to 5000 "
            "and click **+** again. A stays above its dashed line. B stays below. "
            "Same math both times. The only difference is how long you waited."
        )
        n = st.slider(
            "Number of trades", 20, 5000, 50, step=10,
            help="How long the simulation runs. At 50 trades, luck is most of what you see. "
                 "At 5,000, the edge starts to win. Real trading careers are somewhere "
                 "in between, which is why most traders never know if they're good or lucky.",
        )
        edge_a = st.slider(
            "Trader A edge per trade ($)", 0.0, 5.0, 1.0, step=0.1,
            help="Average dollars Trader A makes per trade in the long run. Real strategies "
                 "rarely have an edge this clean. Move this lower to see how a tiny edge "
                 "still wins eventually, but takes much longer to show up.",
        )
        edge_b = st.slider(
            "Trader B edge per trade ($)", -5.0, 0.0, -1.0, step=0.1,
            help="Same idea, but Trader B loses on average. Move this closer to zero and "
                 "B becomes nearly impossible to distinguish from a winning trader on "
                 "any reasonable sample size.",
        )
        seed = st.number_input(
            "Random sample (seed)", value=40, step=1,
            help="Each number is one random run of trades. Same trader, same edge, just "
                 "different luck. Click + to draw a fresh sample without changing anything "
                 "else. At low trade counts the path will look completely different every "
                 "time. That's the whole point. You wouldn't grade a coin as biased after "
                 "ten flips. Same logic for traders.",
        )
        st.plotly_chart(
            short_run_vs_long_run(n_trades=n, edge_a_per_trade=edge_a,
                                  edge_b_per_trade=edge_b, seed=int(seed)),
            use_container_width=True,
        )

    elif section.startswith("2"):
        st.subheader("Fixed edge vs dynamic edge")
        st.markdown(
            "Left panel: ten people grinding on roulette. The wheel pays the casino a "
            "fixed cut on every spin. Nobody adapts. Nobody reads anything. The math "
            "just runs."
        )
        st.markdown(
            "Right panel: ten traders in a market where the edge flips between favorable "
            "(shaded green) and unfavorable. A trader who can't tell the regimes apart "
            "is forced to take both. A trader who can read state only takes the green "
            "windows. Same market, different policy, different outcome."
        )
        n = st.slider(
            "Number of bets / trades", 200, 3000, 1000, step=100,
            help="More bets means more time for the casino edge to grind on the left, "
                 "and more regime flips visible on the right. Try low numbers first to "
                 "see how a short sample can hide what's actually going on.",
        )
        st.plotly_chart(fixed_vs_dynamic_edge(n_bets=n), use_container_width=True)

    elif section.startswith("3"):
        st.subheader("Policy makes the wealth path")
        st.markdown(
            "Two blackjack policies, same shuffled deck on every hand. The first stays "
            "at 16 or higher. The second hits until 20. Both lose money long term. "
            "One loses about six times faster than the other."
        )
        st.markdown(
            "Click **+** on the sample number a few times. The gap between the two "
            "policies shows up every run. The cards are identical. The dealer is identical. "
            "Only the action rule changes."
        )
        n = st.slider(
            "Number of hands", 100, 5000, 1000, step=100,
            help="Hands per simulation. More hands means the realized loss rate per hand "
                 "settles closer to the policy's true expected value.",
        )
        bet = st.slider(
            "Bet size ($)", 1, 100, 10,
            help="Just a multiplier. Bigger bets blow up the dollar amounts but don't "
                 "change which policy is better. Useful if you want the loss to feel "
                 "real instead of academic.",
        )
        seed = st.number_input(
            "Random sample (seed)", value=11, step=1, key="bj_seed",
            help="Reshuffles the deck. Same policies, different cards. The point of "
                 "trying a few values is to see that the bad policy doesn't get bailed "
                 "out by lucky shuffles. The math wins on every sample.",
        )
        st.plotly_chart(
            policy_makes_the_path(n_hands=n, bet_size=float(bet), seed=int(seed)),
            use_container_width=True,
        )

    elif section.startswith("4"):
        st.subheader("Sizing and ruin")
        st.markdown(
            "Same edge. Same signal. The only thing that changes is how much of your "
            "account you risk per trade. Cyan paths survived. Red paths got wiped out "
            "below 10% of starting capital."
        )
        st.markdown(
            "Start at 10% per trade. Almost nobody dies. Move to 50% — ruin shows up, "
            "median wealth flatlines. Move to 100% — most paths die even though the "
            "underlying edge is still positive. Sizing isn't about getting rich faster. "
            "It's about staying in the game long enough for the edge to do anything."
        )
        col1, col2, col3 = st.columns(3)
        with col1:
            frac = st.slider(
                "Fraction of bankroll per trade", 0.05, 1.00, 0.50, step=0.05,
                help="How much of your account is in the trade. 0.50 means half the "
                     "account is exposed and half is in cash. 1.00 means the whole "
                     "account is on the line every trade — which is how people get wiped "
                     "out even when their edge is real.",
            )
        with col2:
            edge = st.slider(
                "Underlying edge (%/trade)", -2.0, 5.0, 1.0, step=0.25,
                help="The asset's average return per trade before sizing. Most real "
                     "edges in trading are well under 1% per trade. Move this higher "
                     "and ruin is harder to trigger. Move it negative and you're paying "
                     "the casino.",
            ) / 100
        with col3:
            vol = st.slider(
                "Underlying volatility (%/trade)", 5.0, 40.0, 20.0, step=1.0,
                help=(
                    "How wild the asset is per trade, measured as standard deviation. "
                    "Rough rules of thumb: SPY held intraday is around 0.5–1%. A single "
                    "stock held a day is 2–4%. A leveraged ETF held a week is 10–15%. "
                    "Weekly options can be 30% or more. Default 20% is a volatile "
                    "single-name swing trade. At this volatility with a 1% edge, the "
                    "Kelly-optimal fraction is about 25%. Anything north of 50% means "
                    "you're overbetting and the path bleeds even when each trade has "
                    "positive expected value."
                ),
            ) / 100
        n_paths = st.slider(
            "Number of sample paths", 50, 1000, 200, step=50,
            help="How many traders we simulate side by side. More paths gives you a "
                 "more stable ruin-rate number, at the cost of a denser chart.",
        )
        st.plotly_chart(
            sizing_and_ruin(edge_per_trade=edge, vol_per_trade=vol,
                            fraction_of_bankroll=frac, n_paths=n_paths),
            use_container_width=True,
        )

    elif section.startswith("5"):
        st.subheader("Where expected value lives")
        st.markdown(
            "Edge doesn't live in the pattern. It lives in the (state, action) pair. "
            "Same action — buy breakout, fade breakout, whatever — has different "
            "expected value depending on what state you're in."
        )
        st.markdown(
            "Hover any cell. Look at *Buy breakout* across rows. It's +60 bps on an "
            "early trend day. It's −25 bps on a late trend day. Same action, different "
            "state, different trade. Now look at the *Drawdown + tilted* row. Every "
            "active trade has negative EV. The only correct moves are *Reduce* or "
            "*No trade*."
        )
        st.plotly_chart(state_action_ev_heatmap(), use_container_width=True)

    st.divider()
    st.caption(
        "Code: github.com/baynk/setup-was-never-the-thing  ·  "
        "Read the full essay on Substack."
    )


# ---------------------------------------------------------------------------
# CLI entry — export modes for hosting / static
# ---------------------------------------------------------------------------

DEMOS = {
    "short_run_vs_long_run": lambda: short_run_vs_long_run(n_trades=2000, seed=9),
    "fixed_vs_dynamic_edge": lambda: fixed_vs_dynamic_edge(),
    "policy_makes_the_path": lambda: policy_makes_the_path(),
    "sizing_and_ruin": lambda: sizing_and_ruin(),
    "state_action_ev_heatmap": lambda: state_action_ev_heatmap(),
}


def export_html(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, builder in DEMOS.items():
        fig = builder()
        path = out_dir / f"{name}.html"
        fig.write_html(str(path), include_plotlyjs="cdn", full_html=True)
        print(f"wrote {path}")


def export_png(out_dir: Path):
    try:
        import kaleido  # noqa: F401
    except ImportError:
        print("Install kaleido for PNG export:  pip install kaleido==0.2.1")
        return
    out_dir.mkdir(parents=True, exist_ok=True)
    # Width 1600 matches Substack's full-bleed image width. Scale 3 gives ~4800px
    # effective width — crisp on retina screens. Height respects each figure's
    # native aspect (heatmap is tall, time-series are wide).
    for name, builder in DEMOS.items():
        fig = builder()
        native_height = fig.layout.height or 600
        path = out_dir / f"{name}.png"
        fig.write_image(str(path), width=1600, height=native_height, scale=3)
        print(f"wrote {path}")


def main():
    parser = argparse.ArgumentParser(description="Interactive demos for the article.")
    parser.add_argument("--export-html", action="store_true",
                        help="Write self-contained HTML files to ./html/")
    parser.add_argument("--export-png", action="store_true",
                        help="Write static PNG files to ./png/  (requires kaleido)")
    args = parser.parse_args()

    here = Path(__file__).resolve().parent
    if args.export_html:
        export_html(here / "html")
    elif args.export_png:
        export_png(here / "png")
    else:
        # No CLI flags — try Streamlit
        try:
            import streamlit  # noqa: F401
            print("To run as a Streamlit app:    streamlit run app.py")
            print("To export interactive HTML:    python app.py --export-html")
            print("To export static PNG:          python app.py --export-png")
        except ImportError:
            print("Streamlit not installed. Use --export-html or --export-png.")


if __name__ == "__main__":
    # Streamlit invokes the file directly without argv — detect that.
    try:
        import streamlit.runtime
        if streamlit.runtime.exists():
            streamlit_app()
        else:
            main()
    except Exception:
        main()
