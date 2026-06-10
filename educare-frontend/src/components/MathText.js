import React from 'react';
import { splitMathSegments, renderTexToHtml } from '../utils/renderMath';
import 'katex/dist/katex.min.css';

/**
 * Plain-text assistant messages with LaTeX ($...$, $$...$$) rendering.
 */
function MathText({ text, className = '' }) {
  if (!text) return null;
  const segments = splitMathSegments(text);

  return (
    <div className={`math-text whitespace-pre-wrap ${className}`.trim()}>
      {segments.map((seg, i) => {
        if (seg.type === 'text') {
          return <span key={i}>{seg.value}</span>;
        }
        return (
          <span
            key={i}
            className={seg.type === 'display' ? 'math-display block my-1' : 'math-inline'}
            dangerouslySetInnerHTML={{
              __html: renderTexToHtml(seg.tex, seg.type === 'display'),
            }}
          />
        );
      })}
    </div>
  );
}

export default MathText;
