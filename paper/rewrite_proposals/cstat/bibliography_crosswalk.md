# Verified bibliography and claim boundaries

Primary source records checked on **2026-11-13**. This is a targeted crosswalk,
not a systematic literature review or a claim that the four papers exhaust the
relevant work. Existing unrelated bibliography entries are not newly verified.

| Work and verified metadata | Relevant established result | COMET comparison and proposed citation |
|---|---|---|
| Nikos Karampatziakis, Paul Mineiro, Aaditya Ramdas. *Off-Policy Confidence Sequences*. ICML 2021, PMLR 139:5301–5310. [Publisher record](https://proceedings.mlr.press/v139/karampatziakis21a.html) | Contextual-bandit OPE bounds that hold uniformly over time and at arbitrary stopping times. | COMET's proved independent-block, fixed-window CI does not supply this sequential guarantee. New key `karampatziakis2021sequences`; do not claim the first off-policy certificate or deployment guarantee. |
| Mikael Møller Høgsgaard, Andrea Paudice. *Uniform Mean Estimation for Heavy-Tailed Distributions via Median-of-Means*. ICML 2025, PMLR 267:23357–23381. [Publisher record](https://proceedings.mlr.press/v267/hogsgaard25a.html) | Simultaneous function-class mean estimation with finite p moments for 1<p≤2. | COMET's finite-family union bound and exact-majority selector are not a new general theory of uniform heavy-tail estimation. New key `hogsgaard2025uniform`; theorem differences arise from the explicit conditional graph/block setup. |
| Mohammad Mehrabi, Stefan Wager. *Off-Policy Evaluation in Markov Decision Processes under Weak Distributional Overlap*. arXiv:2402.08201, first submitted 2024-02-13; current v2 dated 2025-09-28. [Author manuscript record](https://arxiv.org/abs/2402.08201) | Truncated DR for MDP stationary-distribution overlap, including slower-rate regimes when the ratio lacks a second moment. | Retain existing key `mehrabi2024weak` as the first-posted year; distinguish that bibliographic year from the revised version inspected. COMET's finite-exposure conditional design and fixed moment envelope do not subsume this MDP setting. |
| Tatsuhiro Shimizu, Koichi Tanaka, Ren Kishimoto, Haruka Kiyohara, Masahiro Nomura, Yuta Saito. *Effective Off-Policy Evaluation and Learning in Contextual Combinatorial Bandits*. arXiv:2408.11202, 2024; author record says accepted at RecSys 2024. [Author manuscript record](https://arxiv.org/abs/2408.11202) | Factored action-space OPE/learning separating main and residual effects. | New key `shimizu2024combinatorial`; use verified arXiv metadata plus acceptance note rather than guessing proceedings pages or DOI. COMET's present binary-action simulation is not an empirical combinatorial-bandit extension. |

The related-work paragraphs are comparative statements of scope, not claims of
strict dominance. They remove the old implication that DR, cross-fitting,
coloring, MOM and pessimism become novel merely by placing them in one pipeline.
