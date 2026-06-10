import katex from 'katex';

/**
 * Render math inside a DOM subtree (learning notes HTML).
 * Handles .math-latex spans and raw $...$ / $$...$$ delimiters in text nodes.
 */
export function typesetMathInElement(root) {
  if (!root) return;

  root.querySelectorAll('.math-latex').forEach((span) => {
    const tex = (span.textContent || '').trim();
    if (!tex) return;
    try {
      katex.render(tex, span, { throwOnError: false, displayMode: false });
    } catch {
      /* keep original text */
    }
  });

  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, null);
  const textNodes = [];
  let node;
  while ((node = walker.nextNode())) {
    if (node.parentElement?.closest('.math-latex, .katex')) continue;
    if (/\$[^$]+\$|\$\$[^$]+\$\$/.test(node.textContent)) {
      textNodes.push(node);
    }
  }

  textNodes.forEach((textNode) => {
    const text = textNode.textContent;
    const parts = text.split(/(\$\$[^$]+\$\$|\$[^$]+\$)/g);
    if (parts.length <= 1) return;

    const frag = document.createDocumentFragment();
    parts.forEach((part) => {
      if (!part) return;
      const display = part.startsWith('$$') && part.endsWith('$$');
      const inline = part.startsWith('$') && part.endsWith('$') && !display;
      if (display || inline) {
        const tex = part.slice(display ? 2 : 1, display ? -2 : -1);
        const el = document.createElement(display ? 'div' : 'span');
        el.className = display ? 'math-display katex-block' : 'math-inline';
        try {
          katex.render(tex, el, { throwOnError: false, displayMode: display });
        } catch {
          el.textContent = part;
        }
        frag.appendChild(el);
      } else {
        frag.appendChild(document.createTextNode(part));
      }
    });
    textNode.parentNode.replaceChild(frag, textNode);
  });
}

/**
 * Split plain text (chatbot) into React-friendly segments with math flag.
 */
export function splitMathSegments(text) {
  if (!text) return [];
  const parts = text.split(/(\$\$[^$]+\$\$|\$[^$]+\$)/g);
  return parts.filter(Boolean).map((part) => {
    const display = part.startsWith('$$') && part.endsWith('$$');
    const inline = part.startsWith('$') && part.endsWith('$') && !display;
    if (display || inline) {
      return {
        type: display ? 'display' : 'inline',
        tex: part.slice(display ? 2 : 1, display ? -2 : -1),
      };
    }
    return { type: 'text', value: part };
  });
}

export function renderTexToHtml(tex, displayMode = false) {
  try {
    return katex.renderToString(tex, { throwOnError: false, displayMode });
  } catch {
    return tex;
  }
}
