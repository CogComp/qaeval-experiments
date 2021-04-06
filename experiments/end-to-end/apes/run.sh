export EXPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

source ~/miniconda3/etc/profile.d/conda.sh
set -e

conda deactivate
conda activate ${QAEVAL_ENV}

# Score the summaries with APES
for dataset in tac2008 tac2009; do
  sacrerouge apes score \
    --output-jsonl ${EXPT_DIR}/output/${dataset}/scores.jsonl \
    --input-files data/${dataset}/summaries.jsonl \
    --dataset-reader reference-based \
    --environment_name ${APES_ENV} \
    --verbose true

  python -m sacrerouge correlate \
    --metrics-jsonl-files data/${dataset}/metrics.jsonl ${EXPT_DIR}/output/${dataset}/scores.jsonl \
    --metrics overall_responsiveness APES_num_correct \
    --summarizer-type peer \
    --output-file ${EXPT_DIR}/output/${dataset}/correlations.json
done
