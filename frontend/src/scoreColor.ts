export function scoreColor(pct: number): string {
  const clamped = Math.max(0, Math.min(100, pct));
  return `hsl(${clamped * 1.2}, 65%, 45%)`;
}
