import regular from '../../../../shared/fonts/alabuga-sans-regular.woff2?inline';
import medium from '../../../../shared/fonts/alabuga-sans-medium.woff2?inline';
import bold from '../../../../shared/fonts/alabuga-sans-bold.woff2?inline';

// Sandboxed DOCX frames have an opaque origin and cannot share the page's fonts.
// Keep their fonts inside the document, with no network access or relaxed sandbox.
export const documentFontStyles = [
  [regular, '400'],
  [medium, '500 600'],
  [bold, '700'],
].map(([source, weight]) => `@font-face{font-family:"Alabuga Sans";src:url("${source}") format("woff2");font-style:normal;font-weight:${weight};font-display:swap}`).join('');
