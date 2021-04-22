This directory contains the code to reproduce the number of references learning curve (Figure 6).

First, you must run QAEval end-to-end:
```
sh experiments/end-to-end/qaeval/run.sh
```

Required data:
- `data/tac2008/{summaries,metrics,pyramids,pyramid-annotations}.jsonl`

Required environments:
- `QAEVAL_ENV`
- `PYREVAL_ENV`
- `MOVERSCORE_ENV`
- `APES_ENV`

Then run the script:
```
sh experiments/num-references/run.sh
```
It is a very long script to run.

After it is done, the plots will be saved to `experiments/num-references/output/tac2008/plots`.