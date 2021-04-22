export EXPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

source ~/miniconda3/etc/profile.d/conda.sh

export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export OPENMP_NUM_THREADS=1
export MKL_NUM_THREADS=1

set -e

conda deactivate
conda activate ${QAEVAL_ENV}

python ${EXPT_DIR}/sample.py \
  --summaries-jsonl data/fabbri2020/summaries.jsonl \
  --metrics-jsonl data/fabbri2020/metrics.jsonl \
  --num-summaries 4 \
  --num-instances 10 \
  --output-summaries-jsonl ${EXPT_DIR}/output/all/summaries.jsonl \
  --output-metrics-jsonl ${EXPT_DIR}/output/all/metrics.jsonl \
  --output-summaries-jsonl-1 ${EXPT_DIR}/output/1/summaries.jsonl \
  --output-metrics-jsonl-1 ${EXPT_DIR}/output/1/metrics.jsonl \
  --output-summaries-jsonl-2 ${EXPT_DIR}/output/2/summaries.jsonl \
  --output-metrics-jsonl-2 ${EXPT_DIR}/output/2/metrics.jsonl \
  --random-seed 5

### Run QAEval on the sampled data. This also generates the questions
### which are used in the manual annotation. We are lazy and run it on both buckets as well as the
### combined. We could alternatively concatenate the two buckets
###
### This code will regenerate the questions with different IDs that don't match the answers we
### included, so we leave this commented out for reproducing the results.
##for bucket in all 1 2; do
##  python ${EXPT_DIR}/add_references.py \
##    ${EXPT_DIR}/output/${bucket}/summaries.jsonl \
##    ${EXPT_DIR}/output/${bucket}/qaeval/summaries.jsonl \
##
##  python -m qaeval_expts.generation.generate_candidates \
##    ${EXPT_DIR}/output/${bucket}/qaeval/summaries.jsonl \
##    ${EXPT_DIR}/output/${bucket}/qaeval/candidates.jsonl \
##    --method all-nps
##
##  python -m qaeval_expts.generation.generate_prompts \
##    ${EXPT_DIR}/output/${bucket}/qaeval/candidates.jsonl \
##    ${EXPT_DIR}/output/${bucket}/qaeval/prompts.jsonl
##
##  sh models/generation/predict.sh \
##    ${EXPT_DIR}/output/${bucket}/qaeval/prompts.jsonl \
##    models/generation/model/model.tar.gz \
##    ${EXPT_DIR}/output/${bucket}/qaeval/raw-questions-output.jsonl
##
##  python -m qaeval_expts.generation.model.postprocess \
##    ${EXPT_DIR}/output/${bucket}/qaeval/candidates.jsonl \
##    ${EXPT_DIR}/output/${bucket}/qaeval/raw-questions-output.jsonl \
##    ${EXPT_DIR}/output/${bucket}/qaeval/questions.jsonl
##
##  # Run question-answering
##  conda deactivate
##  conda activate ${TRANSFORMERS_ENV}
##
##  sh models/answering/predict.sh \
##    ${EXPT_DIR}/output/${bucket}/qaeval/questions.jsonl \
##    ${EXPT_DIR}/output/${bucket}/qaeval/raw-answering-output
##
##  conda deactivate
##  conda activate ${QAEVAL_ENV}
##
##  python -m qaeval_expts.answering.postprocess \
##    ${EXPT_DIR}/output/${bucket}/qaeval/questions.jsonl \
##    ${EXPT_DIR}/output/${bucket}/qaeval/raw-answering-output/nbest_predictions_.json \
##    ${EXPT_DIR}/output/${bucket}/qaeval/answers.jsonl
##done
##
### Score the summaries
##sacrerouge score \
##  --config data/metric.jsonnet \
##  --output-jsonl ${EXPT_DIR}/output/all/qaeval/scores.jsonl \
##  --overrides '{"input_files": "'${EXPT_DIR}'/output/all/qaeval/answers.jsonl"}' \
##  --include-packages qaeval_expts
##
### Preprocess the questions for human answering
##python ${EXPT_DIR}/answer_preprocess.py \
##  ${EXPT_DIR}/output/all/qaeval/questions.jsonl \
##  ${EXPT_DIR}/output/all/expert/mturk-input.csv \
##  --num-questions-per-assignment 20
##
##for bucket in 1 2; do
##  python ${EXPT_DIR}/answer_postprocess.py \
##    --questions-jsonl ${EXPT_DIR}/output/${bucket}/qaeval/questions.jsonl \
##    --mturk-csvs ${EXPT_DIR}/output/${bucket}/expert/mturk-output.csv \
##    --output-jsonl ${EXPT_DIR}/output/${bucket}/expert/answers.jsonl
##done
##
##mkdir -p ${EXPT_DIR}/output/all/expert
##cat ${EXPT_DIR}/output/1/expert/answers.jsonl ${EXPT_DIR}/output/2/expert/answers.jsonl > ${EXPT_DIR}/output/all/expert/answers.jsonl
##
##mkdir -p ${EXPT_DIR}/output/all/model
##cp ${EXPT_DIR}/output/all/qaeval/answers.jsonl ${EXPT_DIR}/output/all/model

python ${EXPT_DIR}/squad_evaluate.py \
  ${EXPT_DIR}/output/all/expert/answers.jsonl \
  ${EXPT_DIR}/output/all/model/answers.jsonl \
  ${EXPT_DIR}/output/all/squad-metrics.json \
  --summarizer-type peer

for qa in expert model; do
  sacrerouge score \
    --config data/metric.jsonnet \
    --output-jsonl ${EXPT_DIR}/output/all/${qa}/scores.jsonl \
    --overrides '{"input_files": "'${EXPT_DIR}'/output/all/'${qa}'/answers.jsonl"}' \
    --include-packages qaeval_expts

  for metric in exact-match f1; do
    sacrerouge correlate \
      --metrics-jsonl-files ${EXPT_DIR}/output/all/metrics.jsonl ${EXPT_DIR}/output/all/${qa}/scores.jsonl \
      --metrics expert_relevance qa-eval_${metric} \
      --summarizer-type peer \
      --output-file ${EXPT_DIR}/output/all/${qa}/correlations/${metric}.json \
      --confidence-interval-method none
  done
done

# Prepare for answer verification
python ${EXPT_DIR}/verification_preprocess.py \
  ${EXPT_DIR}/output/all/expert/answers.jsonl \
  ${EXPT_DIR}/output/all/model/answers.jsonl \
  ${EXPT_DIR}/output/all/answer-verification/all-unlabeled-answers.csv \
  ${EXPT_DIR}/output/all/answer-verification/mapping.csv

python ${EXPT_DIR}/verification_postprocess.py \
  ${EXPT_DIR}/output/all/expert/answers.jsonl \
  ${EXPT_DIR}/output/all/model/answers.jsonl \
  ${EXPT_DIR}/output/all/answer-verification/labeled-answers.csv \
  peer \
  ${EXPT_DIR}/output/all/answer-verification/model/right-for-wrong-reasons.csv \
  ${EXPT_DIR}/output/all/answer-verification/expert/human-labeled-answers.jsonl \
  ${EXPT_DIR}/output/all/answer-verification/model/human-labeled-answers.jsonl \
  > ${EXPT_DIR}/output/all/answer-verification/log.txt

# Calculate the correlations with the expert verification
for qa in model expert; do
  sacrerouge score \
    --config data/metric.jsonnet \
    --output-jsonl ${EXPT_DIR}/output/all/answer-verification/${qa}/scores.jsonl \
    --overrides '{"input_files": "'${EXPT_DIR}'/output/all/answer-verification/'${qa}'/human-labeled-answers.jsonl"}' \
    --include-packages qaeval_expts

  for metric in human-is-correct; do
    sacrerouge correlate \
      --metrics-jsonl-files ${EXPT_DIR}/output/all/metrics.jsonl ${EXPT_DIR}/output/all/answer-verification/${qa}/scores.jsonl \
      --metrics expert_relevance qa-eval_${metric} \
      --summarizer-type peer \
      --output-file ${EXPT_DIR}/output/all/answer-verification/${qa}/correlations/${metric}.json \
      --confidence-interval-method none
  done
done

# Run the other metrics on this subset of data
sacrerouge rouge score \
  --output-jsonl ${EXPT_DIR}/output/baselines/rouge.jsonl \
  --input-files ${EXPT_DIR}/output/all/summaries.jsonl \
  --compute_rouge_l true \
  --skip_bigram_gap_length 4 \
  --dataset-reader reference-based

sacrerouge apes score \
  --output-jsonl ${EXPT_DIR}/output/baselines/apes.jsonl \
  --input-files ${EXPT_DIR}/output/all/summaries.jsonl \
  --dataset-reader reference-based \
  --environment_name ${APES_ENV} \
  --verbose true

conda deactivate
conda activate ${MOVERSCORE_ENV}

sacrerouge moverscore score \
  --output-jsonl ${EXPT_DIR}/output/baselines/moverscore.jsonl \
  --input-files ${EXPT_DIR}/output/all/summaries.jsonl \
  --dataset-reader reference-based

conda deactivate
conda activate ${QAEVAL_ENV}

for metric in rouge-1_f1 rouge-2_f1 rouge-l_f1 rouge-su4_f1 MoverScore APES_num_correct; do
  sacrerouge correlate \
    --metrics-jsonl-files ${EXPT_DIR}/output/all/metrics.jsonl ${EXPT_DIR}/output/baselines/rouge.jsonl ${EXPT_DIR}/output/baselines/moverscore.jsonl ${EXPT_DIR}/output/baselines/apes.jsonl \
    --metrics expert_relevance ${metric} \
    --summarizer-type peer \
    --output-file ${EXPT_DIR}/output/baselines/correlations/${metric}.json \
    --confidence-interval-method none \
    &
done
wait