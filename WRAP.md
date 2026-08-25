# Portfolio — Ammar, SPC Engineer

Three connected works on Statistical Process Control, plus a Python library.

## The pieces

| Work | File / path | What it is |
|---|---|---|
| 🏭 **Line of Sight** | `line-of-sight.html` | Interactive essay: four simulated production lines streaming live in the browser; one is drifting. Acts I–IV walk from raw numbers → control charts → capability → management translation. Vanilla JS, no dependencies. |
| 📐 **spc-lab** | `spc-lab/` | Python library: SPC formulas with nothing hidden. Control-chart constants derived by Monte Carlo and verified against AIAG Table B in tests. Includes formula sheets (`spc-lab/docs/`), 3b1b-style Manim videos, and a four-level curriculum ("Why SPC works"). |
| 🎓 **SPC from First Principles** | `spc-from-first-principles.html` | Flagship interactive essay tying the four-level curriculum together — embedded figures/videos from spc-lab plus two live interactives (threshold picker, Cpk→defects promise). Dark theme matches the Manim renders. |
| (earlier draft) | `index.html` | First portfolio page — superseded by the above; kept for reference. |

## Curriculum arc (in spc-lab)

1. **Variation is predictable** — σ/√n, why we chart means
2. **Control limits are a hypothesis test** — ±3σ = a bet at 370:1 odds
3. **Capability compares two distributions** — Cpk as an exact defect promise
4. **Detection theory** — EWMA vs Shewhart ARL, fairly calibrated

## Quick commands

```bash
# run tests
cd spc-lab && PYTHONPATH=src .venv/bin/python -m pytest tests -q

# regenerate formula sheets + level sheets
PYTHONPATH=src .venv/bin/python -m spclab.formula_sheets && PYTHONPATH=src .venv/bin/python -m spclab.level1 \
  && PYTHONPATH=src .venv/bin/python -m spclab.level2 && PYTHONPATH=src .venv/bin/python -m spclab.level3 \
  && PYTHONPATH=src .venv/bin/python -m spclab.level4

# re-render manim scenes (1080p60)
PYTHONPATH=src .venv/bin/manim -qh src/spclab/scenes.py SPCGallery   # etc.

# view the pieces
xdg-open line-of-sight.html spc-from-first-principles.html
```

## TODO / next session

- [ ] Replace placeholder name/email/LinkedIn/résumé links everywhere
- [ ] Swap case-study stories in Line of Sight for real projects
- [ ] GitHub repo + GitHub Pages deploy (single URL for recruiters)
- [ ] pandas-native chart classes, Gage R&R module, PyPI publish (see spc-lab README roadmap)
- [ ] Optional: HTML essay embedding all curriculum levels' videos (currently L2 & L4 only)
