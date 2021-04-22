export EXPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

source ~/miniconda3/etc/profile.d/conda.sh

export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export OPENMP_NUM_THREADS=1
export MKL_NUM_THREADS=1

set -e

conda deactivate
conda activate ${QAEVAL_ENV}

python ${EXPT_DIR}/randomly_select_inputs.py \
  data/tac2008/summaries.jsonl \
  ${EXPT_DIR}/output/summaries.jsonl

for method in all-nps top-nps ner; do
  python -m qaeval_expts.generation.generate_candidates \
    ${EXPT_DIR}/output/summaries.jsonl \
    ${EXPT_DIR}/output/candidates-${method}.jsonl \
    --method ${method}

  python -m qaeval_expts.generation.generate_prompts \
    ${EXPT_DIR}/output/candidates-${method}.jsonl \
    ${EXPT_DIR}/output/prompts-${method}.jsonl
done

python ${EXPT_DIR}/dedupe_prompts.py \
  --input-files ${EXPT_DIR}/output/prompts-*.jsonl \
  --output-file ${EXPT_DIR}/output/prompts.jsonl

python ${EXPT_DIR}/preprocess.py \
  ${EXPT_DIR}/output/prompts.jsonl \
  ${EXPT_DIR}/output/input.csv \
  --num-prompts-per-assignment 15

for method in all-nps top-nps ner; do
  python ${EXPT_DIR}/postprocess.py \
    ${EXPT_DIR}/output/candidates-${method}.jsonl \
    ${EXPT_DIR}/output/output.csv \
    ${EXPT_DIR}/output/prompts-${method}.jsonl \
    ${EXPT_DIR}/output/questions-${method}.jsonl
done

python ${EXPT_DIR}/dedupe_questions.py \
  --input-files ${EXPT_DIR}/output/questions-*.jsonl \
  --output-file ${EXPT_DIR}/output/questions.jsonl

python ${EXPT_DIR}/questions_to_csv.py \
  ${EXPT_DIR}/output/questions.jsonl \
  ${EXPT_DIR}/output/prompts.jsonl \
  ${EXPT_DIR}/output/prompts-ner.jsonl \
  ${EXPT_DIR}/output/prompts-top-nps.jsonl \
  ${EXPT_DIR}/output/prompts-all-nps.jsonl \
  ${EXPT_DIR}/output/question_to_scu.csv

python ${EXPT_DIR}/split_annotation_by_strategy.py \
  ${EXPT_DIR}/output/question_to_scu_output.csv \
  ${EXPT_DIR}/output/question_to_scu_output_all_nps.csv \
  ${EXPT_DIR}/output/question_to_scu_output_top_nps.csv \
  ${EXPT_DIR}/output/question_to_scu_output_ner.csv

python ${EXPT_DIR}/compare_questions_scus.py \
  data/tac2008/pyramids.jsonl \
  ${EXPT_DIR}/output/question_to_scu_output_all_nps.csv \
  ${EXPT_DIR}/output/missing-scus-all-nps.tsv \
  ${EXPT_DIR}/output/questions_no_scus-all-nps.tsv

python ${EXPT_DIR}/compare_questions_scus.py \
  data/tac2008/pyramids.jsonl \
  ${EXPT_DIR}/output/question_to_scu_output_top_nps.csv \
  ${EXPT_DIR}/output/missing-scus-top-nps.tsv \
  ${EXPT_DIR}/output/questions_no_scus-top-nps.tsv

python ${EXPT_DIR}/compare_questions_scus.py \
  data/tac2008/pyramids.jsonl \
  ${EXPT_DIR}/output/question_to_scu_output_ner.csv \
  ${EXPT_DIR}/output/missing-scus-ner.tsv \
  ${EXPT_DIR}/output/questions_no_scus-ner.tsv

python ${EXPT_DIR}/compare_questions_scus.py \
  data/tac2008/pyramids.jsonl \
  ${EXPT_DIR}/output/question_to_scu_output.csv \
  ${EXPT_DIR}/output/missing-scus-combined.tsv \
  ${EXPT_DIR}/output/questions_no_scus-combined.tsv