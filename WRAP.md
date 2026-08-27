# Portfolio — Ammar, SPC Engineer

Three connected works on Statistical Process Control, plus a Python library.

## The pieces

| Work | File / path | What it is |
|---|---|---|
| 🏭 **Line of Sight** | `line-of-sight.html` | Interactive essay: four simulated production lines streaming live in the browser; one is drifting. Acts I–IV walk from raw numbers → control charts → capability → management translation. Vanilla JS, no dependencies. |
| 📐 **spc-lab** | `spc-lab/` | Python library: SPC formulas with nothing hidden. Control-chart constants derived by Monte Carlo and verified against AIAG Table B in tests. Includes formula sheets (`spc-lab/docs/`), 3b1b-style Manim videos, and a five-level curriculum ("Why SPC works"). |
| 🎓 **SPC from First Principles** | `index.html` | The front door and the curriculum hub in one page: an in-flow control chart whose four phases link to the levels they explain, the five-level syllabus, the narrated gallery video, and the shop-floor cases with two live labs (EWMA vs Shewhart, Gage R&R). Absorbed the old `spc-from-first-principles.html`, which is deleted. Contract: `specs/spc-landing-contract.md`. |
| 📚 **Levels** | `level-03.html` … `level-09.html` | One page per level, each with its narrated Manim act, numbered figures and equations. |

## Curriculum arc (in spc-lab)

0. **What the numbers mean** — mean, why spread is squared, where the bell comes from
1. **Variation is predictable** — σ/√n, why we chart means
2. **Control limits are a hypothesis test** — ±3σ = a bet at 370:1 odds
3. **Capability compares two distributions** — Cpk as an exact defect promise
4. **Detection theory** — EWMA vs Shewhart ARL, fairly calibrated

## Quick commands

```bash
# run tests
cd spc-lab && PYTHONPATH=src .venv/bin/python -m pytest tests -q

# regenerate formula sheets + level sheets
PYTHONPATH=src .venv/bin/python -m spclab.formula_sheets && PYTHONPATH=src .venv/bin/python -m spclab.level04 \
  && PYTHONPATH=src .venv/bin/python -m spclab.level06 && PYTHONPATH=src .venv/bin/python -m spclab.level08 \
  && PYTHONPATH=src .venv/bin/python -m spclab.level09

# re-render manim scenes (1080p60)
PYTHONPATH=src .venv/bin/manim -qh src/spclab/scenes.py SPCGallery   # etc.

# view the pieces
xdg-open index.html line-of-sight.html
```

## TODO / next session

- [ ] Replace placeholder name/email/LinkedIn/résumé links everywhere
- [ ] Swap case-study stories in Line of Sight for real projects
- [ ] GitHub repo + GitHub Pages deploy (single URL for recruiters)
- [ ] pandas-native chart classes, Gage R&R module, PyPI publish (see spc-lab README roadmap)
- [ ] Optional: HTML essay embedding all curriculum levels' videos (currently L2 & L4 only)
