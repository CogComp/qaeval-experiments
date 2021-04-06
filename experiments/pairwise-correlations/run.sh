export EXPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

source ~/miniconda3/etc/profile.d/conda.sh

export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export OPENMP_NUM_THREADS=1
export MKL_NUM_THREADS=1

set -e

metrics=("rouge-1_recall" "rouge-2_recall" "rouge-l_recall" "rouge-su4_recall" "qa-eval_exact-match" "qa-eval_f1" "APES_num_correct")
for metric1 in "${metrics[@]}"; do
  for metric2 in "${metrics[@]}"; do
    sacrerouge correlate \
      --metrics-jsonl-files data/tac2008/metrics.jsonl experiments/end-to-end/apes/output/tac2008/scores.jsonl experiments/end-to-end/qaeval/output/tac2008/scores.jsonl \
      --metrics ${metric1} ${metric2} \
      --summarizer-type peer \
      --output-file ${EXPT_DIR}/output/correlations/${metric1}/${metric2}.json \
      --confidence-interval-method 'none' \
    &
  done
  wait
done

python ${EXPT_DIR}/plot_pairwise_correlations.py \
  ${EXPT_DIR}/output/correlations \
  ${EXPT_DIR}/output/plots \
  --metrics "rouge-1_recall" "rouge-2_recall" "rouge-l_recall" "rouge-su4_recall" "APES_num_correct" "qa-eval_exact-match" "qa-eval_f1" \
  --names R1 R2 RL RSU4 APES QA-EM QA-F1