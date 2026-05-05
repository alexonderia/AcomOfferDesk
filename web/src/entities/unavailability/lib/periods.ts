export const hasPeriodOverlapByDate = (
  leftStartIso: string,
  leftEndIso: string,
  rightStartIso: string,
  rightEndIso: string
) => {
  const leftStart = new Date(leftStartIso);
  const leftEnd = new Date(leftEndIso);
  const rightStart = new Date(rightStartIso);
  const rightEnd = new Date(rightEndIso);

  if (
    Number.isNaN(leftStart.getTime()) ||
    Number.isNaN(leftEnd.getTime()) ||
    Number.isNaN(rightStart.getTime()) ||
    Number.isNaN(rightEnd.getTime())
  ) {
    return false;
  }

  const leftStartDate = new Date(leftStart.getFullYear(), leftStart.getMonth(), leftStart.getDate());
  const leftEndDate = new Date(leftEnd.getFullYear(), leftEnd.getMonth(), leftEnd.getDate());
  const rightStartDate = new Date(rightStart.getFullYear(), rightStart.getMonth(), rightStart.getDate());
  const rightEndDate = new Date(rightEnd.getFullYear(), rightEnd.getMonth(), rightEnd.getDate());

  return leftStartDate <= rightEndDate && leftEndDate >= rightStartDate;
};
