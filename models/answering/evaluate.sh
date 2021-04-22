rm squad_data/cached_dev_*

python run_squad.py \
  --model_type electra \
  --model_name_or_path model \
  --do_eval \
  --do_lower_case \
  --data_dir squad_data \
  --cache_dir cache \
  --per_gpu_train_batch_size 32 \
  --max_seq_length 384 \
  --doc_stride 128 \
  --output_dir ./electra-output \
  --version_2_with_negative