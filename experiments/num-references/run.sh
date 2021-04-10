export EXPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

source ~/miniconda3/etc/profile.d/conda.sh
set -e

for dataset in tac2008; do
  conda deactivate
  conda activate ${QAEVAL_ENV}

  # ROUGE, QAEval, APES, and MoverScore scores can be decomposed across references: their scores will be averaged
  # across references, so it is enough for us to score each instance against each reference individually. Then
  # we can simulate having a different number of references by averaging the unrolled instances. This is not
  # true for the Pyramid Method or Pyreval. Those are handled separately
  python ${EXPT_DIR}/unroll_instances.py \
    experiments/end-to-end/qaeval/output/${dataset}/answers.jsonl \
    ${EXPT_DIR}/output/${dataset}/unrolled-instances.jsonl \
    --remove-references

  # Score with QAEval
  sacrerouge score \
    --config data/metric.jsonnet \
    --output-jsonl ${EXPT_DIR}/output/${dataset}/qaeval.jsonl \
    --overrides '{"input_files": "'${EXPT_DIR}'/output/'${dataset}'/unrolled-instances.jsonl"}' \
    --include-packages qaeval_expts

  # Score with ROUGE
  sacrerouge rouge score \
    --output-jsonl ${EXPT_DIR}/output/${dataset}/rouge.jsonl \
    --dataset-reader reference-based \
    --max_ngram 2 \
    --remove_stopwords false \
    --use_porter_stemmer true \
    --input-files ${EXPT_DIR}/output/${dataset}/unrolled-instances.jsonl

  # Score with MoverScore
  conda deactivate
  conda activate ${MOVERSCORE_ENV}
  sacrerouge moverscore score \
    --input-files ${EXPT_DIR}/output/${dataset}/unrolled-instances.jsonl \
    --dataset-reader reference-based \
    --output-jsonl ${EXPT_DIR}/output/${dataset}/moverscore.jsonl

  # Score with APES
  conda deactivate
  conda activate ${QAEVAL_ENV}
  sacrerouge apes score \
    --output-jsonl ${EXPT_DIR}/output/${dataset}/apes.jsonl \
    --input-files ${EXPT_DIR}/output/${dataset}/unrolled-instances.jsonl \
    --dataset-reader reference-based \
    --environment_name ${APES_ENV}

  # Combine all of the scores into one file for easier processing
  python ${EXPT_DIR}/merge_metrics.py \
    ${EXPT_DIR}/output/${dataset}/scores.jsonl \
    ${EXPT_DIR}/output/${dataset}/qaeval.jsonl \
    ${EXPT_DIR}/output/${dataset}/rouge.jsonl \
    ${EXPT_DIR}/output/${dataset}/moverscore.jsonl \
    ${EXPT_DIR}/output/${dataset}/apes.jsonl

  for num_references in 1 2 3 4; do
    for sample in $(seq 1 30); do
      # Calculate the scores for this sample for the above metrics
      python ${EXPT_DIR}/sample_metrics.py \
        ${EXPT_DIR}/output/${dataset}/scores.jsonl \
        ${num_references} \
        ${sample} \
        ${EXPT_DIR}/output/${dataset}/samples/${num_references}/${sample}.jsonl

      # For Pyramid Score: sample Pyramids, then calculate the pyramid score
      python ${EXPT_DIR}/sample_pyramids.py \
        data/${dataset}/pyramids.jsonl \
        ${num_references} \
        ${sample} \
        ${EXPT_DIR}/output/${dataset}/pyramid-samples/${num_references}/${sample}.jsonl

      sacrerouge pyramid-score score \
        --output-jsonl ${EXPT_DIR}/output/${dataset}/pyramid-scores/${num_references}/${sample}.jsonl \
        --input-files ${EXPT_DIR}/output/${dataset}/pyramid-samples/${num_references}/${sample}.jsonl data/${dataset}/pyramid-annotations.jsonl \
        --dataset-reader '{"type": "pyramid-based", "include_reference_annotations": false}'
    done
  done

  # For PyrEval, it's best to sample different numbers of references and combine them into a single file
  # so that repeated (summary, reference) pairs can have work reused. The computation is much faster this way
  python ${EXPT_DIR}/sample_references.py \
    data/${dataset}/summaries.jsonl \
    30 \
    ${EXPT_DIR}/output/${dataset}/reference-samples.jsonl

  sacrerouge pyreval score \
    --output-jsonl ${EXPT_DIR}/output/${dataset}/pyreval-scores.jsonl \
    --input-files ${EXPT_DIR}/output/${dataset}/reference-samples.jsonl \
    --dataset-reader reference-based \
    --environment_name ${PYREVAL_ENV} \
    --verbose true

  # Now split the samples into individual files
  python ${EXPT_DIR}/divide_pyreval_samples.py \
    ${EXPT_DIR}/output/${dataset}/pyreval-scores.jsonl \
    ${EXPT_DIR}/output/${dataset}/pyreval-samples

  # Remove the Pyramid Score from the ground-truth since we recalculated it
  python ${EXPT_DIR}/remove_metrics.py \
    data/${dataset}/metrics.jsonl \
    ${EXPT_DIR}/output/${dataset}/responsiveness.jsonl \
    --remove-pyramid

  # Calculate the correlations
  for num_references in 1 2 3 4; do
    for sample in $(seq 1 30); do
        for metric in qa-eval_exact-match qa-eval_f1 rouge-1_recall MoverScore APES_num_correct modified_pyramid_score; do
          sacrerouge correlate \
            --metrics-jsonl-files \
                ${EXPT_DIR}/output/${dataset}/responsiveness.jsonl \
                ${EXPT_DIR}/output/${dataset}/samples/${num_references}/${sample}.jsonl \
                ${EXPT_DIR}/output/${dataset}/pyramid-scores/${num_references}/${sample}.jsonl \
            --metrics overall_responsiveness ${metric} \
            --summarizer-type peer \
            --output-file ${EXPT_DIR}/output/${dataset}/correlations/${metric}/${num_references}/${sample}.json \
            --confidence-interval-method none \
          &
        done
        wait
    done
  done

  # Handle PyrEval separately because it fails with 1 reference, so we skip that
  for num_references in 2 3 4; do
    for sample in $(seq 0 29); do
        sacrerouge correlate \
          --metrics-jsonl-files ${EXPT_DIR}/output/${dataset}/responsiveness.jsonl ${EXPT_DIR}/output/${dataset}/pyreval-samples/${num_references}/${sample}.jsonl \
          --metrics overall_responsiveness pyreval_quality \
          --summarizer-type peer \
          --output-file ${EXPT_DIR}/output/${dataset}/correlations/pyreval/${num_references}/${sample}.json \
          --confidence-interval-method none
    done
  done

  # Plot the results
  for metric in qa-eval_f1; do
    python ${EXPT_DIR}/plot_curve.py \
      peer \
      ${metric} \
      rouge-1-recall \
      pyramid-score \
      pyreval \
      moverscore \
      apes \
      ${EXPT_DIR}/output/${dataset}/correlations/${metric} \
      ${EXPT_DIR}/output/${dataset}/correlations/rouge-1_recall \
      ${EXPT_DIR}/output/${dataset}/correlations/modified_pyramid_score \
      ${EXPT_DIR}/output/${dataset}/correlations/pyreval \
      ${EXPT_DIR}/output/${dataset}/correlations/MoverScore \
      ${EXPT_DIR}/output/${dataset}/correlations/APES_num_correct \
      ${EXPT_DIR}/output/${dataset}/plots/${metric}
  done
done