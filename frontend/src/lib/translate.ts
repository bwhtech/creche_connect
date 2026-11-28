const messages: Record<string, string> = Object.assign(Object.create(null), (window as any).translations)
export const lang: string = (window as any).lang ?? 'en'

export const __ = (message: string, ...args: (string | number)[]) =>
  (messages[message] || message).replace(/{(\d+)}/g, (match, i) => String(args[i] ?? match))
