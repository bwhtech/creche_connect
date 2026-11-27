const messages: Record<string, string> = Object.assign(Object.create(null), (window as any).translations)
export const lang: string = (window as any).lang ?? 'en'

export const __ = (message: string, ...args: (string | number)[]) =>
  (messages[message] || message).replace(/{(\d+)}/g, (match, i) => String(args[i] ?? match))

export function translateHtml(html: string) {
  if (lang === 'en') return html
  const doc = new DOMParser().parseFromString(html, 'text/html')
  for (const el of doc.body.querySelectorAll('p, li, h1, h2, h3, blockquote')) {
    const text = messages[el.textContent!.trim()]
    if (text) el.textContent = text
  }
  return doc.body.innerHTML
}
