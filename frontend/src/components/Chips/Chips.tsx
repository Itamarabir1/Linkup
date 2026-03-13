import styles from './Chips.module.css';

export interface ChipItem {
  id: string;
  label: string;
}

interface ChipsProps {
  items: ChipItem[];
  activeId: string;
  onChange: (id: string) => void;
}

export default function Chips({ items, activeId, onChange }: ChipsProps) {
  return (
    <div className={styles.wrap} role="tablist">
      {items.map((item) => (
        <button
          key={item.id}
          type="button"
          role="tab"
          aria-selected={activeId === item.id}
          className={
            activeId === item.id
              ? `${styles.chip} ${styles.chipSelected}`
              : styles.chip
          }
          onClick={() => onChange(item.id)}
        >
          {item.label}
        </button>
      ))}
    </div>
  );
}
