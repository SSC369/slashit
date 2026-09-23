const RETURN_PARAM = "next";
const HOME_PATH = "/";

/** The sign-in URL that brings the reader back to `path` afterwards
 * (003 sub-plan 4.3, decision 1). Home needs no parameter. */
export const buildSignInPath = (path: string): string =>
  path === HOME_PATH ? "/sign-in" : `/sign-in?${RETURN_PARAM}=${encodeURIComponent(path)}`;

/**
 * Where sign-in should land, read from its own query string. Only a path on
 * this origin is honoured: "//evil.example" and "https://..." fall back to
 * home, so the parameter cannot be used as an open redirect.
 */
export const readReturnPath = (search: string): string => {
  const path = new URLSearchParams(search).get(RETURN_PARAM);
  if (path === null || !path.startsWith("/") || path.startsWith("//") || path.includes("\\")) {
    return HOME_PATH;
  }
  return path;
};
