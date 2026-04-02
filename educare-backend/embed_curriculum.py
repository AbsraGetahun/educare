import os
import json
import fitz
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

# Configuration
PDF_FOLDER = "curriculum_data"
INDEX_FOLDER = "faiss_index"
CHUNK_SIZE = 1000

# Create folders
os.makedirs(PDF_FOLDER, exist_ok=True)
os.makedirs(INDEX_FOLDER, exist_ok=True)

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
    
    for page_num, page in enumerate(doc):
        text = page.get_text()
        
        for i in range(0, len(text), CHUNK_SIZE):
            chunk = text[i:i+CHUNK_SIZE]
            if len(chunk.strip()) > 50:
                chunks.append(chunk)
                metadata.append({
                    "source": pdf_file,
                    "page": page_num + 1,
                    "chunk_index": len(chunks),
                    "text": chunk
                })
    
    doc.close()
    print(f"  Extracted {len([m for m in metadata if m['source'] == pdf_file])} chunks")

print(f"\nTotal chunks: {len(chunks)}")

if len(chunks) == 0:
    print("No text extracted from PDFs.")
    exit(1)

print("Creating TF-IDF embeddings...")
vectorizer = TfidfVectorizer(max_features=384)
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
        "chunk_index": metadata[i]["chunk_index"]
    })
chunks_path = os.path.join(INDEX_FOLDER, "chunks.json")
with open(chunks_path, 'w', encoding='utf-8') as f:
    json.dump(chunks_with_meta, f, indent=2)
print(f"Chunks saved to {chunks_path}")

print("\n✅ Curriculum embedding complete!")
print(f"Processed {len(chunks)} chunks from {len(pdf_files)} PDF files.")