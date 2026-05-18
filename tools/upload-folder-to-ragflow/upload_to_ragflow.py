#!/usr/bin/env python3
"""
Upload récursivement un dossier local vers un dataset RAGFlow.

Usage:
    python upload_to_ragflow.py \
        --folder /chemin/vers/dossier \
        --dataset "Mon Dataset" \
        --api-key ragflow-XXXX \
        --base-url http://localhost:9380 \
        --parse
"""
import argparse
import os
import sys
from pathlib import Path
from typing import Iterable

from ragflow_sdk import RAGFlow
from tqdm import tqdm

# Formats supportés par RAGFlow
SUPPORTED_EXTENSIONS = {
    ".pdf", ".doc", ".docx", ".txt", ".md", ".mdx",
    ".csv", ".xlsx", ".xls",
    ".jpeg", ".jpg", ".png", ".tif", ".tiff", ".gif",
    ".ppt", ".pptx",
    ".html", ".htm",
    ".eml", ".json",
}

# Taille max d'un batch d'upload (en nombre de fichiers)
BATCH_SIZE = 32


def iter_files(folder: Path, recursive: bool = True) -> Iterable[Path]:
    """Itère sur les fichiers supportés du dossier."""
    pattern = "**/*" if recursive else "*"
    for path in folder.glob(pattern):
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            yield path


def chunked(iterable, size):
    """Découpe un itérable en batches."""
    batch = []
    for item in iterable:
        batch.append(item)
        if len(batch) == size:
            yield batch
            batch = []
    if batch:
        yield batch


def get_existing_filenames(dataset) -> set:
    """Récupère la liste des fichiers déjà présents dans le dataset."""
    existing = set()
    page = 1
    while True:
        docs = dataset.list_documents(page=page, page_size=100)
        if not docs:
            break
        for doc in docs:
            existing.add(doc.name)
        if len(docs) < 100:
            break
        page += 1
    return existing


def main():
    parser = argparse.ArgumentParser(
        description="Upload un dossier vers un dataset RAGFlow"
    )
    parser.add_argument("--folder", required=True, help="Dossier local à uploader")
    parser.add_argument("--dataset", required=True, help="Nom du dataset RAGFlow")
    parser.add_argument(
        "--api-key",
        default=os.environ.get("RAGFLOW_API_KEY"),
        help="Clé API RAGFlow (ou variable d'env RAGFLOW_API_KEY)",
    )
    parser.add_argument(
        "--base-url",
        default=os.environ.get("RAGFLOW_BASE_URL", "http://localhost:9380"),
        help="URL de base de RAGFlow (défaut: http://localhost:9380)",
    )
    parser.add_argument(
        "--no-recursive",
        action="store_true",
        help="Ne pas parcourir les sous-dossiers",
    )
    parser.add_argument(
        "--parse",
        action="store_true",
        help="Lancer le parsing automatiquement après upload",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Ignorer les fichiers déjà présents dans le dataset",
    )
    args = parser.parse_args()

    if not args.api_key:
        sys.exit("Erreur : fournis --api-key ou définis RAGFLOW_API_KEY")

    folder = Path(args.folder).expanduser().resolve()
    if not folder.is_dir():
        sys.exit(f"Erreur : {folder} n'est pas un dossier")

    # Connexion à RAGFlow
    print(f"→ Connexion à {args.base_url}")
    rag = RAGFlow(api_key=args.api_key, base_url=args.base_url)

    # Récupère le dataset par son nom
    datasets = rag.list_datasets(name=args.dataset)
    if not datasets:
        sys.exit(f"Erreur : aucun dataset nommé '{args.dataset}' trouvé")
    dataset = datasets[0]
    print(f"→ Dataset trouvé : {dataset.name} (id={dataset.id})")

    # Liste les fichiers à uploader
    files = list(iter_files(folder, recursive=not args.no_recursive))
    if not files:
        sys.exit(f"Aucun fichier supporté trouvé dans {folder}")
    print(f"→ {len(files)} fichier(s) à traiter")

    # Filtre les déjà existants si demandé
    if args.skip_existing:
        print("→ Vérification des fichiers déjà présents…")
        existing = get_existing_filenames(dataset)
        before = len(files)
        files = [f for f in files if f.name not in existing]
        print(f"→ {before - len(files)} fichier(s) ignorés (déjà présents)")
        if not files:
            print("Rien à uploader.")
            return

    # Upload par batches
    uploaded_ids = []
    failed = []
    with tqdm(total=len(files), desc="Upload", unit="fichier") as pbar:
        for batch in chunked(files, BATCH_SIZE):
            payload = []
            for f in batch:
                try:
                    payload.append({
                        "display_name": f.name,
                        "blob": f.read_bytes(),
                    })
                except OSError as e:
                    failed.append((f, str(e)))
                    pbar.update(1)

            if not payload:
                continue

            try:
                docs = dataset.upload_documents(payload)
                if docs:
                    uploaded_ids.extend([d.id for d in docs])
            except Exception as e:
                # Si le batch entier échoue, on note tous les fichiers
                for f in batch:
                    failed.append((f, str(e)))
            finally:
                pbar.update(len(payload))

    print(f"\n✓ {len(uploaded_ids)} fichier(s) uploadés avec succès")
    if failed:
        print(f"✗ {len(failed)} échec(s) :")
        for f, err in failed[:10]:
            print(f"  - {f.name} : {err}")
        if len(failed) > 10:
            print(f"  … et {len(failed) - 10} de plus")

    # Lancement du parsing
    if args.parse and uploaded_ids:
        print(f"\n→ Lancement du parsing async sur {len(uploaded_ids)} document(s)…")
        # Le parsing peut nécessiter de splitter en batches selon le serveur
        for batch_ids in chunked(uploaded_ids, 50):
            dataset.async_parse_documents(batch_ids)
        print("✓ Parsing lancé. Suis l'avancement dans l'UI RAGFlow.")


if __name__ == "__main__":
    main()
