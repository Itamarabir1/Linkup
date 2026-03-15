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

const DAY_NAMES = ['ראשון', 'שני', 'שלישי', 'רביעי', 'חמישי', 'שישי', 'שבת'];

/** לפתק שיחה: לפני X דקות / HH:mm / אתמול / DD/MM */
export function formatConversationTime(date: string | Date | null): string {
  if (!date) return '';
  const d = typeof date === 'string' ? new Date(date) : date;
  if (isNaN(d.getTime())) return '';
  const now = new Date();
  const diffMs = now.getTime() - d.getTime();
  const diffMins = Math.floor(diffMs / (60 * 1000));
  if (diffMins < 60) return `לפני ${diffMins} דקות`;
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const day = new Date(d.getFullYear(), d.getMonth(), d.getDate());
  const dayDiff = Math.round((today.getTime() - day.getTime()) / (24 * 60 * 60 * 1000));
  const time = `${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`;
  if (dayDiff === 0) return time;
  if (dayDiff === 1) return 'אתמול';
  return `${d.getDate().toString().padStart(2, '0')}/${(d.getMonth() + 1).toString().padStart(2, '0')}`;
}

/** פורמט קצר לנסיעות: "היום 08:00", "מחר 07:30", "שישי 05:30" */
export function formatRideDate(date: string | Date): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  if (isNaN(d.getTime())) return '';
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const rideDay = new Date(d.getFullYear(), d.getMonth(), d.getDate());
  const diffDays = Math.round((rideDay.getTime() - today.getTime()) / (24 * 60 * 60 * 1000));
  const time = `${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`;
  if (diffDays === 0) return `היום ${time}`;
  if (diffDays === 1) return `מחר ${time}`;
  if (diffDays > 1 && diffDays < 7) return `${DAY_NAMES[rideDay.getDay()]} ${time}`;
  return formatDateTimeNoSeconds(d);
}
