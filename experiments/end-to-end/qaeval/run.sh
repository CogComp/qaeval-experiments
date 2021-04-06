export EXPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

source ~/miniconda3/etc/profile.d/conda.sh

export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export OPENMP_NUM_THREADS=1
export MKL_NUM_THREADS=1

set -e

if [ "$#" -ne 1 ]; then
    echo "Usage: sh path/to/run.sh <dataset>"
    exit
fi

dataset=$1

# Run question-generation
conda deactivate
conda activate ${QAEVAL_ENV}

python -m qaeval_expts.generation.generate_candidates \
  data/${dataset}/summaries.jsonl \
  ${EXPT_DIR}/output/${dataset}/candidates.jsonl \
  --method all-nps

python -m qaeval_expts.generation.generate_prompts \
  ${EXPT_DIR}/output/${dataset}/candidates.jsonl \
  ${EXPT_DIR}/output/${dataset}/prompts.jsonl

sh models/generation/predict.sh \
  ${EXPT_DIR}/output/${dataset}/prompts.jsonl \
  models/generation/model/model.tar.gz \
  ${EXPT_DIR}/output/${dataset}/raw-questions-output.jsonl

python -m qaeval_expts.generation.model.postprocess \
  ${EXPT_DIR}/output/${dataset}/candidates.jsonl \
  ${EXPT_DIR}/output/${dataset}/raw-questions-output.jsonl \
  ${EXPT_DIR}/output/${dataset}/questions.jsonl

# Run question-answering
conda deactivate
conda activate ${TRANSFORMERS_ENV}

sh models/answering/predict.sh \
  ${EXPT_DIR}/output/${dataset}/questions.jsonl \
  ${EXPT_DIR}/output/${dataset}/raw-answering-output

conda deactivate
conda activate ${QAEVAL_ENV}

python -m qaeval_expts.answering.postprocess \
  ${EXPT_DIR}/output/${dataset}/questions.jsonl \
  ${EXPT_DIR}/output/${dataset}/raw-answering-output/nbest_predictions_.json \
  ${EXPT_DIR}/output/${dataset}/answers.jsonl

# Score the summaries
sacrerouge score \
  --config data/metric.jsonnet \
  --output-jsonl ${EXPT_DIR}/output/${dataset}/scores.jsonl \
  --overrides '{"input_files": "'${EXPT_DIR}'/output/'${dataset}'/answers.jsonl"}' \
  --include-packages qaeval_expts

for metric in "exact-match" "f1"; do
  sacrerouge correlate \
    --metrics-jsonl-files data/${dataset}/metrics.jsonl ${EXPT_DIR}/output/${dataset}/scores.jsonl \
    --metrics overall_responsiveness qa-eval_${metric} \
    --summarizer-type peer \
    --output-file ${EXPT_DIR}/output/${dataset}/correlations/${metric}.json
done