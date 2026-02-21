/**
 * פורמט תאריך ושעה בעברית בלי שניות.
 * דוגמה: "16.2.2026, 09:00"
 */
export function formatDateTimeNoSeconds(date: string | Date): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  if (isNaN(d.getTime())) return '';
  const day = d.getDate();
  const month = d.getMonth() + 1;
  const year = d.getFullYear();
  const h = d.getHours();
  const m = d.getMinutes();
  return `${day}.${month}.${year}, ${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}`;
}
