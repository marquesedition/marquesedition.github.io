export const SITE_URL = "https://www.marquesedition.com";
export const SITE_NAME = "Marques Edition";

export const buildAbsoluteUrl = (path: string, base = SITE_URL) => new URL(path, base).href;
