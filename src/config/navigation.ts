export interface NavItem {
  href: string;
  label: string;
  external?: boolean;
}

const INNER_PAGE_NAV_ITEMS: NavItem[] = [
  { href: "/", label: "Inicio" },
  { href: "/about/", label: "About" },
  { href: "/reels/", label: "Reels" },
  { href: "/streams/", label: "Remixes" },
  { href: "/sets/", label: "Sets" },
  { href: "/events/", label: "Events" },
  { href: "/media-links/", label: "Media Links" },
  { href: "/booking/", label: "Booking" },
];

export const getInnerPageNav = (currentHref: string) =>
  INNER_PAGE_NAV_ITEMS.filter((item) => item.href !== currentHref);
