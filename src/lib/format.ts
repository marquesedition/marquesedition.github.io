export const formatCompactNumber = (value: number) => {
  if (value >= 1000) {
    const whole = value / 1000;
    return Number.isInteger(whole) ? `${whole.toFixed(0)}k` : `${whole.toFixed(1).replace(".", ",")}k`;
  }

  return String(value);
};

export const formatShortSpanishDate = (dateValue: string | Date) => {
  const date = typeof dateValue === "string" ? new Date(`${dateValue}T12:00:00`) : dateValue;
  return new Intl.DateTimeFormat("es-ES", {
    day: "numeric",
    month: "short",
    year: "numeric",
  }).format(date);
};
