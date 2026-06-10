"""HTTP routes for file uploads and static serving."""
import os
from flask import jsonify, request, send_from_directory
from upload_utils import UPLOAD_ROOT, ensure_upload_dirs, save_upload, init_quiz_question_image_column


def register_routes(app, get_db_connection):
    ensure_upload_dirs()

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        init_quiz_question_image_column(cur)
        conn.commit()
        cur.close()
        conn.close()
    except Exception:
        pass

    @app.route('/uploads/<path:subpath>')
    def serve_upload(subpath):
        """Serve uploaded files (images, PDFs) for peer help, quizzes, and profile pictures."""
        safe = subpath.replace('..', '').strip('/')
        if not safe.startswith(('peer/', 'quiz/', 'profile/')):
            return jsonify({'error': 'Not found'}), 404
        directory = UPLOAD_ROOT
        filename = safe.split('/', 1)[1] if '/' in safe else safe
        subdir = safe.split('/', 1)[0]
        return send_from_directory(os.path.join(directory, subdir), filename)

    @app.route('/api/upload', methods=['POST'])
    def upload_file():
        """
        Multipart upload: file + context ('peer' | 'quiz').
        Teachers use context=quiz for manual quiz question images.
        Students use context=peer for peer help attachments.
        """
        if 'file' not in request.files:
            return jsonify({'error': 'No file attached'}), 400
        context = (request.form.get('context') or 'peer').strip().lower()
        if context not in ('peer', 'quiz'):
            return jsonify({'error': 'context must be peer or quiz'}), 400
        try:
            meta = save_upload(request.files['file'], context)
            return jsonify(meta), 201
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            return jsonify({'error': str(e)}), 500
