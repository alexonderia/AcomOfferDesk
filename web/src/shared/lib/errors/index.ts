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

export const formatSettledTaskErrors = (
  results: PromiseSettledResult<unknown>[],
  labels: string[],
  fallback: string,
): string[] =>
  results.flatMap((result, index) => {
    if (result.status === 'fulfilled') {
      return [];
    }

    const label = labels[index]?.trim();
    const message = getErrorMessage(result.reason, fallback);
    return [label ? `${label}: ${message}` : message];
  });

export const joinUserFacingErrors = (errors: string[]): string | null => {
  if (errors.length === 0) {
    return null;
  }

  return errors.join('\n');
};
