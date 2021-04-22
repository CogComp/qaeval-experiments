DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

input_file=$1
output_dir=$2

python ${DIR}/run_squad.py \
  --model_type electra \
  --model_name_or_path ${DIR}/model \
  --do_predict \
  --predict_file ${input_file} \
  --do_lower_case \
  --max_seq_length 384 \
  --doc_stride 128 \
  --output_dir ${output_dir} \
  --version_2_with_negative