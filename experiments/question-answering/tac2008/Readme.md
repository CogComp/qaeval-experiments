This directory contains the code to reproduce the expert QA results on the TAC 2008 dataset.

Required data:
- `data/tac2008/{summaries,metrics,pyramids,pyramid-annotations}.jsonl`

Required environments:
- `QAEVAL_ENV`
- `TRANSFORMERS_ENV`
- `MOVERSCORE_ENV`
- `APES_ENV`

Included data:
- `input/{candidates,questions}.jsonl`: The candidate answers and automatic questions from the `answer-selection` experiment (all NPs)
- `output/expert/{mturk,holes}-outputs.csv`: The human annotated QA pairs
- `output/answer-verification/labeled-answers.csv`: The human annotated answer verification data

To reproduce the results, run
```
sh experiments/question-answering/tac2008/run.sh
```

After the `run.sh` script finishes, the metric correlations (Table 3) will be written to the following locations:
- `output/baselines/correlations/rouge-X.json`: The summary-level ROUGE correlations on the labeled subset
- `output/baselines/correlations/MoverScore.json`: The summary-level MoverScore correlations on the labeled subset
- `output/baselines/correlations/APES.json`: The summary-level APES correlations on the labeled subset
- `output/baselines/pyramid-score/correlations.json`: The summary-level Pyramid Score correlations on the labeled subset
- `output/model/correlations/f1.json`: The summary-level correlations with model QA and F1 answer verification
- `output/expert/correlations/f1.json`: The summary-level correlations with human QA and F1 answer verification
- `output/answer-verification/model/correlations/human-is-correct.json`: The summary-level correlations with model QA and human answer verification
- `output/answer-verification/expert/correlations/human-is-correct.json`: The summary-level correlations with human QA and human answer verification

The QA metrics (Table 2) will be written to `output/squad-metrics.json` and `output/answer-verification/log.txt`.
The first file contains the is-answerable F1 (`is_answerable -> unweighted -> f1`) and the EM/F1 scores on just the subset of the data which is answerable (`is-answerable-only -> squad -> exact-match/f1`).
The second file contains the human labeled answer accuracy given the question is answerable (`Accuracy given ground-truth question is answerable 0.8429003021148036`).