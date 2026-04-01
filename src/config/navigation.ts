import { getLocaleHref, type SiteLocale } from "../lib/i18n";

export interface NavItem {
  href: string;
  label: string;
  external?: boolean;
}

const INNER_PAGE_NAV_ITEMS = [
  { path: "/", labels: { es: "Inicio", en: "Home" } },
  { path: "/about/", labels: { es: "About", en: "About" } },
  { path: "/reels/", labels: { es: "Reels", en: "Reels" } },
  { path: "/streams/", labels: { es: "Remixes", en: "Remixes" } },
  { path: "/sets/", labels: { es: "Sets", en: "Sets" } },
  { path: "/library/", labels: { es: "Library", en: "Library" } },
  { path: "/events/", labels: { es: "Events", en: "Events" } },
  { path: "/media-links/", labels: { es: "Media Links", en: "Media Links" } },
  { path: "/booking/", labels: { es: "Booking", en: "Booking" } },
];

const TRANSLATED_EN_PATHS = new Set(["/", "/about/", "/booking/"]);

const resolveNavHref = (locale: SiteLocale, path: string) => {
  if (locale === "en" && !TRANSLATED_EN_PATHS.has(path)) return path;
  return getLocaleHref(locale, path);
};

export const getInnerPageNav = (currentPath: string, locale: SiteLocale = "es"): NavItem[] => {
  const currentHref = resolveNavHref(locale, currentPath);

  return INNER_PAGE_NAV_ITEMS.map((item) => ({
    href: resolveNavHref(locale, item.path),
    label: item.labels[locale],
  })).filter((item) => item.href !== currentHref);
};
