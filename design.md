# UI and UX design

## Principles

Keep the conversation central, show evidence close to the answer, and make generated documents usable without exposing prompts or infrastructure. Use the requested palette as a dark theme: deep teal `#0F3040` is the page ground (`paper`), a lighter teal `#1D4C5E` elevates cards and panels (`surface`), a warm off-white (`#F5EFEA`, derived from the palette's own light neutral) carries primary text so it reads against the dark ground, slate `#464858` is lightened to `#AEB4C4` for secondary text, terracotta `#A56F63` is reserved for icons/borders (its contrast against dark is moderate — accent role only, never body text), and peach `#D99B7F` drives primary actions and highlights. Generated Markdown/HTML/CSS artifacts keep their own light, print-style document surface regardless of app theme, since they are meant to read as documents, not app chrome. Show the selected provider because it affects latency, quality and where data is processed.

## Information architecture

The desktop sidebar contains new chat, saved sessions, delete controls and provider selection. The center contains the thread, citations, artifact chips and composer. The right pane is an artifact preview with code, copy and download actions. At smaller widths the sidebar is a drawer and the artifact uses a full-screen overlay.

## Interaction states

- **New chat:** four prompts introduce Q&A, essays and HTML briefs.
- **Loading:** thread loading is separate from answer generation.
- **Retrieving:** status and source links appear before tokens.
- **Generating:** text streams, send changes to stop, concurrent sends are blocked.
- **Completed:** final text replaces partial output, and saved artifacts open automatically. Reopened sessions expose artifact chips.
- **Unsupported:** the assistant explains insufficient evidence. It does not offer a generated artifact.
- **Quality warning:** absent/invalid references or essay length deviations appear beside the draft.
- **Failure:** connection or stream failures offer a readable error; model billing errors do not expose a Node stack trace.
- **Provider selection:** options without keys or installed local models are disabled. A key indicates configuration, not paid endpoint health.
- **Artifact:** Markdown renders natively. HTML shows a protected preview; code view displays source as text.

## Responsive behavior

At 1024px the persistent sidebar and adjacent artifact pane are available. Below that breakpoint, the sidebar overlays the thread and the artifact occupies the viewport. Long content scrolls inside each pane. The composer grows to a bounded height. Check 390px, 768px, 1024px and 1440px in the manual plan.

## Accessibility

Inputs have labels, icon actions have accessible names, artifact preview/code controls have tab roles, and actionable elements are native buttons. Enter sends and Shift+Enter inserts a newline. Status/warning text identifies pending and degraded replies. Computed WCAG contrast against the dark page ground (`#0F3040`): primary text (`#F5EFEA`) ≈ 12.1:1, secondary text (`#AEB4C4`) ≈ 6.7:1, peach accent (`#D99B7F`) ≈ 5.9:1, both comfortably clear body-text AA (4.5:1). Against the elevated card surface (`#1D4C5E`) primary text is ≈ 8.2:1. Terracotta (`#A56F63`, ≈3.3:1) and the brightened danger red (`#E2685C`, ≈4.2:1) fall below body-text AA on dark backgrounds, so they stay restricted to icons, borders, and short status labels, never paragraph text — the same restriction the original light theme applied to low-contrast accents. Keyboard-only navigation, visible focus, zoom and screen-reader behavior need manual evaluation; no WCAG conformance is claimed. Overlay focus trapping and focus return remain improvements before a wider production rollout.

## Rendering decision

HTML starts from a grounded generated Markdown document and is assembled into a complete escaped HTML/CSS page by the backend. This gives predictable, readable briefs and avoids asking a small model to produce executable code. DOMPurify removes risky elements/attributes; the viewer's empty iframe sandbox denies capabilities and CSP blocks external loading. See `architecture.md` for exact permissions and limits.
