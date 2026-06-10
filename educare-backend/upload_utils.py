"""Save and serve user-uploaded images/files for peer help and manual quizzes."""
import os
import re
import uuid
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_ROOT = os.path.join(BASE_DIR, 'uploads')

PEER_IMAGE_EXT = {'.png', '.jpg', '.jpeg', '.gif', '.webp'}
PEER_FILE_EXT = {'.pdf', '.doc', '.docx', '.txt', '.ppt', '.pptx', '.xls', '.xlsx'}
QUIZ_IMAGE_EXT = {'.png', '.jpg', '.jpeg', '.gif', '.webp'}

MAX_PEER_IMAGE_BYTES = 5 * 1024 * 1024
MAX_PEER_FILE_BYTES = 10 * 1024 * 1024
MAX_QUIZ_IMAGE_BYTES = 5 * 1024 * 1024


def ensure_upload_dirs():
    for sub in ('peer', 'quiz'):
        os.makedirs(os.path.join(UPLOAD_ROOT, sub), exist_ok=True)


def _safe_filename(name: str) -> str:
    base = os.path.basename(name or 'file')
    base = re.sub(r'[^\w.\-]+', '_', base)
    return base[:120] or 'file'


def is_image_filename(filename: str, content_type: str = '') -> bool:
    ext = os.path.splitext(filename or '')[1].lower()
    if ext in PEER_IMAGE_EXT or ext in QUIZ_IMAGE_EXT:
        return True
    return (content_type or '').startswith('image/')


def save_upload(file_storage, context: str):
    """
    Save uploaded file. context: 'peer' | 'quiz'
    Returns dict with url, file_name, content_type, is_image, size
    """
    if not file_storage or not file_storage.filename:
        raise ValueError('No file provided')

    ensure_upload_dirs()
    original = file_storage.filename
    ext = os.path.splitext(original)[1].lower()
    content_type = (file_storage.content_type or '').lower()

    if context == 'quiz':
        if ext not in QUIZ_IMAGE_EXT:
            raise ValueError('Quiz questions only support images (PNG, JPG, GIF, WEBP)')
        max_bytes = MAX_QUIZ_IMAGE_BYTES
        subdir = 'quiz'
    elif context == 'peer':
        if ext not in PEER_IMAGE_EXT and ext not in PEER_FILE_EXT:
            raise ValueError(
                'Unsupported file type. Use images (PNG, JPG, GIF, WEBP) or PDF, Word, TXT, PowerPoint, Excel.'
            )
        max_bytes = MAX_PEER_IMAGE_BYTES if ext in PEER_IMAGE_EXT else MAX_PEER_FILE_BYTES
        subdir = 'peer'
    else:
        raise ValueError('Invalid upload context')

    file_storage.stream.seek(0, os.SEEK_END)
    size = file_storage.stream.tell()
    file_storage.stream.seek(0)
    if size > max_bytes:
        raise ValueError(f'File too large (max {max_bytes // (1024 * 1024)} MB)')

    stamp = datetime.utcnow().strftime('%Y%m%d')
    unique = uuid.uuid4().hex[:12]
    stored = f'{stamp}_{unique}_{_safe_filename(original)}'
    folder = os.path.join(UPLOAD_ROOT, subdir)
    path = os.path.join(folder, stored)
    file_storage.save(path)

    url = f'/uploads/{subdir}/{stored}'
    return {
        'url': url,
        'file_name': original,
        'content_type': content_type or 'application/octet-stream',
        'is_image': is_image_filename(original, content_type),
        'size': size,
    }


def init_quiz_question_image_column(cursor):
    try:
        cursor.execute("SHOW COLUMNS FROM quiz_questions LIKE 'question_image'")
        if not cursor.fetchone():
            cursor.execute(
                "ALTER TABLE quiz_questions ADD COLUMN question_image VARCHAR(512) NULL AFTER question_text"
            )
    except Exception:
        pass
