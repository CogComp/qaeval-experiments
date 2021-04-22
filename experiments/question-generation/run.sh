export EXPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

source ~/miniconda3/etc/profile.d/conda.sh

export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export OPENMP_NUM_THREADS=1
export MKL_NUM_THREADS=1

set -e

conda deactivate
conda activate ${QAEVAL_ENV}

python ${EXPT_DIR}/remove_errors.py \
  ${EXPT_DIR}/input/questions.jsonl \
  ${EXPT_DIR}/input/prompts.jsonl \
  ${EXPT_DIR}/output/questions-no-errors.jsonl \
  ${EXPT_DIR}/output/prompts-no-errors.jsonl

python ${EXPT_DIR}/add_summaries.py \
  data/tac2008/summaries.jsonl \
  ${EXPT_DIR}/output/questions-no-errors.jsonl \
  ${EXPT_DIR}/output/expert/questions.jsonl

sh models/generation/predict.sh \
  ${EXPT_DIR}/output/prompts-no-errors.jsonl \
  models/generation/model/model.tar.gz \
  ${EXPT_DIR}/output/model/raw-question-output.jsonl

python -m qaeval_expts.generation.model.postprocess \
  ${EXPT_DIR}/input/candidates.jsonl \
  ${EXPT_DIR}/output/model/raw-question-output.jsonl \
  ${EXPT_DIR}/output/model/questions.jsonl

python ${EXPT_DIR}/add_summaries.py \
  data/tac2008/summaries.jsonl \
  ${EXPT_DIR}/output/model/questions.jsonl \
  ${EXPT_DIR}/output/model/questions-peers.jsonl

conda deactivate
conda activate ${TRANSFORMERS_ENV}

sh models/answering/predict.sh \
  ${EXPT_DIR}/output/expert/questions.jsonl \
  ${EXPT_DIR}/output/expert/answering-raw-output

sh models/answering/predict.sh \
  ${EXPT_DIR}/output/model/questions-peers.jsonl \
  ${EXPT_DIR}/output/model/answering-raw-output

conda deactivate
conda activate ${QAEVAL_ENV}

python -m qaeval_expts.answering.postprocess \
  ${EXPT_DIR}/output/expert/questions.jsonl \
  ${EXPT_DIR}/output/expert/answering-raw-output/nbest_predictions_.json \
  ${EXPT_DIR}/output/expert/answers.jsonl

python -m qaeval_expts.answering.postprocess \
  ${EXPT_DIR}/output/model/questions-peers.jsonl \
  ${EXPT_DIR}/output/model/answering-raw-output/nbest_predictions_.json \
  ${EXPT_DIR}/output/model/answers.jsonl

sacrerouge score \
  --config data/metric.jsonnet \
  --output-jsonl ${EXPT_DIR}/output/expert/scores.jsonl \
  --overrides '{"input_files": "'${EXPT_DIR}'/output/expert/answers.jsonl"}' \
  --include-packages qaeval_expts

sacrerouge score \
  --config data/metric.jsonnet \
  --output-jsonl ${EXPT_DIR}/output/model/scores.jsonl \
  --overrides '{"input_files": "'${EXPT_DIR}'/output/model/answers.jsonl"}' \
  --include-packages qaeval_expts

python ${EXPT_DIR}/sample_instances.py \
  ${EXPT_DIR}/output/expert/scores.jsonl \
  30 \
  ${EXPT_DIR}/output/expert/samples \
  --num-inputs 2 4 6 8 10

python ${EXPT_DIR}/sample_instances.py \
  ${EXPT_DIR}/output/model/scores.jsonl \
  30 \
  ${EXPT_DIR}/output/model/samples \
  --num-inputs 2 4 6 8 10

python ${EXPT_DIR}/remove_unnecessary_metrics.py \
  data/tac2008/metrics.jsonl \
  ${EXPT_DIR}/output/responsiveness.jsonl \
  --remove-pyramid

python ${EXPT_DIR}/replace_responsiveness_with_average.py \
  ${EXPT_DIR}/output/responsiveness.jsonl \
  ${EXPT_DIR}/output/responsiveness-average.jsonl

for metric in "exact-match" "f1"; do
  for type in "model" "expert"; do
    for num_inputs in 2 4 6 8 10; do
      for sample in $(seq 0 29); do
        sacrerouge correlate \
          --metrics-jsonl-files ${EXPT_DIR}/output/responsiveness-average.jsonl ${EXPT_DIR}/output/${type}/samples/${num_inputs}/${sample}.jsonl \
          --metrics overall_responsiveness qa-eval_${metric} \
          --summarizer-type peer \
          --output-file ${EXPT_DIR}/output/${type}/correlations/${metric}/${num_inputs}/${sample}.json
      done
    done
  done
done

for metric in "exact-match" "f1"; do
  python ${EXPT_DIR}/plot_curve.py \
    ${EXPT_DIR}/output/expert/correlations/${metric} \
    ${EXPT_DIR}/output/model/correlations/${metric} \
    ${EXPT_DIR}/output/plots/${metric}
done