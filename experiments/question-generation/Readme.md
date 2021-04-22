This directory contains the code to reproduce the human vs system-generated questions experiment (Figure 3).
Included are:
- `input/{candidates,prompts,questions}.jsonl`: The manually written questions collected as part of the `experiments/answer-selection` experiment, copied here for easier access. 

Required data:
- `data/tac2008/{summaries,metrics}.jsonl`

Required environments:
- `QAEVAL_ENV`
- `TRANSFORMERS_ENV`

To reproduce the results, run
```
sh experiments/question-generation/run.sh
```
from the root of the repository.

The plots for QAEval-EM and QAEval-F1 and the different correlation coefficients will be written to the `output/plots/`.
Our paper used the F1/Spearman plot.