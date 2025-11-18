import json
from pathlib import Path

from .models import Document

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"

with (DATA_DIR / "documents.json").open("r", encoding="utf-8") as f:
    RAW_DOCS = json.load(f)

DOCUMENTS: list[Document] = [Document(**d) for d in RAW_DOCS]
