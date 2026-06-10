import React, { useRef } from 'react';
import { uploadFile } from '../services/api';
import { resolveUploadUrl } from '../utils/uploadUrl';

/**
 * Pick images/files from device, upload to server, return attachment metadata.
 * @param {string} context - 'peer' | 'quiz'
 */
function FilePicker({ context = 'peer', files, onChange, accept, label, imagesOnly = false }) {
  const inputRef = useRef(null);
  const [uploading, setUploading] = React.useState(false);
  const [err, setErr] = React.useState('');

  const defaultAccept = imagesOnly
    ? 'image/png,image/jpeg,image/gif,image/webp'
    : 'image/png,image/jpeg,image/gif,image/webp,.pdf,.doc,.docx,.txt,.ppt,.pptx,.xls,.xlsx';

  const handlePick = async (e) => {
    const picked = Array.from(e.target.files || []);
    if (!picked.length) return;
    setErr('');
    setUploading(true);
    const next = [...(files || [])];
    try {
      for (const file of picked) {
        if (next.length >= 5) break;
        const meta = await uploadFile(file, context);
        next.push({
          url: meta.url,
          file_name: meta.file_name,
          content_type: meta.content_type,
          is_image: meta.is_image,
        });
      }
      onChange(next);
    } catch (ex) {
      setErr(ex.response?.data?.error || ex.message || 'Upload failed');
    } finally {
      setUploading(false);
      if (inputRef.current) inputRef.current.value = '';
    }
  };

  const removeAt = (idx) => {
    onChange((files || []).filter((_, i) => i !== idx));
  };

  return (
    <div className="mt-2">
      {label && (
        <p className="text-xs font-medium text-gray-600 mb-1">{label}</p>
      )}
      <div className="flex flex-wrap gap-2 items-center">
        <input
          ref={inputRef}
          type="file"
          accept={accept || defaultAccept}
          multiple
          className="hidden"
          onChange={handlePick}
        />
        <button
          type="button"
          disabled={uploading || (files || []).length >= 5}
          onClick={() => inputRef.current?.click()}
          className="px-3 py-1.5 text-xs font-medium border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50"
        >
          {uploading ? 'Uploading…' : imagesOnly ? '📷 Add image' : '📎 Add image or file'}
        </button>
        <span className="text-[10px] text-gray-400">{(files || []).length}/5</span>
      </div>
      {err && <p className="text-xs text-red-600 mt-1">{err}</p>}
      {(files || []).length > 0 && (
        <div className="flex flex-wrap gap-2 mt-2">
          {(files || []).map((f, idx) => (
            <div
              key={idx}
              className="relative border border-gray-200 rounded-lg p-1 bg-gray-50"
            >
              {f.is_image ? (
                <img
                  src={resolveUploadUrl(f.url)}
                  alt={f.file_name}
                  className="h-16 w-16 object-cover rounded"
                />
              ) : (
                <span className="text-xs px-2 py-3 block max-w-[120px] truncate">
                  {f.file_name}
                </span>
              )}
              <button
                type="button"
                onClick={() => removeAt(idx)}
                className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white text-xs rounded-full leading-none"
                aria-label="Remove"
              >
                ×
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default FilePicker;
