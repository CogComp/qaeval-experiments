This directory contains the code to reproduce the results from the paper in which we mapped from questions to SCUs (Table 1).
Included are:
- `output/output.csv`: The human-written questions for a subset of the TAC'08 data
- `output/question_to_scu_output.csv`: The mapping from the questions to the SCUs
These files have manual annotations which are not produced by the scripts.
However, they are used in the processing.

Required data:
- `data/tac2008/{summaries,pyramids}.jsonl`

Required environments:
- `QAEVAL_ENV`

From the root of the repository, run `sh experiments/answer-selection/run.sh` to run the experiments.
The results will be written to stdout. 