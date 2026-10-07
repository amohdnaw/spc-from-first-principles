# Newcomer test — the 24 questions and their answers

Written and committed 2026-10-07, before the reader started, so the scoring cannot
bend to what it says. Each answer lists what a correct reply must contain; wording
is free. A reply is **right** if it has every "must" point, **partial** if it has
some, **wrong** if it has none or contradicts one. The reader sees only the
questions, and only after finishing the level they belong to.

## Level 1 — Variation
1. Two runs of 240 measurements have exactly the same histogram, mean and spread.
   Can they come from processes that need different action, and if so what tells
   them apart?
   - must: yes; the order the measurements were made in (time order / a run
     statistic) — the histogram throws the order away.
2. An operator corrects the machine after every part by the full amount that part
   was off target. What happens to the variation, and why?
   - must: it gets worse — variance doubles (spread ×√2 ≈ 1.41); each result
     becomes the difference of two independent noise draws.

## Level 2 — Chance
3. A fair coin has just come up heads six times running. What is the chance the
   next flip is heads, and why?
   - must: one half; flips are independent, there is no memory or debt to repay.
4. A chart's false-alarm rate is 0.27 %, "one alarm in 370". Run 370 subgroups on a
   process where nothing has changed: is at least one false alarm certain?
   - must: no — about 63 % (1 − 1/e).

## Level 3 — Centre and spread
5. Why are deviations from the mean squared before they are averaged into a spread?
   - must: unsquared deviations from the mean cancel (sum to zero), so their
     average says nothing; squaring removes the signs.
6. Why does a sample's spread divide by n − 1 rather than n?
   - must: the sample sits tighter around its own mean than around the true
     mean, so dividing by n comes out too small; n − 1 corrects that.

## Level 4 — Variation is predictable
7. You average 4 parts at a time instead of looking at single parts. How does the
   spread of those averages compare with the spread of single parts?
   - must: half (σ/√4 — the spread shrinks by the square root of the count).
8. Why does a control chart plot subgroup means rather than individual parts?
   - must: means vary less (σ/√n), so a shift that hides in the noise of single
     parts moves the mean far enough to see.

## Level 5 — Estimation
9. With 5 parts, why build a 95 % interval with t rather than 1.96?
   - must: σ is itself estimated from the same few parts; 1.96 ignores that and
     the interval covers less than promised (≈88 %); t accounts for the small
     sample and delivers 95 %.
10. With σ known, you want an interval half as wide. How many parts do you need
    compared with now?
    - must: four times as many (precision goes with √n).

## Level 6 — Limits as a test
11. A subgroup mean lands outside the ±3σ limits. What does that point mean, and
    what should you do?
    - must: evidence that the process changed (against the null hypothesis), not
      a verdict on that part; go and find what changed (scrapping it changes
      nothing).
12. Where does "one false alarm in 370" come from?
    - must: 0.27 % of a normal distribution lies outside ±3σ (99.73 % inside);
      1 / 0.0027 ≈ 370.

## Level 7 — Evidence and decisions
13. The process mean moves by 1σ. What is the chance the very next point falls
    outside the 3σ limits?
    - must: about 2.3 % (it is missed ~97.7 % of the time, β = 0.977).
14. Turning on the extra run rules: what do they cost, and when are they worth it?
    - must: more false alarms (about four times: one in 91 instead of 377); worth
      it against small shifts (≈4.6× sooner at 1σ), buy almost nothing against
      large ones (≈1.1× at 3σ).

## Level 8 — Capability
15. What is the difference between Cp and Cpk?
    - must: Cp is tolerance ÷ 6σ and ignores where the mean sits; Cpk uses the
      distance from the mean to the nearer spec limit ÷ 3σ, so it drops when the
      mean is off centre.
16. Why is moving from Cpk 1.33 to 1.67 more than a rounding argument?
    - must: the defect rate falls by about two orders of magnitude (≈33 ppm →
      ≈0.27 ppm).

## Level 9 — Detection
17. Why is a Shewhart chart slow to catch a slow drift?
    - must: it judges each point alone and forgets it (no memory); each point of
      a slow drift looks acceptable on its own.
18. EWMA caught the drift 4.4× sooner on average. Did it pay for that with more
    false alarms?
    - must: no — its limits were calibrated to the same false-alarm rate (one in
      370).

## Level 10 — Counting
19. Why does a p-chart or c-chart have no range chart beside it?
    - must: for counts the mean fixes the spread (binomial / Poisson), so the
      spread is not estimated separately.
20. You count defects (an item can carry several) and the number of items
    inspected varies each time. Which chart?
    - must: u-chart.

## Level 11 — Relationships
21. Adding ten columns of random noise to a regression raised R². Is the model
    better?
    - must: no; R² cannot fall when a predictor is added, so it rises even for
      noise (adjusted R² falls / check the residuals).
22. You want to predict the next single part at a given speed. Which of the two
    intervals do you quote, and why is it wider?
    - must: the interval for a single new reading (prediction interval), not the
      one for the mean; it includes the new reading's own variance, so it never
      shrinks below the process noise.

## Level 12 — Experiments
23. Why can changing one factor at a time settle on the wrong setting even with
    perfect, noise-free measurements?
    - must: the factors interact; one at a time never visits the corner where
      both are changed together, so it cannot see or estimate the interaction.
24. Why add centre points to a two-level design?
    - must: to detect curvature — the corners cannot (the quadratic term is the
      same at every corner); the gap between the corner mean and the centre mean
      tests it.
