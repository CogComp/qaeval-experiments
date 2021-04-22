export EXPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

source ~/miniconda3/etc/profile.d/conda.sh

export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export OPENMP_NUM_THREADS=1
export MKL_NUM_THREADS=1

set -e

conda deactivate
conda activate ${QAEVAL_ENV}

for dataset in tac2008 tac2009; do
  for metric in "rouge-1" "rouge-2" "rouge-l" "rouge-su4"; do
    sacrerouge correlate \
      --metrics-jsonl-files data/${dataset}/metrics.jsonl \
      --metrics overall_responsiveness ${metric}_recall \
      --summarizer-type peer \
      --output-file ${EXPT_DIR}/output/${dataset}/correlations/${metric}.json
  done
done