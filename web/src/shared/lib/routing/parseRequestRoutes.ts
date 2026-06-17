const REQUEST_DETAILS_PATH_RE = /^\/requests\/(?!create$)([^/]+)$/;
const CONTRACTOR_REQUEST_DETAILS_PATH_RE = /^\/requests\/([^/]+)\/contractor$/;

const decodePathSegment = (segment: string): string => {
  try {
    return decodeURIComponent(segment);
  } catch {
    return segment;
  }
};

export const matchRequestDetailsPath = (pathname: string): string | null => {
  const match = pathname.match(REQUEST_DETAILS_PATH_RE);
  return match?.[1] ? decodePathSegment(match[1]) : null;
};

export const matchContractorRequestDetailsPath = (pathname: string): string | null => {
  const match = pathname.match(CONTRACTOR_REQUEST_DETAILS_PATH_RE);
  return match?.[1] ? decodePathSegment(match[1]) : null;
};

export const isRequestDetailsPath = (pathname: string): boolean => matchRequestDetailsPath(pathname) !== null;

export const isContractorRequestDetailsPath = (pathname: string): boolean =>
  matchContractorRequestDetailsPath(pathname) !== null;
