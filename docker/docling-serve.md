# Installation docling-serve avec GPU

## 1. Prérequis

```bash
nvidia-smi          # doit afficher ta carte
docker --version
```

## 2. NVIDIA Container Toolkit

```bash
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | \
  sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

## 3. docker-compose.yml

```bash
mkdir -p /opt/docling && cd /opt/docling
```

```yaml
services:
  docling-serve:
    image: quay.io/docling-project/docling-serve-cu130:main
    container_name: docling-serve
    restart: unless-stopped
    ports:
      - "5001:5001"
    environment:
      - DOCLING_SERVE_ENABLE_UI=true
      - DOCLING_DEVICE=cuda
      - NVIDIA_VISIBLE_DEVICES=all
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
```

> Adapte `cu130` → `cu128` si ton driver supporte CUDA 12.8 et pas 13.

## 4. Démarrer

```bash
docker compose up -d
```

Premier pull : ~11 Go (modèles inclus).

## 5. Vérifier

**Que ça tourne :**

```bash
curl http://localhost:5001/health
```

**Que CUDA est activé :**

```bash
docker logs docling-serve 2>&1 | grep -i accelerator
# attendu : Accelerator device: 'cuda:0'
```

**Que le GPU est utilisé pendant une conversion :**

Terminal 1 :

```bash
watch -n 1 nvidia-smi
```

Terminal 2 :

```bash
curl -X POST "http://localhost:5001/v1/convert/source" \
  -H "Content-Type: application/json" \
  -d '{"sources": [{"kind": "http", "url": "https://arxiv.org/pdf/2501.17887"}]}'
```

Tu dois voir dans `nvidia-smi` la mémoire GPU monter (2–5 GB) et le process `python` apparaître.

## 6. Accès

- UI : <http://IP:5001/ui>
- API docs : <http://IP:5001/docs>
