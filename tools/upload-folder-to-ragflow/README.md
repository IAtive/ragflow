# Crée un venv

python3.12 -m venv ~/.venvs/ragflow
source ~/.venvs/ragflow/bin/activate

# Installe

pip install ragflow-sdk tqdm

# Cas simple

python upload_to_ragflow.py \
 --folder ~/my_folder \
 --dataset "my_dataset" \
 --api-key ragflow-XXXXXXXXXXXX

# Avec parsing auto et skip des doublons

1.  python upload_to_ragflow.py \
     --folder ~/my_folder \
     --dataset "my_dataset" \
     --api-key ragflow-XXXXXXXXXXXX \
     --base-url http://192.168.1.10:9380 \
     --parse \
     --skip-existing

2.  export RAGFLOW_API_KEY="ragflow-KEY"
    export RAGFLOW_BASE_URL="http://RAGFLOW_BASE_PATH:PORT"
    python upload_to_ragflow.py --folder my_folder --dataset "my_dataset" --parse --skip-existing
