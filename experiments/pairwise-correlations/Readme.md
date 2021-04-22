This directory contains the code to reproduce the pairwise correlations between ROUGE, APES, and QAEval (Figure 5).

First, run APES and QAEval end-to-end using these scripts:
```
sh experiments/end-to-end/apes/run.sh
sh experiments/end-to-end/qaeval/run.sh
```
They will produce scores files in the following locations which are used by this script:
- `experiments/end-to-end/{apes,qaeval}/output/tac2008/scores.jsonl`

The other required input are the TAC 2008 scores:
- `data/tac2008/metrics.jsonl`

Required environments:
- `QAEVAL_ENV`

Then, run:
```
sh experiments/pairwise-correlations/run.sh
```
The heatmaps will be written to `experiments/pairwise-correlations/output/plots`.
We reported the `global-pearson.pdf` in the paper.