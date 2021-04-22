export EXPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

source ~/miniconda3/etc/profile.d/conda.sh

export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export OPENMP_NUM_THREADS=1
export MKL_NUM_THREADS=1

set -e

conda deactivate
conda activate ${QAEVAL_ENV}

python ${EXPT_DIR}/sample_peers.py \
  ${EXPT_DIR}/input/questions.jsonl \
  data/tac2008/summaries.jsonl \
  ${EXPT_DIR}/output/questions-peers.jsonl \
  --num-peers 5

python ${EXPT_DIR}/answer_preprocess.py \
  ${EXPT_DIR}/output/questions-peers.jsonl \
  ${EXPT_DIR}/output/expert/mturk-input.csv \
  --num-questions-per-assignment 20

python ${EXPT_DIR}/answer_postprocess.py \
  --questions-jsonl ${EXPT_DIR}/output/questions-peers.jsonl \
  --mturk-csvs ${EXPT_DIR}/output/expert/mturk-output.csv ${EXPT_DIR}/output/expert/holes-output.csv \
  --output-jsonl ${EXPT_DIR}/output/expert/answers.jsonl

python ${EXPT_DIR}/reduce_to_answered_questions.py \
  ${EXPT_DIR}/output/expert/answers.jsonl \
  ${EXPT_DIR}/output/questions-peers.jsonl \
  ${EXPT_DIR}/output/model/questions.jsonl

conda deactivate
conda activate ${TRANSFORMERS_ENV}

mkdir -p ${EXPT_DIR}/output/model
sh models/answering/predict.sh \
  ${EXPT_DIR}/output/model/questions.jsonl \
  ${EXPT_DIR}/output/model/answering-raw-output

conda deactivate
conda activate ${QAEVAL_ENV}

python -m qaeval_expts.answering.postprocess \
  ${EXPT_DIR}/output/model/questions.jsonl \
  ${EXPT_DIR}/output/model/answering-raw-output/nbest_predictions_.json \
  ${EXPT_DIR}/output/model/answers.jsonl

python ${EXPT_DIR}/remove_metrics.py \
  data/tac2008/metrics.jsonl \
  ${EXPT_DIR}/output/responsiveness.jsonl \
  --remove-pyramid

for qa in expert model; do
  sacrerouge score \
    --config data/metric.jsonnet \
    --output-jsonl ${EXPT_DIR}/output/${qa}/scores.jsonl \
    --overrides '{"input_files": "'${EXPT_DIR}'/output/'${qa}'/answers.jsonl"}' \
    --include-packages qaeval_expts

  for metric in exact-match f1; do
    sacrerouge correlate \
      --metrics-jsonl-files ${EXPT_DIR}/output/responsiveness.jsonl ${EXPT_DIR}/output/${qa}/scores.jsonl \
      --metrics overall_responsiveness qa-eval_${metric} \
      --summarizer-type peer \
      --output-file ${EXPT_DIR}/output/${qa}/correlations/${metric}.json \
      --confidence-interval-method none
  done
done

python ${EXPT_DIR}/squad_evaluate.py \
  ${EXPT_DIR}/output/expert/answers.jsonl \
  ${EXPT_DIR}/output/model/answers.jsonl \
  ${EXPT_DIR}/output/squad-metrics.json \
  --summarizer-type peer

# Prepare answer verification
python ${EXPT_DIR}/verification_preprocess.py \
  ${EXPT_DIR}/output/expert/answers.jsonl \
  ${EXPT_DIR}/output/model/answers.jsonl \
  ${EXPT_DIR}/output/answer-verification/all-unlabeled-answers.csv

python ${EXPT_DIR}/verification_postprocess.py \
  ${EXPT_DIR}/output/expert/answers.jsonl \
  ${EXPT_DIR}/output/model/answers.jsonl \
  ${EXPT_DIR}/output/answer-verification/labeled-answers.csv \
  peer \
  ${EXPT_DIR}/output/answer-verification/model/right-for-wrong-reasons.csv \
  ${EXPT_DIR}/output/answer-verification/expert/human-labeled-answers.jsonl \
  ${EXPT_DIR}/output/answer-verification/model/human-labeled-answers.jsonl \
  > ${EXPT_DIR}/output/answer-verification/log.txt

for qa in model expert; do
  sacrerouge score \
    --config data/metric.jsonnet \
    --output-jsonl ${EXPT_DIR}/output/answer-verification/${qa}/scores.jsonl \
    --overrides '{"input_files": "'${EXPT_DIR}'/output/answer-verification/'${qa}'/human-labeled-answers.jsonl"}' \
    --include-packages qaeval_expts

  for metric in human-is-correct; do
    sacrerouge correlate \
      --metrics-jsonl-files ${EXPT_DIR}/output/responsiveness.jsonl ${EXPT_DIR}/output/answer-verification/${qa}/scores.jsonl \
      --metrics overall_responsiveness qa-eval_${metric} \
      --summarizer-type peer \
      --output-file ${EXPT_DIR}/output/answer-verification/${qa}/correlations/${metric}.json \
      --confidence-interval-method none
  done
done

# Run the baselines on this subset of the data
python ${EXPT_DIR}/select_summaries.py \
  ${EXPT_DIR}/output/expert/answers.jsonl \
  data/tac2008/summaries.jsonl \
  ${EXPT_DIR}/output/baselines/summaries.jsonl

sacrerouge rouge score \
  --output-jsonl ${EXPT_DIR}/output/baselines/rouge.jsonl \
  --dataset-reader reference-based \
  --max_ngram 2 \
  --remove_stopwords false \
  --use_porter_stemmer true \
  --compute_rouge_l true \
  --skip_bigram_gap_length 4 \
  --input-files ${EXPT_DIR}/output/baselines/summaries.jsonl

sacrerouge apes score \
  --output-jsonl ${EXPT_DIR}/output/baselines/apes.jsonl \
  --input-files ${EXPT_DIR}/output/baselines/summaries.jsonl \
  --dataset-reader reference-based \
  --environment_name ${APES_ENV} \
  --verbose true

conda deactivate
conda activate ${MOVERSCORE_ENV}

sacrerouge moverscore score \
  --output-jsonl ${EXPT_DIR}/output/baselines/moverscore.jsonl \
  --input-files ${EXPT_DIR}/output/baselines/summaries.jsonl \
  --dataset-reader reference-based

conda deactivate
conda activate ${QAEVAL_ENV}

for metric in rouge-1_recall rouge-2_recall rouge-l_recall rouge-su4_recall APES_num_correct MoverScore; do
  sacrerouge correlate \
    --metrics-jsonl-files ${EXPT_DIR}/output/responsiveness.jsonl ${EXPT_DIR}/output/baselines/rouge.jsonl ${EXPT_DIR}/output/baselines/apes.jsonl ${EXPT_DIR}/output/baselines/moverscore.jsonl \
    --metrics overall_responsiveness ${metric} \
    --summarizer-type peer \
    --output-file ${EXPT_DIR}/output/baselines/correlations/${metric}.json \
    --confidence-interval-method none \
  &
done
wait

# Pyramid Score
python ${EXPT_DIR}/select_pyramids.py \
  ${EXPT_DIR}/output/expert/answers.jsonl \
  data/tac2008/pyramids.jsonl \
  data/tac2008/pyramid-annotations.jsonl \
  ${EXPT_DIR}/output/pyramid-score/pyramids.jsonl \
  ${EXPT_DIR}/output/pyramid-score/pyramid-annotations.jsonl

sacrerouge pyramid-score score \
  --output-jsonl ${EXPT_DIR}/output/pyramid-score/scores.jsonl \
  --input-files ${EXPT_DIR}/output/pyramid-score/pyramids.jsonl ${EXPT_DIR}/output/pyramid-score/pyramid-annotations.jsonl \
  --dataset-reader '{"type": "pyramid-based", "include_reference_annotations": false}'

sacrerouge correlate \
  --metrics-jsonl-files ${EXPT_DIR}/output/responsiveness.jsonl ${EXPT_DIR}/output/pyramid-score/scores.jsonl \
  --metrics overall_responsiveness modified_pyramid_score \
  --summarizer-type peer \
  --output-file ${EXPT_DIR}/output/pyramid-score/correlation.json \
  --confidence-interval-method none
