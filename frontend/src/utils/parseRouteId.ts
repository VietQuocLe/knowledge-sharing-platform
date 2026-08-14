/** Parse a positive integer route param; returns null when invalid (NaN, zero, non-numeric). */
export function parseRouteId(raw: string | undefined): number | null {
  if (raw === undefined || raw === '' || !/^\d+$/.test(raw)) {
    return null
  }

  const id = Number(raw)
  return id > 0 ? id : null
}
