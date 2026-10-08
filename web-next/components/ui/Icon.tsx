// Équivalent de web/utils/styles.py::icon() — Material Icon inline.
export function Icon({
  name,
  size = 20,
  color = "#2DAD7E",
  className,
}: {
  name: string;
  size?: number;
  color?: string;
  className?: string;
}) {
  return (
    <span
      className={`material-icons-outlined align-middle${className ? ` ${className}` : ""}`}
      style={{ fontSize: size, color, lineHeight: 1 }}
    >
      {name}
    </span>
  );
}
