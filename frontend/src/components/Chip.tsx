interface ChipProps {
  label: string;
  active: boolean;
  onToggle: () => void;
}

export function Chip({ label, active, onToggle }: ChipProps) {
  return (
    <button
      type="button"
      className={`chip${active ? " chip--active" : ""}`}
      aria-pressed={active}
      onClick={onToggle}
    >
      {label}
    </button>
  );
}