const getDecimalSeparator = (locale: string) => (locale.startsWith("en") ? "." : ",");

export const formatCompactNumber = (value: number, locale = "es-ES") => {
  if (value >= 1000) {
    const whole = value / 1000;
    const separator = getDecimalSeparator(locale);
    return Number.isInteger(whole)
      ? `${whole.toFixed(0)}k`
      : `${whole.toFixed(1).replace(".", separator)}k`;
  }

  return String(value);
};

export const formatShortDate = (dateValue: string | Date, locale = "es-ES") => {
  const date = typeof dateValue === "string" ? new Date(`${dateValue}T12:00:00`) : dateValue;
  return new Intl.DateTimeFormat(locale, {
    day: "numeric",
    month: "short",
    year: "numeric",
  }).format(date);
};

export const formatShortSpanishDate = (dateValue: string | Date) =>
  formatShortDate(dateValue, "es-ES");
