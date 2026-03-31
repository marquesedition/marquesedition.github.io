export type SiteLocale = "es" | "en";

export const DEFAULT_LOCALE: SiteLocale = "es";

const normalizePath = (path: string) => {
  if (!path || path === "/") return "/";
  return path.endsWith("/") ? path : `${path}/`;
};

export const getLocaleHref = (locale: SiteLocale, path: string) => {
  const normalizedPath = normalizePath(path);
  if (locale === "es") return normalizedPath;
  return normalizedPath === "/" ? "/en/" : `/en${normalizedPath}`;
};

export const getAlternateLocale = (locale: SiteLocale): SiteLocale =>
  locale === "es" ? "en" : "es";
