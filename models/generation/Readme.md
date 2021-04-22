This directory contains the code to train the question generation model.
The training data comes from the CodaLab link: https://worksheets.codalab.org/worksheets/0xd4ebc52cebb84130a07cbfe81597aaf0/.
The source code comes from https://github.com/kelvinguu/qanli.

The commands to retrain the model should be run from the root of the repo:
```
# Download and reformat the training data
sh models/generation/setup.sh

# Train the model
sh models/generation/train.sh
```

The QAEval code will then use the `predict.sh` script to generate questions for the summarization data.