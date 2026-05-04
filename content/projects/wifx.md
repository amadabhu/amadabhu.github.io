---
order: 2
slug: wifx
name: WIFX
status: shipped
highlight: true
one_liner: Women's International Football Rankings — analytics dashboard live at wifxfootball.com.
stack:
  - Python
  - scikit-learn
  - XGBoost
  - PyTorch
  - Hugging Face Spaces
  - GitHub Actions
links:
  - { label: "Live site", url: "https://wifxfootball.com/lab/global-player-rankings/" }
---

A composite-metric ranking system for women's football across players, club teams,
national teams, and confederations. 

Match predictions are produced by : <br/>
 - Poisson goal models <br/>
 - Gradient-boosted trees <br/>
 - Small neural nets <br/>
 - Ensemble models <br/>

Then, selected by 5-fold time-series CV log-loss high-confidence calls require agreement across a 12-model
consensus panel split into distinct model families.

