DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

mkdir -p ${DIR}/squad_data
wget https://rajpurkar.github.io/SQuAD-explorer/dataset/train-v2.0.json -O ${DIR}/squad_data/train-v2.0.json
wget https://rajpurkar.github.io/SQuAD-explorer/dataset/dev-v2.0.json -O ${DIR}/squad_data/dev-v2.0.json
