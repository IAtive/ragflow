1.  /etc/hosts (macOS, une seule fois) :

sudo sh -c 'echo "127.0.0.1 es01 infinity mysql minio redis" >> /etc/hosts'

2. Dépendances Python (une seule fois) :

cd /Users/hakimkramdi/Documents/IATIVE/Workspace/ragflow
uv sync --python 3.12 --all-extras

3. Démarrer les services de base avec Infinity :

cd docker
DOC_ENGINE=infinity docker compose -f docker-compose-base.yml --profile infinity up -d

4. Démarrer le backend en mode debug (terminal 1) :

cd /Users/hakimkramdi/Documents/IATIVE/Workspace/ragflow
source .venv/bin/activate

export PYTHONPATH=$(pwd) \
export DOC_ENGINE=infinity \
export DOCLING_OCR_ENGINE=rapidocr \
export DOCLING_OCR_LANG=fr,en \
export DOCLING_TABLE_MODE=accurate \
export DOCLING_SERVER_URL=http://localhost:5001

# Lancer directement (hot-reload possible, logs lisibles)

python api/ragflow_server.py

5. Démarrer le task executor (terminal 2) :

source .venv/bin/activate

export PYTHONPATH=$(pwd) \
export DOC_ENGINE=infinity \
export DOCLING_OCR_ENGINE=rapidocr \
export DOCLING_OCR_LANG=fr,en \
export DOCLING_TABLE_MODE=accurate \
export DOCLING_SERVER_URL=http://localhost:5001

python rag/svr/task_executor.py 0

6. Démarrer le frontend (terminal 3) :

cd web
npm install
npm run dev

# → http://localhost:9222

# Si y a des erreurs pour cv2

La correction :

## Désinstaller les deux

uv pip uninstall opencv-python opencv-python-headless

## Réinstaller uniquement la version headless

uv pip install opencv-python-headless

## Docker build and push

Build the image

docker build \  
 --platform linux/amd64 \
 -f Dockerfile \
 -t infiniflow/ragflow:latest \

1. Re-tagger l'image

docker tag infiniflow/ragflow:latest ghcr.io/iative/ragflow:latest

2. Login et Push

gh auth login --scopes "write:packages,read:packages"

gh auth token | docker login ghcr.io -u IAtive --password-stdin

docker push ghcr.io/iative/ragflow:latest

3. Mettre à jour docker/.env

RAGFLOW_IMAGE=ghcr.io/iative/ragflow:latest
