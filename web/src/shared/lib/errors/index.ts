import {
  fallbackByActionHint,
  normalizeUserFacingText,
} from './userFacing';

export const getErrorMessage = (error: unknown, fallback: string) => {
  if (error instanceof Error && error.message) {
    return normalizeUserFacingText(error.message, fallbackByActionHint(fallback));
  }

  return normalizeUserFacingText(fallback, fallbackByActionHint(fallback));
};
