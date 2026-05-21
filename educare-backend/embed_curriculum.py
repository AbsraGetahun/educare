import os
import json
import re
import fitz
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

PDF_FOLDER = "curriculum_data"
INDEX_FOLDER = "faiss_index"
CHUNK_SIZE = 2000
MIN_CHUNK_LENGTH = 150

METADATA_PATTERNS = [
    'Authors:', 'Editor:', 'Evaluators:',
    'Federal Democratic Republic of Ethiopia',
    'Ministry of Education',
    'ISBN', 'Copyright',
]

EXCLUDE_PAGES = list(range(1, 10))

GRADE_FILENAME_MAP = {
    'grade9': 9,
    'grade10': 10,
    'grade11': 11,
    'grade12': 12,
}


def _parse_grade_from_filename(filename: str):
    """Return grade_level int guessed from the PDF filename, else None."""
    name = filename.lower()
    for key, grade in GRADE_FILENAME_MAP.items():
        if key in name:
            return grade
    return None


def _is_metadata_page(text: str, page_num: int) -> bool:
    """Check if page should be skipped (front matter or metadata)."""
    if page_num in EXCLUDE_PAGES:
        return True
    
    text_lower = text.lower()
    for pattern in METADATA_PATTERNS:
        if pattern.lower() in text_lower:
            return True
    
    return False


def _split_into_chunks(text: str, min_size: int = MIN_CHUNK_LENGTH) -> list:
    """Split text by paragraphs, sections, or fall back to fixed size."""
    chunks = []
    
    paragraphs = re.split(r'\n\s*\n', text)
    
    current_chunk = ""
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        
        if len(current_chunk) + len(para) + 1 < CHUNK_SIZE:
            current_chunk += " " + para if current_chunk else para
        else:
            if len(current_chunk) >= min_size:
                chunks.append(current_chunk)
            
            if len(para) >= min_size:
                current_chunk = para
            else:
                current_chunk = ""
    
    if len(current_chunk) >= min_size:
        chunks.append(current_chunk)
    
    return chunks


print("Using TF-IDF for text embeddings (no download required)...")

chunks = []
metadata = []

print(f"Scanning {PDF_FOLDER} for PDF files...")
pdf_files = [f for f in os.listdir(PDF_FOLDER) if f.endswith('.pdf')]

if not pdf_files:
    print(f"No PDF files found in {PDF_FOLDER}/ folder!")
    print("Please add your Grade 12 math PDF to this folder.")
    exit(1)

for pdf_file in pdf_files:
    print(f"Processing: {pdf_file}")
    pdf_path = os.path.join(PDF_FOLDER, pdf_file)
    
    doc = fitz.open(pdf_path)
    page_count = 0
    
    for page_num, page in enumerate(doc):
        page_num += 1
        text = page.get_text()
        
        if _is_metadata_page(text, page_num):
            continue
        
        text_chunks = _split_into_chunks(text)
        
        for chunk in text_chunks:
            if len(chunk.strip()) > MIN_CHUNK_LENGTH:
                chunks.append(chunk)
                metadata.append({
                    "source": pdf_file,
                    "page": page_num,
                    "chunk_index": len(chunks),
                    "text": chunk[:2500],
                    "grade_level": _parse_grade_from_filename(pdf_file)
                })
        page_count += 1
    
    doc.close()
    print(f"  Extracted {len([m for m in metadata if m['source'] == pdf_file])} chunks from {page_count} pages")

print(f"\nTotal chunks: {len(chunks)}")

if len(chunks) == 0:
    print("No text extracted from PDFs.")
    exit(1)

print("Creating TF-IDF embeddings...")
vectorizer = TfidfVectorizer(max_features=384, stop_words='english')
embeddings = vectorizer.fit_transform(chunks).toarray()

print("Saving vectorizer...")
import pickle
with open(os.path.join(INDEX_FOLDER, "vectorizer.pkl"), 'wb') as f:
    pickle.dump(vectorizer, f)

print("Creating FAISS index...")
import faiss
dimension = embeddings.shape[1]
index = faiss.IndexFlatL2(dimension)
index.add(np.array(embeddings).astype('float32'))

faiss_path = os.path.join(INDEX_FOLDER, "index.faiss")
faiss.write_index(index, faiss_path)
print(f"FAISS index saved to {faiss_path}")

metadata_path = os.path.join(INDEX_FOLDER, "metadata.json")
with open(metadata_path, 'w', encoding='utf-8') as f:
    json.dump(metadata, f, indent=2)
print(f"Metadata saved to {metadata_path}")

print("Saving text chunks...")
chunks_with_meta = []
for i, chunk in enumerate(chunks):
    chunks_with_meta.append({
        "text": chunk,
        "source": metadata[i]["source"],
        "page": metadata[i]["page"],
        "chunk_index": metadata[i]["chunk_index"],
        "grade_level": metadata[i]["grade_level"]
    })
chunks_path = os.path.join(INDEX_FOLDER, "chunks.json")
with open(chunks_path, 'w', encoding='utf-8') as f:
    json.dump(chunks_with_meta, f, indent=2)
print(f"Chunks saved to {chunks_path}")

print("\n✅ Curriculum embedding complete!")
print(f"Processed {len(chunks)} chunks from {len(pdf_files)} PDF files.")