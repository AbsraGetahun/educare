# Curriculum PDFs

Place all six mathematics textbooks in this folder, then rebuild the search index:

```bash
cd educare-backend
python embed_curriculum.py
```

## Required textbooks

You may use **either** canonical names **or** alternate MOE filenames (both are indexed correctly):

| Canonical name | Alternate filename |
|----------------|-------------------|
| `grade9_math.pdf` | `grade-9-mathematics-textbook.pdf` |
| `grade10_math.pdf` | `grade-10-mathematics-textbook.pdf` |
| `grade11_math.pdf` | `grade-11-mathematics-textbook.pdf` |
| `grade12_math.pdf` | `grade-12-mathematics-textbook.pdf` |
| `Extreme Mathematics Grade 9&10.pdf` | (same) |
| `Extreme Mathematics Grade 11&12.pdf` | (same) |

## Usage in EDUCARE

- **Curriculum search, study materials, assistant answers** → Grade 9–12 textbooks only
- **Quiz / exam-style question generation** → Extreme Mathematics + grade textbooks

After adding or renaming PDFs, run `python embed_curriculum.py` and restart the Flask backend.

Check index status: `GET /api/curriculum/index-status` (lists indexed vs missing books).
