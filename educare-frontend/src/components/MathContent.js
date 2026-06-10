import React, { useEffect, useRef } from 'react';
import { typesetMathInElement } from '../utils/renderMath';
import 'katex/dist/katex.min.css';

/**
 * Renders backend-generated learning-note HTML with KaTeX math support.
 */
function MathContent({ html, className = '' }) {
  const ref = useRef(null);

  useEffect(() => {
    if (ref.current) {
      typesetMathInElement(ref.current);
    }
  }, [html]);

  if (!html || !html.trim()) return null;

  return (
    <div
      ref={ref}
      className={`math-content rag-content ${className}`.trim()}
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}

export default MathContent;
