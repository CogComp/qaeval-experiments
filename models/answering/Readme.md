This directory contains the code to train the question answering model.
The scripts should be run from this directory:

```
# Download the training data
sh setup.sh

# Train the model
sh train.sh
```

The QAEval code will use the `predict.sh` script to answer the questions.

Here are the results of the trained model with google/electra-large-discriminator:
```json
{
    "exact": 43.44310620736124,
    "f1": 46.7579012131542,
    "total": 11873,
    "HasAns_exact": 87.01079622132254,
    "HasAns_f1": 93.64989222398445,
    "HasAns_total": 5928,
    "NoAns_exact": 0.0,
    "NoAns_f1": 0.0,
    "NoAns_total": 5945,
    "best_exact": 86.86936747241641,
    "best_exact_thresh": 0.0033068576883730607,
    "best_f1": 89.78113205776883,
    "best_f1_thresh": 0.0033068576883730607,
    "best_exact_is_answerable": {
        "precision": 0.9262617621899059,
        "recall": 0.9132928475033738,
        "f1": 0.9197315892295932
    },
    "best_f1_is_answerable": {
        "precision": 0.9262617621899059,
        "recall": 0.9132928475033738,
        "f1": 0.9197315892295932
    }
}
```
These are very close to those reported in the original Electra paper.

The `run_squad_trainer.py` is taken from the transformers library:
https://github.com/huggingface/transformers/blob/master/examples/question-answering/run_squad_trainer.py

The `run_squad.py` file is edited from the transformers library:
https://github.com/huggingface/transformers/blob/master/examples/question-answering/run_squad.py