This directory contains the code to reproduce the experiments that calculate QA metrics and correlations on the subset of the manually labeled Fabbri (2020) data (Tables 2 and 3).

Required data:
- `data/fabbri2020/{summaries,metrics}.jsonl`

Required environments:
- `QAEVAL_ENV`
- `TRANSFORMERS_ENV`
- `MOVERSCORE_ENV`
- `APES_ENV`

To recalculate the numbers, run:
```
sh experiments/question-answering/fabbri2020/run.sh
```

Because the question generation model randomly generates question IDs, rerunning the question generation will result in IDs that do not match the IDs that we used to do the manual annotation.
Therefore, to recalculate the scores reported in the paper, we had to include intermediate outputs of the script, and `run.sh` only finishes the processing from those outputs.
However, it contains the commented out code which we used to run the whole pipeline.

We did the annotation in batches, so you may see batch numbers 1 and 2 in the output directories and code.

Included data:
- `output/{1,2}/expert/mturk-output.csv`: The manually annotated answers to the questions for each batch.
- `output/all/{expert,model}/answers.jsonl`: The post-processed answers to batches 1 and 2 combined and the QAEval answers for the same subset.
  We had to include these because converting from the MTurk output to the `answers.jsonl` requires the questions, and the ID mapping is off.
- `output/all/answer-verification/labeled-answers.csv`: The manual annotations of whether the system/human answers are verified as being correct or incorrect
  
After the `run.sh` script finishes, the metric correlations (Table 3) will be written to the following locations:
- `output/baselines/correlations/rouge-X.json`: The summary-level ROUGE correlations on the labeled subset
- `output/baselines/correlations/MoverScore.json`: The summary-level MoverScore correlations on the labeled subset
- `output/baselines/correlations/APES.json`: The summary-level APES correlations on the labeled subset
- `output/all/model/correlations/f1.json`: The summary-level QAEval correlations with model answers and F1 answer verification
- `output/all/expert/correlations/f1.json`: The summary-level QAEval correlations with human answers and F1 answer verification
- `output/all/answer-verification/model/correlations/human-is-correct.json`: The summary-level QAEval correlations with model answers and human answer verification
- `output/all/answer-verification/expert/correlations/human-is-correct.json`: The summary-level QAEval correlations with human answers and human answer verification

The QA metrics (Table 2) will be written to `output/all/squad-metrics.json` and `output/all/answer-verification/log.txt`.
The first file contains the is-answerable F1 (`is_answerable -> unweighted -> f1`) and the EM/F1 scores on just the subset of the data which is answerable (`is-answerable-only -> squad -> exact-match/f1`).
The second file contains the human labeled answer accuracy given the question is answerable (`Accuracy given ground-truth question is answerable 0.8629737609329446`).