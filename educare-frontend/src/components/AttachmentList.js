import React from 'react';
import { resolveUploadUrl } from '../utils/uploadUrl';

function AttachmentList({ attachments, className = '' }) {
  if (!attachments || attachments.length === 0) return null;

  return (
    <div className={`flex flex-wrap gap-3 mt-2 ${className}`}>
      {attachments.map((att, idx) => {
        const url = resolveUploadUrl(att.url);
        if (att.is_image) {
          return (
            <a
              key={idx}
              href={url}
              target="_blank"
              rel="noopener noreferrer"
              className="block"
            >
              <img
                src={url}
                alt={att.file_name || 'attachment'}
                className="max-w-full max-h-64 rounded-lg border border-gray-200 object-contain bg-gray-50"
              />
            </a>
          );
        }
        return (
          <a
            key={idx}
            href={url}
            target="_blank"
            rel="noopener noreferrer"
            download={att.file_name}
            className="inline-flex items-center gap-2 px-3 py-2 text-sm bg-gray-100 border border-gray-200 rounded-lg hover:bg-gray-200 text-gray-800"
          >
            <span aria-hidden>📎</span>
            {att.file_name || 'Download file'}
          </a>
        );
      })}
    </div>
  );
}

export default AttachmentList;
