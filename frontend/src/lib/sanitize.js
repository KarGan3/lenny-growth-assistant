import DOMPurify from 'dompurify'

// Defense in depth for rendering model-generated (untrusted) HTML artifacts.
//
// Layer 1 — DOMPurify: strip scripts, event handlers, and dangerous elements
//           before the HTML is ever inserted anywhere.
// Layer 2 — a locked-down <iframe sandbox srcDoc> (see ArtifactViewer): unique
//           origin, no same-origin, no scripts, no forms, no top-navigation.
// Layer 3 — a strict Content-Security-Policy inside the iframe document that
//           blocks ALL network requests, so even sanitized markup cannot
//           exfiltrate data via <img>, fonts, or background-image beacons.

export function sanitizeArtifactHtml(dirty) {
  return DOMPurify.sanitize(dirty ?? '', {
    WHOLE_DOCUMENT: true,
    // Scripts and interactive/network-capable elements are removed outright.
    FORBID_TAGS: ['script', 'iframe', 'object', 'embed', 'form', 'input', 'textarea', 'link', 'meta', 'base'],
    FORBID_ATTR: ['formaction', 'ping', 'srcset'],
    ALLOW_DATA_ATTR: false,
    // Inline styles are allowed (that's most of what a "HTML/CSS snippet" is),
    // but URL-bearing attributes are validated by DOMPurify against a safe list.
    ADD_ATTR: ['style', 'target'],
    ALLOWED_URI_REGEXP: /^(?:(?:https?|mailto|tel):|data:image\/(?:png|jpeg|gif|webp|svg\+xml);|#)/i,
  })
}

// Wrap sanitized HTML in a minimal, self-contained document with a strict CSP.
// This string is handed to the iframe's `srcDoc`. `default-src 'none'` means the
// document can render inline HTML/CSS but cannot load or contact anything.
export function buildSandboxSrcDoc(sanitizedHtml) {
  const parsed = new window.DOMParser().parseFromString(sanitizedHtml, 'text/html')
  const content = [...parsed.head.querySelectorAll('style')].map((s) => s.outerHTML).join('\n') + parsed.body.innerHTML
  return `<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta http-equiv="Content-Security-Policy"
      content="default-src 'none'; style-src 'unsafe-inline'; img-src data:; font-src data:; base-uri 'none'; form-action 'none';">
<style>
  html,body{margin:0;padding:16px;background:#fff;color:#0F3040;
    font-family:"IBM Plex Sans",system-ui,sans-serif;line-height:1.5;}
  a{color:#A56F63;}
  img,table{max-width:100%;}
</style>
</head>
<body>${content}</body>
</html>`
}
