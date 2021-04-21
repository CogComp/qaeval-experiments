# QAEval Experiments
This repository will contain the code to reproduce the experiments from [Towards Question-Answering as an Automatic Metric for Evaluating the Content Quality of a Summary](https://arxiv.org/abs/2010.00490).
If you want to use QAEval, the easiest way is through [its implementation in SacreROUGE](https://github.com/danieldeutsch/sacrerouge/blob/master/doc/metrics/qaeval.md), which is far simpler and easier to use than this repository.

## Environments
The experiments run several different evaluation metrics and deep learning libraries.
Each requires a specific set of dependencies, so we have a conda environment for each one.
The `envs` directory contains the output from `conda env export <environment-name>` for the environments we used in our experiments.
*Before running each of the scripts, you need to set environment variables in `setup-env.sh` that name each of the environments.*
Edit that file to point to your environment names, then run `source setup-env.sh` before running the experiment scripts.

Here is a description of each one:
- `envs/qaeval-environment.yml`: The environment for interactions with sacrerouge, question generation, and MoverScore.
It corresponds to `QAEVAL_ENV` and `MOVERSCORE_ENV` in `setup-env.sh`
- `envs/transformers-environment.yml`: The environment for the QA model of QAEval.
It corresponds to `TRANSFORMERS_ENV` in `setup-env.sh`
- `envs/apes-environment`: The environment to run APES.
It corresponds to `APES_ENV` in `setup-env.sh`
- `envs/pyreval-environment`: The environment to run PyrEval.
It corresponds to `PYREVAL_ENV` in `setup-env.sh`

Each of the environments should be able to be recreated with `conda create -f <filename>`.
Further, several of them require installing Spacy model files with pip commands, as follows:
- `envs/qaeval-environment.yml`: `pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-2.2.5/en_core_web_sm-2.2.5.tar.gz`
- `envs/transformers-environment.yml`: `pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-2.3.1/en_core_web_sm-2.3.1.tar.gz`
- `envs/apes-environment.yml`: `pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-2.3.1/en_core_web_sm-2.3.1.tar.gz`
As far as we know, these can't be included in the environment files, so it needs to be done manually after creating the environments.

Further, each of the scripts must initialize conda before they run using `source ~/miniconda3/etc/profile.d/conda.sh`.
If that is not the location of your conda setup script, you will need to replace it in all of the scripts you want to run.

The `QAEVAL_ENV` must have ROUGE and PyrEval setup:
```
sacrerouge setup-metric rouge
sacrerouge setup-metric pyreval
```

The `MOVERSCORE_ENV` must have MoverScore setup:
```
sacrerouge setup-metric moverscore
```

The `APES_ENV` must have APES setup:
```
sacrerouge setup-metric apes
```

## Data Dependencies
Some of the experiments require access to the TAC 2008 and 2009 datasets, which we cannot provide due to license restrictions.
If you have access to them, first set them up using SacreROUGE (see [here](https://github.com/danieldeutsch/sacrerouge/blob/master/doc/datasets/duc-tac/tac2008.md) and [here](https://github.com/danieldeutsch/sacrerouge/blob/master/doc/datasets/duc-tac/tac2009.md)).
Then copy the following files over to the `data` directory of this repo:
- `{tac2008,tac2009}/task1.A.summaries.jsonl -> data/{tac2008,tac2009}/summaries.jsonl`
- `{tac2008,tac2009}/task1.A.metrics.jsonl -> data/{tac2008,tac2009}/metrics.jsonl`
- `{tac2008,tac2009}/task1.A.pyramids.jsonl -> data/{tac2008,tac2009}/pyramids.jsonl`
- `{tac2008,tac2009}/task1.A.pyramid-annotations.jsonl -> data/{tac2008,tac2009}/pyramid-annotations.jsonl`

The Fabbri (2020) data dependencies can be setup using SacreROUGE.
See [here](https://github.com/danieldeutsch/sacrerouge/blob/master/doc/datasets/fabbri2020.md).
We have also included the data in this repo since it is publicly available (`data/fabbri2020`).

## Model Dependencies
Running QAEval requires a pre-trained question generation and question answering models.
The code to retrain each of those models can be found [here](models/generation/Readme.md) and [here](models/answering/Readme.md).

The models are available for download here:
- [Question generation](http://cogcomp.org/models/qaeval-experiments/model.tar.gz)
- [Question answering](http://cogcomp.org/models/qaeval-experiments/qa-model.zip)

The generation model should be downloaded to `models/generation/model/model.tar.gz`.
The answering model should be downloaded and unzipped in the `models/answering/model/` directory.
The files in that directory should look like:
```bash
ls -l models/answering/model
> config.json
> pytorch_model.bin
> special_tokens_map.json
> tokenizer_config.json
> training_args.bin
> vocab.txt
```

## TAC 2008 & 2009 Correlations
To calculate the correlations of the metrics to human judgments on the TAC 2008 and 2009 datasets (Table 4), see `experiments/end-to-end`.
There is a subdirectory for each metric with a script that will score summaries and calculate the correlation to the ground-truth judgments.

The required input files to run the scripts are:
- `data/{tac2008,tac2009}/summaries.jsonl`
- `data/{tac2008,tac2009}/metrics.jsonl`

## Fabbri (2020) Correlations
We used the implementations of the metrics in SacreROUGE to calculate the Fabbri (2020) correlations (Table 5).
For sample, see [here](https://github.com/danieldeutsch/sacrerouge/blob/master/experiments/qaeval/run-fabbri2020.sh) for calculating QAEval's correlations on Fabbri (2020).

## Answer Selection Results
See [here](experiments/answer-selection/Readme.md) to reproduce the results about mapping questions to SCUs (Table 1).

## Question Generation Results
See [here](experiments/question-generation/Readme.md) to reproduce the results about human vs system-generated questions (Figure 3).

## Question Answering Results
See [here](experiments/question-answering/tac2008/Readme.md) to reproduce the results about the QA performance/metric correlations on the labeled TAC 2008 data (Tables 2 and 3).
See [here](experiments/question-answering/fabbri2020/Readme.md) to reproduce the results about the QA performance/metric correlations on the labeled Fabbri (2020) data (Tables 2 and 3).

## Number of References Learning Curve Results
See [here](experiments/num-references/Readme.md) to reproduce the learning curve in the appendix that measures the impact of additional reference summaries (Figure 6).
