export function matchSearch(text: string, query: string): boolean {
  if (!query) return true;
  try {
    return new RegExp(query, "i").test(text);
  } catch {
    return text.toLowerCase().includes(query.toLowerCase());
  }
}

/** Format ISO date string using browser locale */
export function formatDate(iso: string, locale?: string): string {
  try {
    return new Date(iso).toLocaleDateString(locale, { year: "numeric", month: "short", day: "numeric" });
  } catch {
    return iso.slice(0, 10);
  }
}

/** Format ISO datetime string using browser locale */
export function formatDateTime(iso: string, locale?: string): string {
  try {
    return new Date(iso).toLocaleString(locale, { year: "numeric", month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
  } catch {
    return iso.slice(0, 16).replace("T", " ");
  }
}

/** Format number using browser locale */
export function formatNumber(n: number, locale?: string, decimals?: number): string {
  return n.toLocaleString(locale, decimals !== undefined ? { minimumFractionDigits: decimals, maximumFractionDigits: decimals } : undefined);
}
