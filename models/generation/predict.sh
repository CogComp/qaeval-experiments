input_file=$1
model_file=$2
output_file=$3

mkdir -p $(dirname ${output_file})

allennlp predict \
  --include-package qaeval_expts \
  --output-file ${output_file} \
  --cuda-device 0 \
  --predictor question_generation \
  --silent \
  --batch-size 16 \
  ${model_file} \
  ${input_file}