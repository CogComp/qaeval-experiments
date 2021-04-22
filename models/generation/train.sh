DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

rm -r ${DIR}/model

allennlp train \
  --include-package qaeval_expts \
  -s ${DIR}/model \
  ${DIR}/model.jsonnet