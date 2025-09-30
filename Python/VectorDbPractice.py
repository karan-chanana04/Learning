import os, shutil, hashlib, tempfile
from pathlib import Path
from typing import List, Dict
import pandas as pd
from chromadb import PersistentClient
import google.generativeai as genai
from dotenv import load_dotenv

# ---------- CONFIG ----------
MODEL = "text-embedding-004"  # Updated to newer embedding model
TEXT_COL = "document"
CHUNK_SIZE_CHARS = 3500
CHUNK_OVERLAP_CHARS = 400
MIN_CHARS = 20
BATCH_SIZE = 96
COLLECTION = "my_collection"
# ----------------------------
global_env_path = Path.home() / ".env"
load_dotenv(global_env_path)
api_key = os.getenv("GOOGLE_API_KEY")


def pick_writable_dir() -> str:
    """
    Try several safe locations; return the first that is definitely writable.
    """
    candidates = [
        Path.home() / ".chroma" / COLLECTION,                                # user home (preferred)
        Path(os.environ.get("LOCALAPPDATA", Path.home())) / "Chroma" / COLLECTION,  # Windows-friendly
        Path(tempfile.gettempdir()) / "chroma" / COLLECTION,                 # last resort
    ]
    for p in candidates:
        p.mkdir(parents=True, exist_ok=True)
        probe = p / ".__writetest__"
        try:
            with open(probe, "w", encoding="utf-8") as f:
                f.write("ok")
            probe.unlink(missing_ok=True)
            return str(p)
        except Exception:
            continue
    raise RuntimeError("No writable directory found for Chroma.")

PERSIST_DIR = pick_writable_dir()
print(f"[info] Using PERSIST_DIR: {PERSIST_DIR}")

# Insert-only semantics: rebuild each run, so no updates occur.
shutil.rmtree(PERSIST_DIR, ignore_errors=True)
Path(PERSIST_DIR).mkdir(parents=True, exist_ok=True)

# --- init clients ---
#api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise RuntimeError("Set GEMINI_API_KEY or GOOGLE_API_KEY in your environment.")

# Configure the API key
genai.configure(api_key=api_key)

chroma = PersistentClient(path=PERSIST_DIR)
collection = chroma.create_collection(name=COLLECTION)

# --- helpers ---
def chunk_text(s: str, size: int, overlap: int) -> List[str]:
    s = (s or "").strip()
    if not s:
        return []
    if len(s) <= size:
        return [s] if len(s) >= MIN_CHARS else []
    chunks, start = [], 0
    while start < len(s):
        end = min(start + size, len(s))
        piece = s[start:end].strip()
        if len(piece) >= MIN_CHARS:
            chunks.append(piece)
        if end == len(s):
            break
        start = max(end - overlap, 0)
    return chunks

def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def batches(seq, n):
    for i in range(0, len(seq), n):
        yield seq[i:i+n]

# --- build (insert-only) ---
def build_insert_only(df: pd.DataFrame):
    docs: List[str] = []
    ids: List[str] = []
    metas: List[Dict] = []

    seen = set()  # dedupe identical chunks to avoid DuplicateIDError
    for _, row in df.iterrows():
        raw = str(row.get(TEXT_COL, "") or "")
        for ch in chunk_text(raw, CHUNK_SIZE_CHARS, CHUNK_OVERLAP_CHARS):
            _id = content_hash(ch)
            if _id in seen:
                continue
            seen.add(_id)
            ids.append(_id)
            docs.append(ch)
            metas.append({k: str(row[k]) for k in row.index if k != TEXT_COL})

    print(f"[info] Chunks prepared: {len(docs)}. Inserting...")





    for batch in batches(list(zip(ids, docs, metas)), BATCH_SIZE):
        b_ids  = [t[0] for t in batch]
        b_text = [t[1] for t in batch]
        b_meta = [t[2] for t in batch]

        vectors = []
        for text in b_text:
            try:
                embedding_response = genai.embed_content(
                    model="models/embedding-001",
                    content=text,
                    task_type="retrieval_document"
                )
                vectors.append(embedding_response["embedding"])
            except Exception as e:
                print(f"Error embedding text: {e}")
                # Use a zero vector as fallback (dimension may need adjustment)
                vectors.append([0.0] * 768)

        collection.add(ids=b_ids, documents=b_text, metadatas=b_meta, embeddings=vectors)

    print("[info] Insert-only vector DB ready.")

# Main execution
def main():
    # Load the CSV file
    csv_path = "/Users/karanchanana/Repos/Learning/Notebook/ai-medical-chatbot.csv"
    
    try:
        df = pd.read_csv(csv_path)
        print(f"[info] Loaded CSV with {len(df)} rows")
        print(f"[info] Columns: {df.columns.tolist()}")
        
        # Create the document column as you specified
        df['document'] = (
            df['Description'].fillna('') + '\n\n' +
            'Patient: ' + df['Patient'].fillna('') + '\n\n' +
            'Doctor: ' + df['Doctor'].fillna('')
        )
        
        print(f"[info] Created document column. Sample:")
        print(df['document'].iloc[0][:200] + "..." if len(df) > 0 else "No data")
        
        # Build the vector database
        build_insert_only(df.head(1000))
        
    except FileNotFoundError:
        print(f"[error] File not found: {csv_path}")
        print("[info] Please check the file path and ensure the file exists.")
    except Exception as e:
        print(f"[error] An error occurred: {e}")

if __name__ == "__main__":
    main()
    