export function amazonSearchUrl(title: string, author: string): string {
  const query = [title, author].filter(Boolean).join(" ");
  return `https://www.amazon.com/s?k=${encodeURIComponent(query)}&i=stripbooks`;
}
