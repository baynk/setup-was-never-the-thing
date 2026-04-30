# The setup was never the thing — interactive companion

Five Plotly demos for the Substack essay *"Nobody can teach you trading the
way retail wants it taught."* Built in the style of Roman Paolucci's Quant
Guild proof, adapted to the article's specific argument.

## What's in here

| File / folder | Purpose |
| --- | --- |
| `app.py` | Five demos as functions + Streamlit wrapper + CLI exporter |
| `requirements.txt` | Pin for Streamlit Cloud deploy |
| `html/` | Self-contained HTML files (one per demo, Plotly via CDN) |
| `png/` | Static 1600×900 PNGs for inline Substack use |

## Demos

| Demo | Article marker | Section |
| --- | --- | --- |
| `short_run_vs_long_run` | `[IMAGE: short run lies, long run reveals]` | Where expected value lives |
| `fixed_vs_dynamic_edge` | `[IMAGE: fixed edge vs dynamic edge]` | Fixed games and dynamic games |
| `policy_makes_the_path` | `[IMAGE: policy changes wealth path]` | What a policy actually is |
| `sizing_and_ruin` | `[IMAGE: sizing and ruin]` | Sizing is policy, not decoration |
| `state_action_ev_heatmap` | `[IMAGE: state-action EV heatmap]` | Where expected value lives |

The other `[IMAGE: ...]` markers in the article (decision loop, setup vs
policy, no-trade threshold, forecast vs policy, feedback contamination,
review/policy update, what can actually be taught) are conceptual diagrams —
they belong as static SVG/illustrations, not simulations.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Open http://localhost:8501. Pick a demo from the sidebar, move sliders.

## Publishing recipe (the one we're using)

Substack does **not** support arbitrary iframe embeds. So:

**For each `[IMAGE: ...]` marker in the article:**
1. Insert the matching PNG from `png/` as an image
2. Below the image, add a caption with a deep-link to the live demo:
   *"Want to move the sliders? [Open the live demo →]"*

That gives readers a complete, self-contained article (PNGs render in email
and on every Substack plan), plus an interactive escape hatch for anyone
who wants to play with the parameters.

### Step 1 — push to GitHub

```bash
cd setup_was_never_the_thing
git init
git add app.py requirements.txt README.md html/ png/ .gitignore
git commit -m "Initial commit"
gh repo create setup-was-never-the-thing --public --source=. --push
```

(If you don't have `gh`, create the repo on github.com and push manually.)

### Step 2 — deploy to Streamlit Cloud

1. Go to https://share.streamlit.io
2. Sign in with GitHub, click **New app**
3. Pick the repo, branch `main`, main file `app.py`
4. Click **Deploy**

You'll get a URL like `https://<handle>-setup-was-never-the-thing.streamlit.app`.

### Step 3 — paste these into Substack

Below each PNG, add a caption with the matching deep-link:

| Article marker | PNG to upload | Deep-link to caption |
| --- | --- | --- |
| `[IMAGE: short run lies, long run reveals]` | `png/short_run_vs_long_run.png` | `https://<your-app>.streamlit.app/?demo=short_run` |
| `[IMAGE: fixed edge vs dynamic edge]` | `png/fixed_vs_dynamic_edge.png` | `https://<your-app>.streamlit.app/?demo=fixed_edge` |
| `[IMAGE: policy changes wealth path]` | `png/policy_makes_the_path.png` | `https://<your-app>.streamlit.app/?demo=policy` |
| `[IMAGE: sizing and ruin]` | `png/sizing_and_ruin.png` | `https://<your-app>.streamlit.app/?demo=sizing` |
| `[IMAGE: state-action EV heatmap]` | `png/state_action_ev_heatmap.png` | `https://<your-app>.streamlit.app/?demo=heatmap` |

The deep-links open Streamlit on the right demo automatically.

## Regenerating outputs

If you tweak `app.py`:

```bash
python app.py --export-html       # writes html/<demo>.html
python app.py --export-png        # writes png/<demo>.png  (needs kaleido==0.2.1)
```

For PNG export specifically, use `pip install kaleido==0.2.1`. Newer kaleido
versions have a regression that breaks Plotly's `write_image()`.

## How the demos relate to Roman's notebook

Roman's notebook proves the same thesis with fewer interactive controls (his
demos run inside Jupyter). Parameter choices that match his version:
roulette `18/38`, blackjack stay-16-vs-hit-20, ten players grinding. The
sizing-and-ruin sweep and state-action heatmap are article-specific.

Credit Roman in the article footnote:
<https://github.com/romanmichaelpaolucci/Quant-Guild-Library>
