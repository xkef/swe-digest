// One JSON object per line. Workers Logs indexes the fields, so the
// dashboard can filter on `event` and on any field an event carries.
export function log(event: string, fields: Record<string, unknown> = {}): void {
  console.log(JSON.stringify({ event, ...fields }));
}
