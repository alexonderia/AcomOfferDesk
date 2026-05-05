import { ChangeEvent, MouseEvent as ReactMouseEvent, ReactNode, useEffect, useMemo, useRef, useState } from 'react';
import AddRounded from '@mui/icons-material/AddRounded';
import ArrowDownwardRounded from '@mui/icons-material/ArrowDownwardRounded';
import ArrowUpwardRounded from '@mui/icons-material/ArrowUpwardRounded';
import FilterAltRounded from '@mui/icons-material/FilterAltRounded';
import KeyboardArrowDownRounded from '@mui/icons-material/KeyboardArrowDownRounded';
import NavigateBeforeRounded from '@mui/icons-material/NavigateBeforeRounded';
import NavigateNextRounded from '@mui/icons-material/NavigateNextRounded';
import SearchRounded from '@mui/icons-material/SearchRounded';
import SettingsOutlined from '@mui/icons-material/SettingsOutlined';
import TableRowsRounded from '@mui/icons-material/TableRowsRounded';
import UnfoldMoreRounded from '@mui/icons-material/UnfoldMoreRounded';
import WindowRounded from '@mui/icons-material/WindowRounded';
import ButtonBase from '@mui/material/ButtonBase';
import Divider from '@mui/material/Divider';
import InputBase from '@mui/material/InputBase';
import MenuItem from '@mui/material/MenuItem';
import Paper from '@mui/material/Paper';
import Popover from '@mui/material/Popover';
import Select from '@mui/material/Select';
import Stack from '@mui/material/Stack';
import Switch from '@mui/material/Switch';
import Typography from '@mui/material/Typography';
import Checkbox from '@mui/material/Checkbox';
import FormControlLabel from '@mui/material/FormControlLabel';
import FormGroup from '@mui/material/FormGroup';
import Button from '@mui/material/Button';
import { alpha, useTheme } from '@mui/material/styles';
import { ActionButton } from '@shared/components/ActionButton';
import { useIsMobileViewport } from '@shared/lib/responsive';

type CellAlign = 'left' | 'center' | 'right';

type TableUiScale = {
  toolbarGap: number;
  searchWidth: number;
  searchHeight: number;
  controlRadius: number;
  headerHeight: number;
  rowHeight: number;
  footerHeight: number;
  pagerButtonSize: number;
  rowsPerPageWidth: number;
  fontSize: number;
  iconSize: number;
  rowGap: string;
  gridColumnGap: number;
  rowPaddingX: number;
  cellPaddingX: number;
};

type ColumnResizeState = {
  index: number;
  startX: number;
  initialWidths: number[];
};

const DEFAULT_COLUMN_WIDTH = 160;
const FR_COLUMN_WIDTH_UNIT = 150;
const MIN_COLUMN_WIDTH = 120;
const MIN_NARROW_COLUMN_WIDTH = 40;
type PaginationItem = number | 'ellipsis-left' | 'ellipsis-right';
type ColumnFilterKind = 'select' | 'none';
type SortDirection = 'asc' | 'desc';
type DataViewMode = 'table' | 'cards';

export type TableTemplateFilterOption = {
  label: string;
  value: string;
};

const tableUiScale: TableUiScale = {
  toolbarGap: 12,
  searchWidth: 360,
  searchHeight: 44,
  controlRadius: 12,
  headerHeight: 44,
  rowHeight: 52,
  footerHeight: 56,
  pagerButtonSize: 40,
  rowsPerPageWidth: 64,
  fontSize: 15,
  iconSize: 22,
  rowGap: '2px',
  gridColumnGap: 0,
  rowPaddingX: 2,
  cellPaddingX: 0.75,
};

export type TableTemplateColumn<T> = {
  id: string;
  header: string;
  field?: keyof T;
  width?: string;
  minWidth?: number;
  align?: CellAlign;
  filterKind?: ColumnFilterKind;
  filterOptions?: TableTemplateFilterOption[];
  getFilterValue?: (row: T) => string;
  sortable?: boolean;
  getSortValue?: (row: T) => unknown;
  renderCell?: (row: T) => ReactNode;
  renderValue?: (value: unknown, row: T) => ReactNode;
  getSearchValue?: (row: T) => string;
};

export type TableTemplateProps<T> = {
  columns: TableTemplateColumn<T>[];
  rows: T[];
  isLoading?: boolean;
  statusContent?: ReactNode;
  onRowClick?: (row: T) => void;
  getCardPrimaryText?: (row: T) => ReactNode;
  getCardSecondaryText?: (row: T) => ReactNode;
  renderCard?: (row: T, rowIndex: number) => ReactNode;
  cardExcludedColumnIds?: string[];
  getRowId?: (row: T, index: number) => string | number;
  showSearch?: boolean;
  searchPlaceholder?: string;
  addButtonLabel?: string;
  onAddClick?: () => void;
  showAddAction?: boolean;
  onSettingsClick?: () => void;
  showViewToggle?: boolean;
  defaultViewMode?: DataViewMode;
  showSettingsAction?: boolean;
  rowsPerPageOptions?: number[];
  defaultRowsPerPage?: number;
  noRowsLabel?: string;
  noSearchResultsLabel?: string;
  minTableWidth?: number;
  onSearchChange?: (value: string) => void;
  resizableColumns?: boolean;
  cardExpansionControl?: {
    checked: boolean;
    onChange: (checked: boolean) => void;
    openLabel?: string;
    closeLabel?: string;
  };
};

function alignToFlex(align: CellAlign | undefined) {
  if (align === 'center') {
    return 'center';
  }

  if (align === 'right') {
    return 'flex-end';
  }

  return 'flex-start';
}

function normalizeSearch(value: string) {
  return value.trim().toLocaleLowerCase();
}

function getColumnMinWidth<T>(column: TableTemplateColumn<T>) {
  if (typeof column.minWidth === 'number' && Number.isFinite(column.minWidth)) {
    return Math.max(MIN_NARROW_COLUMN_WIDTH, column.minWidth);
  }

  return MIN_COLUMN_WIDTH;
}

function parseColumnWidth(width: string | undefined, columnMinWidth: number) {
  if (!width) {
    return DEFAULT_COLUMN_WIDTH;
  }

  const normalized = width.trim().toLocaleLowerCase();

  if (normalized.endsWith('px')) {
    const parsed = Number.parseFloat(normalized.replace('px', ''));
    return Number.isFinite(parsed) ? Math.max(columnMinWidth, parsed) : DEFAULT_COLUMN_WIDTH;
  }

  if (normalized.endsWith('fr')) {
    const parsed = Number.parseFloat(normalized.replace('fr', ''));
    return Number.isFinite(parsed) ? Math.max(columnMinWidth, parsed * FR_COLUMN_WIDTH_UNIT) : DEFAULT_COLUMN_WIDTH;
  }

  const parsed = Number.parseFloat(normalized);
  return Number.isFinite(parsed) ? Math.max(columnMinWidth, parsed) : DEFAULT_COLUMN_WIDTH;
}

function isStretchableColumnWidth(width: string | undefined) {
  if (!width) {
    return true;
  }

  return width.trim().toLocaleLowerCase().endsWith('fr');
}

function valueToText(value: unknown): string {
  if (value === null || value === undefined) {
    return '';
  }

  if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean' || typeof value === 'bigint') {
    return String(value);
  }

  if (value instanceof Date) {
    return value.toISOString();
  }

  if (Array.isArray(value)) {
    return value.map(valueToText).join(' ');
  }

  if (typeof value === 'object') {
    return Object.values(value as Record<string, unknown>).map(valueToText).join(' ');
  }

  return '';
}

function valueToDisplay(value: unknown) {
  const text = valueToText(value).trim();
  return text.length > 0 ? text : '-';
}

function getSearchTextByColumn<T>(column: TableTemplateColumn<T>, row: T) {
  if (column.getSearchValue) {
    return column.getSearchValue(row);
  }

  if (column.field) {
    return valueToText(row[column.field]);
  }

  return '';
}

function getFilterTextByColumn<T>(column: TableTemplateColumn<T>, row: T) {
  if (column.getFilterValue) {
    return column.getFilterValue(row);
  }

  return getSearchTextByColumn(column, row);
}

function getSortValueByColumn<T>(column: TableTemplateColumn<T>, row: T) {
  if (column.getSortValue) {
    return column.getSortValue(row);
  }

  if (column.field) {
    const rawValue = row[column.field];

    if (
      typeof rawValue === 'string' ||
      typeof rawValue === 'number' ||
      typeof rawValue === 'boolean' ||
      rawValue instanceof Date ||
      rawValue === null ||
      rawValue === undefined
    ) {
      return rawValue;
    }

    return valueToText(rawValue);
  }

  return getSearchTextByColumn(column, row);
}

function getColumnSignature<T>(column: TableTemplateColumn<T>) {
  return `${column.id} ${column.header}`.toLocaleLowerCase();
}

function getContactFieldLabel<T>(column: TableTemplateColumn<T>) {
  const signature = getColumnSignature(column);
  const id = column.id.toLocaleLowerCase();
  if (id.includes('phone') || signature.includes('phone')) {
    return 'Телефон';
  }
  if (id.includes('email') || signature.includes('email') || signature.includes('mail')) {
    return 'Почта';
  }
  return column.header;
}

function compareSortValues(left: unknown, right: unknown) {
  if (left === right) {
    return 0;
  }
  if (left === null || left === undefined) {
    return -1;
  }
  if (right === null || right === undefined) {
    return 1;
  }
  if (left instanceof Date && right instanceof Date) {
    return left.getTime() - right.getTime();
  }
  if (typeof left === 'number' && typeof right === 'number') {
    return left - right;
  }
  if (typeof left === 'boolean' && typeof right === 'boolean') {
    return Number(left) - Number(right);
  }
  return String(left).localeCompare(String(right), 'ru', { sensitivity: 'base', numeric: true });
}

function getColumnContentWeight<T>(column: TableTemplateColumn<T>, rows: T[]) {
  const headerLength = column.header.trim().length;
  const valuesLength = rows.reduce((maxLength, row) => {
    const value = getSearchTextByColumn(column, row);
    return Math.max(maxLength, value.trim().length);
  }, 0);
  const totalLength = Math.max(headerLength, valuesLength);
  return Math.max(8, Math.min(40, totalLength));
}

function resolveDefaultColumnWidths<T>(
  columns: TableTemplateColumn<T>[],
  rows: T[],
  minTableContentWidth: number
) {
  const columnMinWidths = columns.map((column) => getColumnMinWidth(column));
  const explicitWidths = columns.map((column, index) => (column.width ? parseColumnWidth(column.width, columnMinWidths[index]) : null));
  const explicitTotal = explicitWidths.reduce<number>((total, width) => total + (width ?? 0), 0);

  const autoColumnIndexes = explicitWidths
    .map((width, index) => ({ width, index }))
    .filter((item) => item.width === null)
    .map((item) => item.index);

  if (autoColumnIndexes.length === 0) {
    return explicitWidths.map((width, index) => width ?? Math.max(DEFAULT_COLUMN_WIDTH, columnMinWidths[index]));
  }

  const autoWeights = autoColumnIndexes.map((index) => getColumnContentWeight(columns[index], rows));
  const totalWeight = autoWeights.reduce<number>((sum, weight) => sum + weight, 0);
  const minAutoTotal = autoColumnIndexes.reduce<number>((sum, index) => sum + columnMinWidths[index], 0);
  const availableForAuto = Math.max(minAutoTotal, minTableContentWidth - explicitTotal);

  return columns.map((column, index) => {
    const explicitWidth = explicitWidths[index];
    if (explicitWidth !== null) {
      return explicitWidth;
    }
    const autoIndex = autoColumnIndexes.indexOf(index);
    const weight = autoWeights[autoIndex];
    const proportionalWidth = (availableForAuto * weight) / totalWeight;
    return Math.max(getColumnMinWidth(column), proportionalWidth);
  });
}

function getPaginationItems(currentPage: number, totalPages: number): PaginationItem[] {
  if (totalPages <= 7) {
    return Array.from({ length: totalPages }, (_, index) => index + 1);
  }

  if (currentPage <= 4) {
    return [1, 2, 3, 4, 5, 'ellipsis-right', totalPages];
  }

  if (currentPage >= totalPages - 3) {
    return [1, 'ellipsis-left', totalPages - 4, totalPages - 3, totalPages - 2, totalPages - 1, totalPages];
  }

  return [1, 'ellipsis-left', currentPage - 1, currentPage, currentPage + 1, 'ellipsis-right', totalPages];
}

export function TableTemplate<T>({
  columns,
  rows,
  isLoading = false,
  statusContent,
  onRowClick,
  getCardPrimaryText,
  getCardSecondaryText,
  renderCard,
  cardExcludedColumnIds = [],
  getRowId,
  showSearch = true,
  searchPlaceholder = 'Найти',
  addButtonLabel = 'Добавить',
  onAddClick,
  showAddAction = true,
  onSettingsClick,
  showViewToggle = true,
  defaultViewMode,
  showSettingsAction = true,
  rowsPerPageOptions = [8, 16, 32],
  defaultRowsPerPage,
  noRowsLabel = 'Список пуст',
  noSearchResultsLabel = 'Ничего не найдено',
  minTableWidth = 980,
  onSearchChange,
  resizableColumns = true,
  cardExpansionControl
}: TableTemplateProps<T>) {
  const theme = useTheme();
  const isMobileViewport = useIsMobileViewport();
  const {
    toolbarGap,
    searchWidth,
    searchHeight,
    controlRadius,
    headerHeight,
    rowHeight,
    footerHeight,
    pagerButtonSize,
    rowsPerPageWidth,
    fontSize,
    iconSize,
    rowGap,
    gridColumnGap,
    rowPaddingX,
    cellPaddingX
  } = tableUiScale;

  const allColumnIds = useMemo(() => columns.map((column) => column.id), [columns]);
  const [visibleColumnIds, setVisibleColumnIds] = useState<string[]>(allColumnIds);
  const [settingsAnchorEl, setSettingsAnchorEl] = useState<HTMLElement | null>(null);
  const rowHorizontalPadding = Number.parseFloat(theme.spacing(rowPaddingX));
  const rowPaddingTotal = rowHorizontalPadding * 2;

  useEffect(() => {
    setVisibleColumnIds((currentVisibleColumnIds) => {
      const nextVisibleColumnIds = allColumnIds.filter((columnId) => currentVisibleColumnIds.includes(columnId));
      return nextVisibleColumnIds.length > 0 ? nextVisibleColumnIds : allColumnIds;
    });
  }, [allColumnIds]);

  const visibleColumns = useMemo(
    () => columns.filter((column) => visibleColumnIds.includes(column.id)),
    [columns, visibleColumnIds]
  );

  const getMinTableContentWidth = (targetColumns: TableTemplateColumn<T>[]) => {
    const minColumnsTotalWidth = targetColumns.reduce((total, column) => total + getColumnMinWidth(column), 0);
    const safeMinColumnsTotalWidth = targetColumns.length > 0 ? minColumnsTotalWidth : MIN_COLUMN_WIDTH;
    return Math.max(safeMinColumnsTotalWidth, minTableWidth - rowPaddingTotal);
  };
  const minTableContentWidth = getMinTableContentWidth(visibleColumns);

  const [columnWidths, setColumnWidths] = useState<number[]>(() =>
    resolveDefaultColumnWidths(visibleColumns, rows, minTableContentWidth)
  );
  const [hasManualColumnSizing, setHasManualColumnSizing] = useState(false);
  const [isResizingColumn, setIsResizingColumn] = useState(false);
  const [viewportWidth, setViewportWidth] = useState(minTableWidth);
  const resizeStateRef = useRef<ColumnResizeState | null>(null);
  const viewportRef = useRef<HTMLDivElement | null>(null);

  const safeRowsPerPageOptions = useMemo(() => {
    const positiveOptions = rowsPerPageOptions.filter((value) => Number.isFinite(value) && value > 0);
    const uniqueOptions = Array.from(new Set(positiveOptions));
    return uniqueOptions.length > 0 ? uniqueOptions : [8];
  }, [rowsPerPageOptions]);

  const [searchValue, setSearchValue] = useState('');
  const [columnFilters, setColumnFilters] = useState<Record<string, string[]>>({});
  const [sortState, setSortState] = useState<{ columnId: string; direction: SortDirection } | null>(null);
  const [selectFilterAnchor, setSelectFilterAnchor] = useState<{ columnId: string; anchorEl: HTMLElement } | null>(null);
  const [viewMode, setViewMode] = useState<DataViewMode>(defaultViewMode ?? (isMobileViewport ? 'cards' : 'table'));
  const hasUserToggledViewMode = useRef(false);
  const [rowsPerPage, setRowsPerPage] = useState(
    defaultRowsPerPage && safeRowsPerPageOptions.includes(defaultRowsPerPage)
      ? defaultRowsPerPage
      : safeRowsPerPageOptions[0]
  );
  const [page, setPage] = useState(1);

  useEffect(() => {
    if (!defaultViewMode) {
      return;
    }

    hasUserToggledViewMode.current = false;
    setViewMode(defaultViewMode);
  }, [defaultViewMode]);

  useEffect(() => {
    if (isMobileViewport) {
      setViewMode('cards');
      return;
    }

    if (defaultViewMode || hasUserToggledViewMode.current) {
      return;
    }

    setViewMode('table');
  }, [defaultViewMode, isMobileViewport]);

  useEffect(() => {
    setColumnFilters((currentFilters) => {
      const nextFilters = Object.entries(currentFilters).filter(([columnId]) => allColumnIds.includes(columnId));
      return Object.fromEntries(nextFilters);
    });
  }, [allColumnIds]);

  useEffect(() => {
    if (!sortState) {
      return;
    }
    if (!visibleColumns.some((column) => column.id === sortState.columnId)) {
      setSortState(null);
    }
  }, [sortState, visibleColumns]);

  useEffect(() => {
    if (!selectFilterAnchor) {
      return;
    }
    const hasSelectColumn = visibleColumns.some(
      (column) => column.id === selectFilterAnchor.columnId && column.filterKind === 'select'
    );
    if (!hasSelectColumn) {
      setSelectFilterAnchor(null);
    }
  }, [selectFilterAnchor, visibleColumns]);

  useEffect(() => {
    const nextWidths = resolveDefaultColumnWidths(visibleColumns, rows, minTableContentWidth);
    if (!hasManualColumnSizing || columnWidths.length !== visibleColumns.length) {
      setColumnWidths(nextWidths);
    }
  }, [columnWidths.length, hasManualColumnSizing, minTableContentWidth, rows, visibleColumns]);

  useEffect(() => {
    const element = viewportRef.current;
    if (!element) {
      return;
    }

    const syncViewportWidth = () => {
      setViewportWidth(element.clientWidth);
    };

    syncViewportWidth();
    if (typeof ResizeObserver === 'undefined') {
      window.addEventListener('resize', syncViewportWidth);
      return () => window.removeEventListener('resize', syncViewportWidth);
    }

    const observer = new ResizeObserver(() => {
      syncViewportWidth();
    });

    observer.observe(element);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    if (!isResizingColumn) {
      return;
    }

    const handleMouseMove = (event: MouseEvent) => {
      const state = resizeStateRef.current;
      if (!state) {
        return;
      }

      const leftIndex = state.index;
      const rightIndex = state.index + 1;
      const initialLeftWidth = state.initialWidths[leftIndex];
      const initialRightWidth = state.initialWidths[rightIndex];
      if (initialLeftWidth === undefined || initialRightWidth === undefined) {
        return;
      }

      const widthDelta = event.clientX - state.startX;
      const leftMinWidth = getColumnMinWidth(visibleColumns[leftIndex]);
      const rightMinWidth = getColumnMinWidth(visibleColumns[rightIndex]);
      const minDelta = leftMinWidth - initialLeftWidth;
      const maxDelta = initialRightWidth - rightMinWidth;
      const boundedDelta = Math.min(maxDelta, Math.max(minDelta, widthDelta));

      const nextWidths = [...state.initialWidths];
      nextWidths[leftIndex] = initialLeftWidth + boundedDelta;
      nextWidths[rightIndex] = initialRightWidth - boundedDelta;
      setColumnWidths(nextWidths);
    };

    const handleMouseUp = () => {
      resizeStateRef.current = null;
      setIsResizingColumn(false);
      document.body.style.removeProperty('cursor');
      document.body.style.removeProperty('user-select');
    };

    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);
    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isResizingColumn, visibleColumns]);

  useEffect(() => {
    if (!Number.isFinite(rowsPerPage) || rowsPerPage < 1) {
      setRowsPerPage(safeRowsPerPageOptions[0]);
    }
  }, [rowsPerPage, safeRowsPerPageOptions]);

  const normalizedSearch = useMemo(() => normalizeSearch(searchValue), [searchValue]);

  const filteredRows = useMemo(
    () =>
      rows.filter((row) => {
        if (normalizedSearch) {
          const byColumns = columns.map((column) => getSearchTextByColumn(column, row)).join(' ');
          const allRowText = valueToText(row);
          const joinedText = `${byColumns} ${allRowText}`.toLocaleLowerCase();
          if (!joinedText.includes(normalizedSearch)) {
            return false;
          }
        }

        return visibleColumns.every((column) => {
          if (column.filterKind !== 'select') {
            return true;
          }
          const selectedFilterValues = columnFilters[column.id] ?? [];
          if (selectedFilterValues.length === 0) {
            return true;
          }
          const normalizedColumnValue = normalizeSearch(getFilterTextByColumn(column, row));
          return selectedFilterValues.some(
            (filterValue) => normalizeSearch(filterValue) === normalizedColumnValue
          );
        });
      }),
    [columnFilters, columns, normalizedSearch, rows, visibleColumns]
  );

  const sortedRows = useMemo(() => {
    if (!sortState) {
      return filteredRows;
    }
    const sortColumn = visibleColumns.find((column) => column.id === sortState.columnId);
    if (!sortColumn) {
      return filteredRows;
    }
    const directionFactor = sortState.direction === 'asc' ? 1 : -1;
    return [...filteredRows].sort((leftRow, rightRow) => {
      const leftValue = getSortValueByColumn(sortColumn, leftRow);
      const rightValue = getSortValueByColumn(sortColumn, rightRow);
      return compareSortValues(leftValue, rightValue) * directionFactor;
    });
  }, [filteredRows, sortState, visibleColumns]);

  useEffect(() => {
    setPage(1);
  }, [columnFilters, normalizedSearch, rowsPerPage]);

  const effectiveRowsPerPage = rowsPerPage;
  const pageCount = Math.max(1, Math.ceil(sortedRows.length / effectiveRowsPerPage));

  useEffect(() => {
    if (page > pageCount) {
      setPage(pageCount);
    }
  }, [page, pageCount]);

  const visibleRows = useMemo(() => {
    const start = (page - 1) * effectiveRowsPerPage;
    return sortedRows.slice(start, start + effectiveRowsPerPage);
  }, [effectiveRowsPerPage, page, sortedRows]);
  const paginationItems = useMemo(() => getPaginationItems(page, pageCount), [page, pageCount]);
  const firstVisibleRow = sortedRows.length === 0 ? 0 : (page - 1) * effectiveRowsPerPage + 1;
  const lastVisibleRow = sortedRows.length === 0 ? 0 : Math.min(page * effectiveRowsPerPage, sortedRows.length);

  const hasActiveSelectFilters = Object.values(columnFilters).some((values) => values.length > 0);
  const showEmptySearchState = (normalizedSearch.length > 0 || hasActiveSelectFilters) && sortedRows.length === 0;

  const normalizedColumnWidths =
    columnWidths.length === visibleColumns.length
      ? columnWidths
      : resolveDefaultColumnWidths(visibleColumns, rows, minTableContentWidth);
  const autoStretchedColumnWidths = useMemo(() => {
    if (normalizedColumnWidths.length === 0) {
      return normalizedColumnWidths;
    }

    const baseTotalWidth = normalizedColumnWidths.reduce((sum, width) => sum + width, 0);
    const viewportContentWidth = Math.max(0, viewportWidth - rowPaddingTotal);
    const targetWidth = Math.max(minTableContentWidth, viewportContentWidth);
    if (baseTotalWidth >= targetWidth || baseTotalWidth <= 0) {
      return normalizedColumnWidths;
    }

    const extraWidth = targetWidth - baseTotalWidth;
    const stretchableIndexes = visibleColumns
      .map((column, index) => (isStretchableColumnWidth(column.width) ? index : -1))
      .filter((index) => index >= 0);
    if (stretchableIndexes.length === 0) {
      return normalizedColumnWidths;
    }

    const stretchableIndexSet = new Set(stretchableIndexes);
    const stretchableBaseTotal = stretchableIndexes.reduce((sum, index) => sum + normalizedColumnWidths[index], 0);
    if (stretchableBaseTotal <= 0) {
      return normalizedColumnWidths;
    }

    return normalizedColumnWidths.map((width, index) => {
      if (!stretchableIndexSet.has(index)) {
        return width;
      }
      const ratio = width / stretchableBaseTotal;
      return width + extraWidth * ratio;
    });
  }, [minTableContentWidth, normalizedColumnWidths, rowPaddingTotal, viewportWidth, visibleColumns]);
  const displayColumnWidths = hasManualColumnSizing ? normalizedColumnWidths : autoStretchedColumnWidths;
  const gridTemplateColumns = displayColumnWidths.map((width) => `${Math.round(width)}px`).join(' ');
  const tracksTotalWidth = displayColumnWidths.reduce((acc, width) => acc + width, 0);
  const gapsTotalWidth = Math.max(0, visibleColumns.length - 1) * gridColumnGap;
  const contentMinWidth = Math.max(minTableWidth, tracksTotalWidth + gapsTotalWidth + rowPaddingTotal);
  const effectiveHeaderHeight = headerHeight;

  const handleSearchChange = (event: ChangeEvent<HTMLInputElement>) => {
    const nextValue = event.target.value;
    setSearchValue(nextValue);
    onSearchChange?.(nextValue);
  };

  const rowsPerPageSelectValue = safeRowsPerPageOptions.includes(rowsPerPage)
      ? String(rowsPerPage)
      : 'custom';

  const handleRowsPerPageSelectChange = (event: { target: { value: unknown } }) => {
    const selectedValue = String(event.target.value);
    if (selectedValue === 'custom') {
      return;
    }

    const parsedValue = Number(selectedValue);
    if (Number.isFinite(parsedValue) && parsedValue > 0) {
      setRowsPerPage(parsedValue);
    }
  };

  const handleSortToggle = (columnId: string) => {
    setSortState((currentSortState) => {
      if (!currentSortState || currentSortState.columnId !== columnId) {
        return { columnId, direction: 'asc' };
      }
      if (currentSortState.direction === 'asc') {
        return { columnId, direction: 'desc' };
      }
      return null;
    });
  };

  const handleToggleColumnSelectFilterValue = (columnId: string, nextValue: string) => {
    setColumnFilters((currentFilters) => {
      const currentValues = currentFilters[columnId] ?? [];
      const hasValue = currentValues.includes(nextValue);
      const nextValues = hasValue
        ? currentValues.filter((value) => value !== nextValue)
        : [...currentValues, nextValue];
      if (nextValues.length === 0) {
        const { [columnId]: _, ...rest } = currentFilters;
        return rest;
      }
      return { ...currentFilters, [columnId]: nextValues };
    });
  };

  const handleSelectAllColumnSelectFilter = (
    columnId: string,
    options: TableTemplateFilterOption[]
  ) => {
    const nextValues = Array.from(new Set(options.map((option) => option.value)));
    if (nextValues.length === 0) {
      return;
    }
    setColumnFilters((currentFilters) => ({ ...currentFilters, [columnId]: nextValues }));
  };

  const handleResetColumnSelectFilter = (columnId: string) => {
    setColumnFilters((currentFilters) => {
      if (!currentFilters[columnId]) {
        return currentFilters;
      }
      const { [columnId]: _, ...rest } = currentFilters;
      return rest;
    });
  };

  const handleOpenSelectFilter = (columnId: string, event: ReactMouseEvent<HTMLButtonElement>) => {
    event.stopPropagation();
    setSelectFilterAnchor((currentAnchor) => {
      if (currentAnchor?.columnId === columnId) {
        return null;
      }
      return { columnId, anchorEl: event.currentTarget };
    });
  };

  const handleCloseSelectFilter = () => {
    setSelectFilterAnchor(null);
  };

  const handleSettingsButtonClick = (event: ReactMouseEvent<HTMLElement>) => {
    onSettingsClick?.();
    setSettingsAnchorEl((currentAnchorEl) => (currentAnchorEl ? null : event.currentTarget));
  };

  const handleCloseSettings = () => {
    setSettingsAnchorEl(null);
  };

  const handleToggleColumn = (columnId: string) => {
    setVisibleColumnIds((currentVisibleColumnIds) => {
      const isVisible = currentVisibleColumnIds.includes(columnId);
      if (isVisible) {
        if (currentVisibleColumnIds.length === 1) {
          return currentVisibleColumnIds;
        }
        return currentVisibleColumnIds.filter((id) => id !== columnId);
      }
      return allColumnIds.filter((id) => id === columnId || currentVisibleColumnIds.includes(id));
    });
    setHasManualColumnSizing(false);
  };

  const handleShowAllColumns = () => {
    setVisibleColumnIds(allColumnIds);
    setHasManualColumnSizing(false);
  };

  const handleResetDefaultSettings = () => {
    setVisibleColumnIds(allColumnIds);
    setHasManualColumnSizing(false);
    setColumnFilters({});
    setSortState(null);
    setColumnWidths(resolveDefaultColumnWidths(columns, rows, getMinTableContentWidth(columns)));
  };

  const handleResizeStart = (index: number, event: ReactMouseEvent<HTMLElement>) => {
    if (!resizableColumns || index >= visibleColumns.length - 1) {
      return;
    }
    event.preventDefault();
    event.stopPropagation();

    const baseWidths = hasManualColumnSizing ? normalizedColumnWidths : autoStretchedColumnWidths;
    if (!hasManualColumnSizing) {
      setColumnWidths(baseWidths);
      setHasManualColumnSizing(true);
    }

    resizeStateRef.current = {
      index,
      startX: event.clientX,
      initialWidths: [...baseWidths]
    };
    setIsResizingColumn(true);
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';
  };

  const activeSelectFilterColumn = useMemo(() => {
    if (!selectFilterAnchor) {
      return null;
    }
    const column = visibleColumns.find((item) => item.id === selectFilterAnchor.columnId);
    if (!column || column.filterKind !== 'select') {
      return null;
    }
    return column;
  }, [selectFilterAnchor, visibleColumns]);
  const isCardsView = viewMode === 'cards';
  const viewToggleButtonRadius = Math.max(8, controlRadius - 4);
  const canToggleViewMode = showViewToggle;
  const showCardExpansionToggle = isCardsView && Boolean(cardExpansionControl);
  const shouldUseIconOnlyViewToggle = isMobileViewport || viewportWidth < 560;
  const shouldUseIconOnlyAddButton = isMobileViewport || viewportWidth < 500;
  const estimatedAddButtonWidth = showAddAction && onAddClick ? (shouldUseIconOnlyAddButton ? searchHeight : 132) : 0;
  const estimatedSettingsButtonWidth = showSettingsAction ? searchHeight : 0;
  const estimatedViewToggleWidth = canToggleViewMode ? (shouldUseIconOnlyViewToggle ? 96 : 206) : 0;
  const estimatedSwitchWidth = showCardExpansionToggle ? 38 : 0;
  const estimatedExpandLabelWidth = showCardExpansionToggle ? 126 : 0;
  const estimatedToolbarGaps = 16;
  const estimatedRequiredToolbarWidthWithLabel =
    estimatedAddButtonWidth +
    estimatedSettingsButtonWidth +
    estimatedViewToggleWidth +
    estimatedSwitchWidth +
    estimatedExpandLabelWidth +
    estimatedToolbarGaps;
  const shouldHideExpandAllLabel = showCardExpansionToggle && viewportWidth < estimatedRequiredToolbarWidthWithLabel;
  const shouldHideRowsCountLabel = isMobileViewport || viewportWidth < 410;

  const handleViewModeChange = (nextMode: DataViewMode) => {
    hasUserToggledViewMode.current = true;
    setViewMode(nextMode);
  };

  const toolbarSearch = showSearch ? (
    <Paper
      sx={{
        width: { xs: '100%', md: searchWidth },
        minHeight: searchHeight,
        borderRadius: `${controlRadius}px`,
        border: '1px solid',
        borderColor: 'divider',
        bgcolor: 'background.paper',
        px: 2,
        py: 0.5,
        display: 'flex',
        alignItems: 'center',
        gap: 1
      }}
    >
      <InputBase
        value={searchValue}
        onChange={handleSearchChange}
        placeholder={searchPlaceholder}
        inputProps={{ 'aria-label': 'Поиск по таблице' }}
        sx={{
          flex: 1,
          fontSize,
          color: 'text.primary',
          '& input::placeholder': {
            color: 'text.secondary',
            opacity: 1
          }
        }}
      />
      <SearchRounded sx={{ color: 'text.secondary', fontSize: iconSize }} />
    </Paper>
  ) : null;

  const toolbarActions = (
    <Stack
      direction="row"
      spacing={1}
      alignItems="center"
      flexWrap="nowrap"
      sx={{
        width: { xs: '100%', md: 'auto' },
        justifyContent: isMobileViewport ? 'space-between' : 'flex-end'
      }}
    >
      {showAddAction && onAddClick ? (
        <ActionButton
          kind="filled"
          showNavigationIcons={false}
          startIcon={<AddRounded />}
          aria-label={addButtonLabel}
          onClick={onAddClick}
          sx={{
            minHeight: searchHeight,
            px: shouldUseIconOnlyAddButton ? 0 : 2.5,
            width: shouldUseIconOnlyAddButton ? searchHeight : 'auto',
            minWidth: shouldUseIconOnlyAddButton ? searchHeight : undefined,
            borderRadius: `${controlRadius}px`,
            fontSize
          }}
        >
          {shouldUseIconOnlyAddButton ? null : addButtonLabel}
        </ActionButton>
      ) : null}

      {canToggleViewMode || showCardExpansionToggle ? (
        <Paper
          sx={{
            display: 'flex',
            alignItems: 'center',
            p: 0.5,
            flex: isMobileViewport ? 1 : 'initial',
            borderRadius: `${controlRadius}px`,
            border: '1px solid',
            borderColor: 'divider',
            bgcolor: 'background.paper'
          }}
        >
          {canToggleViewMode ? (
            <>
              <ActionButton
                kind="custom"
                selected={viewMode === 'table'}
                showNavigationIcons={false}
                aria-label="Режим таблицы"
                onClick={() => handleViewModeChange('table')}
                sx={{
                  minHeight: searchHeight - 8,
                  minWidth: 0,
                  px: { xs: 1.25, sm: 1.6 },
                  borderTopLeftRadius: `${viewToggleButtonRadius}px`,
                  borderBottomLeftRadius: `${viewToggleButtonRadius}px`,
                  borderTopRightRadius: 0,
                  borderBottomRightRadius: 0,
                  transition: 'background-color 0.2s ease, color 0.2s ease'
                }}
              >
                <Stack direction="row" alignItems="center" gap={0.75}>
                  <TableRowsRounded sx={{ fontSize: 18 }} />
                  <Typography
                    sx={{ display: shouldUseIconOnlyViewToggle ? 'none' : 'block', fontSize: fontSize - 1, fontWeight: 600 }}
                  >
                    Таблица
                  </Typography>
                </Stack>
              </ActionButton>
              <ActionButton
                kind="custom"
                selected={viewMode === 'cards'}
                showNavigationIcons={false}
                aria-label="Режим карточек"
                onClick={() => handleViewModeChange('cards')}
                sx={{
                  minHeight: searchHeight - 8,
                  minWidth: 0,
                  px: { xs: 1.25, sm: 1.6 },
                  borderTopRightRadius: `${viewToggleButtonRadius}px`,
                  borderBottomRightRadius: `${viewToggleButtonRadius}px`,
                  borderTopLeftRadius: 0,
                  borderBottomLeftRadius: 0,
                  transition: 'background-color 0.2s ease, color 0.2s ease'
                }}
              >
                <Stack direction="row" alignItems="center" gap={0.75}>
                  <WindowRounded sx={{ fontSize: 18 }} />
                  <Typography
                    sx={{ display: shouldUseIconOnlyViewToggle ? 'none' : 'block', fontSize: fontSize - 1, fontWeight: 600 }}
                  >
                    Карточки
                  </Typography>
                </Stack>
              </ActionButton>
            </>
          ) : null}

          {showCardExpansionToggle && cardExpansionControl ? (
            <Stack
              direction="row"
              alignItems="center"
              sx={{
                ml: canToggleViewMode ? 0.5 : 0,
                pl: canToggleViewMode ? 1 : 0,
                pr: 1,
                borderLeft: canToggleViewMode ? '1px solid' : 'none',
                borderColor: 'divider'
              }}
            >
              <Switch
                size="small"
                checked={cardExpansionControl.checked}
                onChange={(event) => cardExpansionControl.onChange(event.target.checked)}
                inputProps={{ 'aria-label': 'Раскрыть или свернуть все карточки' }}
              />
              <Typography
                sx={{
                  display: shouldHideExpandAllLabel ? 'none' : 'block',
                  fontSize: fontSize - 2,
                  color: 'text.secondary',
                  whiteSpace: 'nowrap'
                }}
              >
                Развернуть
              </Typography>
            </Stack>
          ) : null}
        </Paper>
      ) : null}

      {showSettingsAction ? (
        <ActionButton
          kind="outlined"
          showNavigationIcons={false}
          onClick={handleSettingsButtonClick}
          sx={{
            minHeight: searchHeight,
            width: searchHeight,
            minWidth: searchHeight,
            px: 0,
            borderRadius: `${controlRadius}px`,
            borderColor: 'divider',
            color: 'text.secondary'
          }}
        >
          <SettingsOutlined sx={{ fontSize: iconSize }} />
        </ActionButton>
      ) : null}
    </Stack>
  );

  return (
    <Paper
      sx={{
        borderRadius: `${theme.acomShape.panelRadius}px`,
        border: '1px solid',
        borderColor: 'divider',
        bgcolor: 'brand.softSection',
        p: `${theme.acomShape.panelPadding}px`
      }}
    >
      <Stack spacing={1.25}>
        {isMobileViewport ? (
          <Stack spacing={1}>
            {toolbarActions}
            {toolbarSearch}
          </Stack>
        ) : (
          <Stack
            direction="row"
            gap={`${toolbarGap}px`}
            justifyContent="space-between"
            alignItems="center"
            flexWrap="wrap"
          >
            {toolbarSearch}
            {toolbarActions}
          </Stack>
        )}

        <Popover
          open={Boolean(settingsAnchorEl)}
          anchorEl={settingsAnchorEl}
          onClose={handleCloseSettings}
          anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
          transformOrigin={{ vertical: 'top', horizontal: 'right' }}
        >
          <Stack sx={{ width: 320, p: 2, gap: 1.25 }}>
            <Typography sx={{ fontWeight: 600, color: 'text.primary', fontSize }}>
              Настройки таблицы
            </Typography>
            <FormGroup
              sx={{
                maxHeight: 240,
                overflowY: 'auto',
                overflowX: 'hidden',
                flexWrap: 'nowrap',
                alignItems: 'stretch'
              }}
            >
              {columns.map((column) => {
                const isChecked = visibleColumnIds.includes(column.id);
                const isOnlyVisibleColumn = isChecked && visibleColumnIds.length === 1;
                return (
                  <FormControlLabel
                    key={column.id}
                    control={
                      <Checkbox
                        size="small"
                        checked={isChecked}
                        onChange={() => handleToggleColumn(column.id)}
                        disabled={isOnlyVisibleColumn}
                      />
                    }
                    label={column.header}
                    sx={{
                      width: '100%',
                      m: 0,
                      '& .MuiFormControlLabel-label': {
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap'
                      }
                    }}
                  />
                );
              })}
            </FormGroup>
            <Divider />
            <Stack direction="column" alignItems="stretch" gap={0.25}>
              <Button variant="text" size="small" onClick={handleShowAllColumns} sx={{ justifyContent: 'flex-start' }}>
                Показать все
              </Button>
              <Button
                variant="text"
                size="small"
                onClick={handleResetDefaultSettings}
                sx={{ justifyContent: 'flex-start' }}
              >
                По умолчанию
              </Button>
            </Stack>
          </Stack>
        </Popover>

        <Popover
          open={Boolean(selectFilterAnchor && activeSelectFilterColumn)}
          anchorEl={selectFilterAnchor?.anchorEl}
          onClose={handleCloseSelectFilter}
          anchorOrigin={{ vertical: 'bottom', horizontal: 'left' }}
          transformOrigin={{ vertical: 'top', horizontal: 'left' }}
        >
          <Stack sx={{ minWidth: 220, p: 1, gap: 1 }}>
            <Typography
              sx={{
                fontSize: fontSize - 1,
                fontWeight: 600,
                color: 'text.secondary',
                textTransform: 'uppercase'
              }}
            >
              {activeSelectFilterColumn?.header}
            </Typography>
            <Stack direction="column" gap={0.25}>
              {(activeSelectFilterColumn?.filterOptions ?? []).map((option) => {
                const isSelected = (columnFilters[activeSelectFilterColumn?.id ?? ''] ?? []).includes(
                  option.value
                );
                return (
                  <FormControlLabel
                    key={`${activeSelectFilterColumn?.id}-${option.value}`}
                    control={
                      <Checkbox
                        size="small"
                        checked={isSelected}
                        onChange={() => {
                          if (!activeSelectFilterColumn) {
                            return;
                          }
                          handleToggleColumnSelectFilterValue(activeSelectFilterColumn.id, option.value);
                        }}
                      />
                    }
                    label={option.label}
                    sx={{ width: '100%', m: 0 }}
                  />
                );
              })}
            </Stack>
            <Divider />
            <Stack direction="column" alignItems="stretch" gap={0.25}>
              <Button
                variant="text"
                size="small"
                onClick={() => {
                  if (!activeSelectFilterColumn) {
                    return;
                  }
                  handleSelectAllColumnSelectFilter(
                    activeSelectFilterColumn.id,
                    activeSelectFilterColumn.filterOptions ?? []
                  );
                }}
                sx={{ justifyContent: 'flex-start' }}
              >
                Выбрать все
              </Button>
              <Button
                variant="text"
                size="small"
                onClick={() => {
                  if (!activeSelectFilterColumn) {
                    return;
                  }
                  handleResetColumnSelectFilter(activeSelectFilterColumn.id);
                }}
                disabled={!activeSelectFilterColumn || (columnFilters[activeSelectFilterColumn.id] ?? []).length === 0}
                sx={{ justifyContent: 'flex-start' }}
              >
                Сбросить
              </Button>
            </Stack>
          </Stack>
        </Popover>

        {statusContent ? (
          <Paper
            sx={{
              borderRadius: `${theme.acomShape.controlRadius}px`,
              border: '1px solid',
              borderColor: 'divider',
              p: 1.5,
              bgcolor: 'background.paper'
            }}
          >
            {statusContent}
          </Paper>
        ) : null}

        <Stack ref={viewportRef} sx={{ overflowX: isCardsView ? 'visible' : 'auto' }}>
          {!isCardsView ? (
            <Stack sx={{ minWidth: `${contentMinWidth}px`, gap: rowGap }}>
              <Stack
                sx={{
                  display: 'grid',
                  gridTemplateColumns,
                  alignItems: 'center',
                  columnGap: `${gridColumnGap}px`,
                  px: rowPaddingX,
                  minHeight: effectiveHeaderHeight,
                  borderRadius: `${theme.acomShape.controlRadius}px`,
                  bgcolor: alpha(theme.palette.primary.main, 0.14)
                }}
              >
                {visibleColumns.map((column, index) => (
                  <Stack
                    key={column.id}
                    sx={{
                      position: 'relative',
                      minWidth: 0,
                      height: '100%',
                      px: cellPaddingX,
                      justifyContent: 'center',
                      gap: 0.5
                    }}
                  >
                    <Stack direction="row" alignItems="center" gap={0.5} sx={{ width: '100%', minWidth: 0 }}>
                      <Typography
                        sx={{
                          minWidth: 0,
                          flex: 1,
                          fontSize: fontSize - 1,
                          fontWeight: 600,
                          color: 'text.secondary',
                          textTransform: 'uppercase',
                          textAlign: column.align ?? 'left',
                          whiteSpace: 'normal',
                          lineHeight: 1.2,
                          pr: resizableColumns && index < visibleColumns.length - 1 ? 1 : 0
                        }}
                      >
                        {column.header}
                      </Typography>
                      <Stack direction="row" alignItems="center" sx={{ flexShrink: 0 }}>
                        {column.filterKind !== 'select' && column.sortable !== false ? (
                          <ButtonBase
                            onClick={(event: ReactMouseEvent<HTMLButtonElement>) => {
                              event.stopPropagation();
                              handleSortToggle(column.id);
                            }}
                            sx={{
                              width: 18,
                              height: 18,
                              borderRadius: '4px',
                              color: sortState?.columnId === column.id ? 'primary.main' : 'text.secondary',
                              flexShrink: 0
                            }}
                          >
                            {sortState?.columnId === column.id ? (
                              sortState.direction === 'asc' ? (
                                <ArrowUpwardRounded sx={{ fontSize: 14 }} />
                              ) : (
                                <ArrowDownwardRounded sx={{ fontSize: 14 }} />
                              )
                            ) : (
                              <UnfoldMoreRounded sx={{ fontSize: 14 }} />
                            )}
                          </ButtonBase>
                        ) : null}
                        {column.filterKind === 'select' ? (
                          <ButtonBase
                            onClick={(event: ReactMouseEvent<HTMLButtonElement>) =>
                              handleOpenSelectFilter(column.id, event)
                            }
                            sx={{
                              width: 18,
                              height: 18,
                              borderRadius: '4px',
                              color:
                                (columnFilters[column.id] ?? []).length > 0 ||
                                  selectFilterAnchor?.columnId === column.id
                                  ? 'primary.main'
                                  : 'text.secondary',
                              flexShrink: 0
                            }}
                          >
                            <FilterAltRounded sx={{ fontSize: 14 }} />
                          </ButtonBase>
                        ) : null}
                      </Stack>
                    </Stack>
                    {resizableColumns && index < visibleColumns.length - 1 ? (
                      <Stack
                        onMouseDown={(event) => handleResizeStart(index, event)}
                        sx={{
                          position: 'absolute',
                          top: 0,
                          right: -5,
                          width: 10,
                          height: '100%',
                          cursor: 'col-resize',
                          zIndex: 2,
                          '&:hover::before': {
                            opacity: 1
                          },
                          '&::before': {
                            content: '""',
                            position: 'absolute',
                            top: 8,
                            bottom: 8,
                            left: '50%',
                            transform: 'translateX(-50%)',
                            width: 2,
                            borderRadius: 999,
                            backgroundColor: 'primary.main',
                            opacity: 0
                          }
                        }}
                      />
                    ) : null}
                  </Stack>
                ))}
              </Stack>

              {sortedRows.length > 0 ? (
                visibleRows.map((row, rowIndex) => {
                  const rowKey = String(getRowId ? getRowId(row, rowIndex) : rowIndex);
                  return (
                    <Stack
                      key={rowKey}
                      onClick={onRowClick ? () => onRowClick(row) : undefined}
                      sx={{
                        display: 'grid',
                        gridTemplateColumns,
                        alignItems: 'stretch',
                        columnGap: `${gridColumnGap}px`,
                        px: rowPaddingX,
                        minHeight: rowHeight,
                        borderRadius: `${theme.acomShape.controlRadius}px`,
                        bgcolor: 'background.paper',
                        border: '1px solid',
                        borderColor: 'divider',
                        transition: 'border-color 0.18s ease, box-shadow 0.18s ease',
                        cursor: onRowClick ? 'pointer' : 'default',
                        '&:hover': {
                          borderColor: 'primary.main',
                          boxShadow: `0 6px 16px ${alpha(theme.palette.primary.main, 0.16)}`
                        }
                      }}
                    >
                      {visibleColumns.map((column) => {
                        const rawValue = column.field ? row[column.field] : undefined;
                        const rendered = column.renderCell
                          ? column.renderCell(row)
                          : column.renderValue
                            ? column.renderValue(rawValue, row)
                            : valueToDisplay(rawValue);

                        return (
                          <Stack
                            key={`${rowKey}-${column.id}`}
                            direction="row"
                            alignItems="center"
                            justifyContent={alignToFlex(column.align)}
                            sx={{
                              minWidth: 0,
                              px: cellPaddingX,
                              py: 0.8,
                              overflow: 'hidden'
                            }}
                          >
                            <Stack
                              sx={{
                                minWidth: 0,
                                width: '100%',
                                overflow: 'hidden',
                                '& > *': {
                                  minWidth: 0
                                },
                                '& .MuiTypography-root': {
                                  overflow: 'hidden',
                                  textOverflow: 'ellipsis',
                                  whiteSpace: 'nowrap'
                                }
                              }}
                            >
                              {rendered}
                            </Stack>
                          </Stack>
                        );
                      })}
                    </Stack>
                  );
                })
              ) : (
                <Stack
                  sx={{
                    minHeight: rowHeight * 2,
                    alignItems: 'center',
                    justifyContent: 'center',
                    borderRadius: `${theme.acomShape.controlRadius}px`,
                    border: '1px dashed',
                    borderColor: 'divider',
                    bgcolor: 'background.paper'
                  }}
                >
                  <Typography sx={{ fontSize, color: 'text.secondary' }}>
                    {isLoading ? 'Загрузка...' : showEmptySearchState ? noSearchResultsLabel : noRowsLabel}
                  </Typography>
                </Stack>
              )}
            </Stack>
          ) : (
            <Stack
              sx={{
                display: 'grid',
                gridTemplateColumns: {
                  xs: '1fr',
                  md: 'repeat(2, minmax(0, 1fr))',
                  lg: 'repeat(3, minmax(0, 1fr))',
                  xl: 'repeat(4, minmax(0, 1fr))'
                },
                gap: 1.25
              }}
            >
              {visibleRows.length > 0 &&
                visibleRows.map((row, rowIndex) => {
                  const rowKey = String(getRowId ? getRowId(row, rowIndex) : rowIndex);

                  if (renderCard) {
                    return (
                      <Stack key={rowKey} sx={{ minWidth: 0 }}>
                        {renderCard(row, rowIndex)}
                      </Stack>
                    );
                  }

                  const nameColumn =
                    visibleColumns.find((column) => {
                      const signature = getColumnSignature(column);
                      const id = column.id.toLocaleLowerCase();
                      return id.includes('fullname') || signature.includes('full') || signature.includes('name');
                    }) ?? visibleColumns[0];
                  const identityColumn = visibleColumns.find((column) => {
                    if (column.id === nameColumn?.id) {
                      return false;
                    }

                    const signature = getColumnSignature(column);
                    const id = column.id.toLocaleLowerCase();
                    return id.includes('login') || signature.includes('login') || signature.includes('id');
                  });
                  const statusColumn = visibleColumns.find((column) => column.filterKind === 'select');
                  const cardDetailColumns = visibleColumns.filter((column) => {
                    return column.id !== nameColumn?.id && column.id !== identityColumn?.id && column.id !== statusColumn?.id;
                  });
                  const normalizedExcludedColumnIds = new Set(cardExcludedColumnIds);
                  const visibleCardDetailColumns = cardDetailColumns.filter((column) => !normalizedExcludedColumnIds.has(column.id));
                  const personalContactColumns = visibleCardDetailColumns.filter((column) => {
                    const signature = getColumnSignature(column);
                    const id = column.id.toLocaleLowerCase();
                    const isContact = id.includes('phone') || id.includes('email') || signature.includes('phone') || signature.includes('email');
                    const isCompany = id.includes('company') || signature.includes('company');
                    return isContact && !isCompany;
                  });
                  const companyContactColumns = visibleCardDetailColumns.filter((column) => {
                    const signature = getColumnSignature(column);
                    const id = column.id.toLocaleLowerCase();
                    const isContact = id.includes('phone') || id.includes('email') || signature.includes('phone') || signature.includes('email');
                    const isCompany = id.includes('company') || signature.includes('company');
                    return isContact && isCompany;
                  });
                  const extraColumns = visibleCardDetailColumns.filter(
                    (column) => !personalContactColumns.includes(column) && !companyContactColumns.includes(column)
                  );
                  const cardPrimaryText = getCardPrimaryText?.(row);
                  const cardSecondaryText = getCardSecondaryText?.(row);

                  return (
                    <Paper
                      key={rowKey}
                      onClick={onRowClick ? () => onRowClick(row) : undefined}
                      sx={{
                        p: { xs: 1.25, sm: 1.5 },
                        borderRadius: `${theme.acomShape.controlRadius}px`,
                        bgcolor: 'background.paper',
                        border: '1px solid',
                        borderColor: 'divider',
                        boxShadow: `0 2px 8px ${alpha(theme.palette.common.black, 0.04)}`,
                        transition: 'border-color 0.2s ease, box-shadow 0.2s ease',
                        cursor: onRowClick ? 'pointer' : 'default',
                        '&:hover': {
                          borderColor: 'primary.main',
                          boxShadow: `0 6px 14px ${alpha(theme.palette.common.black, 0.08)}`
                        }
                      }}
                    >
                      {(nameColumn || statusColumn) && (
                        <Stack direction="row" justifyContent="space-between" alignItems="flex-start" gap={1.25} mb={1.25}>
                          {nameColumn && (
                            <Stack sx={{ minWidth: 0, gap: 0.25 }}>
                              <Typography
                                sx={{
                                  minWidth: 0,
                                  fontSize: fontSize + 1,
                                  fontWeight: 600,
                                  color: 'text.primary',
                                  overflow: 'hidden',
                                  textOverflow: 'ellipsis',
                                  whiteSpace: 'nowrap'
                                }}
                              >
                                {cardPrimaryText ??
                                  `${valueToDisplay(nameColumn.field ? row[nameColumn.field] : getSearchTextByColumn(nameColumn, row))}${identityColumn
                                    ? ` (${valueToDisplay(
                                      identityColumn.field ? row[identityColumn.field] : getSearchTextByColumn(identityColumn, row)
                                    )})`
                                    : ''
                                  }`}
                              </Typography>
                              {cardSecondaryText && (
                                <Typography
                                  sx={{
                                    minWidth: 0,
                                    fontSize: fontSize - 2,
                                    fontWeight: 400,
                                    color: 'text.secondary',
                                    overflow: 'hidden',
                                    textOverflow: 'ellipsis',
                                    whiteSpace: 'nowrap'
                                  }}
                                >
                                  {cardSecondaryText}
                                </Typography>
                              )}
                            </Stack>
                          )}

                          {statusColumn && (
                            <Stack sx={{ alignItems: 'flex-start', flexShrink: 0 }}>
                              {statusColumn.renderCell ? (
                                statusColumn.renderCell(row)
                              ) : statusColumn.renderValue ? (
                                statusColumn.renderValue(statusColumn.field ? row[statusColumn.field] : undefined, row)
                              ) : (
                                <Typography component="span" sx={{ fontSize, color: 'text.primary' }}>
                                  {valueToDisplay(statusColumn.field ? row[statusColumn.field] : undefined)}
                                </Typography>
                              )}
                            </Stack>
                          )}
                        </Stack>
                      )}
                      <Divider sx={{ mb: 1.1 }} />

                      <Stack sx={{ px: 0.25 }}>
                        {extraColumns.length > 0 && (
                          <Stack divider={<Divider flexItem />}>
                            {extraColumns.map((column) => (
                              <Stack
                                key={`${rowKey}-extra-${column.id}`}
                                sx={{
                                  minWidth: 0,
                                  py: 0.9
                                }}
                              >
                                <Stack direction="row" alignItems="flex-start" gap={1.1} sx={{ minWidth: 0 }}>
                                  <Typography
                                    sx={{
                                      minWidth: 0,
                                      flex: '0 0 44%',
                                      fontSize: fontSize - 4,
                                      fontWeight: 600,
                                      color: 'text.secondary',
                                      textTransform: 'uppercase',
                                      overflow: 'hidden',
                                      textOverflow: 'ellipsis',
                                      whiteSpace: 'nowrap'
                                    }}
                                  >
                                    {column.header}
                                  </Typography>
                                  <Stack sx={{ minWidth: 0, flex: 1, alignItems: 'flex-start' }}>
                                    {column.renderCell ? (
                                      <Stack sx={{ minWidth: 0 }}>{column.renderCell(row)}</Stack>
                                    ) : column.renderValue ? (
                                      <Stack sx={{ minWidth: 0 }}>{column.renderValue(column.field ? row[column.field] : undefined, row)}</Stack>
                                    ) : (
                                      <Typography
                                        component="span"
                                        sx={{
                                          fontSize,
                                          color: 'text.primary',
                                          whiteSpace: 'normal',
                                          wordBreak: 'break-word'
                                        }}
                                      >
                                        {valueToDisplay(column.field ? row[column.field] : undefined)}
                                      </Typography>
                                    )}
                                  </Stack>
                                </Stack>
                              </Stack>
                            ))}
                          </Stack>
                        )}

                        {personalContactColumns.length > 0 && (
                          <Stack>
                            <Typography
                              sx={{
                                mb: 0.65,
                                fontSize: fontSize - 4,
                                fontWeight: 700,
                                color: 'primary.main',
                                textTransform: 'uppercase',
                                letterSpacing: 0.3
                              }}
                            >
                              {'Для связи'}
                            </Typography>
                            <Stack divider={<Divider flexItem />}>
                              {personalContactColumns.map((column) => (
                                <Stack key={`${rowKey}-personal-${column.id}`} sx={{ minWidth: 0, py: 0.85 }}>
                                  <Stack direction="row" alignItems="flex-start" gap={1.1} sx={{ minWidth: 0 }}>
                                    <Typography
                                      sx={{
                                        minWidth: 0,
                                        flex: '0 0 44%',
                                        fontSize: fontSize - 4,
                                        fontWeight: 600,
                                        color: 'text.secondary',
                                        textTransform: 'uppercase',
                                        overflow: 'hidden',
                                        textOverflow: 'ellipsis',
                                        whiteSpace: 'nowrap'
                                      }}
                                    >
                                      {getContactFieldLabel(column)}
                                    </Typography>
                                    <Stack sx={{ minWidth: 0, flex: 1, alignItems: 'flex-start' }}>
                                      {column.renderCell ? (
                                        <Stack sx={{ minWidth: 0 }}>{column.renderCell(row)}</Stack>
                                      ) : column.renderValue ? (
                                        <Stack sx={{ minWidth: 0 }}>{column.renderValue(column.field ? row[column.field] : undefined, row)}</Stack>
                                      ) : (
                                        <Typography component="span" sx={{ fontSize, color: 'text.primary', wordBreak: 'break-word' }}>
                                          {valueToDisplay(column.field ? row[column.field] : undefined)}
                                        </Typography>
                                      )}
                                    </Stack>
                                  </Stack>
                                </Stack>
                              ))}
                            </Stack>
                          </Stack>
                        )}

                        {companyContactColumns.length > 0 && (
                          <Stack sx={{ mt: personalContactColumns.length > 0 ? 0.8 : 0 }}>
                            <Typography
                              sx={{
                                mb: 0.65,
                                fontSize: fontSize - 4,
                                fontWeight: 700,
                                color: 'primary.main',
                                textTransform: 'uppercase',
                                letterSpacing: 0.3
                              }}
                            >
                              {'Компания'}
                            </Typography>
                            <Stack divider={<Divider flexItem />}>
                              {companyContactColumns.map((column) => (
                                <Stack key={`${rowKey}-company-${column.id}`} sx={{ minWidth: 0, py: 0.85 }}>
                                  <Stack direction="row" alignItems="flex-start" gap={1.1} sx={{ minWidth: 0 }}>
                                    <Typography
                                      sx={{
                                        minWidth: 0,
                                        flex: '0 0 44%',
                                        fontSize: fontSize - 4,
                                        fontWeight: 600,
                                        color: 'text.secondary',
                                        textTransform: 'uppercase',
                                        overflow: 'hidden',
                                        textOverflow: 'ellipsis',
                                        whiteSpace: 'nowrap'
                                      }}
                                    >
                                      {getContactFieldLabel(column)}
                                    </Typography>
                                    <Stack sx={{ minWidth: 0, flex: 1, alignItems: 'flex-start' }}>
                                      {column.renderCell ? (
                                        <Stack sx={{ minWidth: 0 }}>{column.renderCell(row)}</Stack>
                                      ) : column.renderValue ? (
                                        <Stack sx={{ minWidth: 0 }}>{column.renderValue(column.field ? row[column.field] : undefined, row)}</Stack>
                                      ) : (
                                        <Typography component="span" sx={{ fontSize, color: 'text.primary', wordBreak: 'break-word' }}>
                                          {valueToDisplay(column.field ? row[column.field] : undefined)}
                                        </Typography>
                                      )}
                                    </Stack>
                                  </Stack>
                                </Stack>
                              ))}
                            </Stack>
                          </Stack>
                        )}
                      </Stack>
                    </Paper>
                  );
                })}
            </Stack>
          )}

          {isCardsView && visibleRows.length === 0 && (
            <Paper
              sx={{
                minHeight: rowHeight * 1.1,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                borderRadius: `${theme.acomShape.controlRadius}px`,
                bgcolor: 'background.paper'
              }}
            >
              <Typography sx={{ fontSize, color: 'text.secondary' }}>
                {isLoading ? 'Загрузка...' : showEmptySearchState ? noSearchResultsLabel : noRowsLabel}
              </Typography>
            </Paper>
          )}
        </Stack>

        <Divider />

        <Stack
          direction="row"
          sx={{
            minHeight: footerHeight,
            display: 'flex',
            flexWrap: 'nowrap',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: 1.25
          }}
        >
          <Typography
            sx={{
              fontSize,
              color: 'text.secondary',
              display: { xs: 'none', md: 'block' },
              whiteSpace: 'nowrap',
              flexShrink: 0
            }}
          >
            {`Показаны строки ${firstVisibleRow}-${lastVisibleRow} из ${sortedRows.length}`}
          </Typography>

          <Stack direction="row" spacing={1} alignItems="center" sx={{ justifySelf: { md: 'center' } }}>
            <ActionButton
              kind="outlined"
              showNavigationIcons={false}
              disabled={page <= 1}
              onClick={() => setPage((currentPage) => Math.max(1, currentPage - 1))}
              sx={{
                minHeight: pagerButtonSize,
                width: pagerButtonSize,
                minWidth: pagerButtonSize,
                px: 0,
                borderRadius: `${controlRadius}px`,
                borderColor: 'divider',
                color: 'text.secondary'
              }}
            >
              <NavigateBeforeRounded />
            </ActionButton>
            {paginationItems.map((item) =>
              typeof item === 'number' ? (
                <ActionButton
                  key={item}
                  kind={item === page ? 'filled' : 'outlined'}
                  showNavigationIcons={false}
                  onClick={() => setPage(item)}
                  disabled={filteredRows.length === 0}
                  sx={{
                    minHeight: pagerButtonSize,
                    width: pagerButtonSize,
                    minWidth: pagerButtonSize,
                    px: 0,
                    borderRadius: `${controlRadius}px`,
                    fontSize,
                    borderColor: item === page ? undefined : 'divider',
                    color: item === page ? undefined : 'text.secondary'
                  }}
                >
                  {item}
                </ActionButton>
              ) : (
                <Stack key={item} sx={{ minWidth: pagerButtonSize, alignItems: 'center', justifyContent: 'center' }}>
                  <Typography sx={{ color: 'text.secondary', fontSize }}>...</Typography>
                </Stack>
              )
            )}
            <ActionButton
              kind="outlined"
              showNavigationIcons={false}
              disabled={page >= pageCount}
              onClick={() => setPage((currentPage) => Math.min(pageCount, currentPage + 1))}
              sx={{
                minHeight: pagerButtonSize,
                width: pagerButtonSize,
                minWidth: pagerButtonSize,
                px: 0,
                borderRadius: `${controlRadius}px`,
                borderColor: 'divider',
                color: 'text.secondary'
              }}
            >
              <NavigateNextRounded />
            </ActionButton>
          </Stack>

          <Stack
            direction="row"
            spacing={0.75}
            alignItems="center"
            sx={{
              color: 'text.secondary',
              flexShrink: 0,
              minHeight: pagerButtonSize
            }}
          >
            <Select
              value={rowsPerPageSelectValue}
              onChange={(event) => handleRowsPerPageSelectChange(event as { target: { value: unknown } })}
              IconComponent={KeyboardArrowDownRounded}
              sx={{
                width: rowsPerPageWidth,
                minHeight: pagerButtonSize,
                borderRadius: `${controlRadius}px`,
                bgcolor: 'background.paper',
                color: 'text.secondary',
                '& .MuiSelect-select': {
                  py: 0.75
                },
                '& .MuiOutlinedInput-notchedOutline': {
                  borderColor: 'divider'
                }
              }}
            >
              {safeRowsPerPageOptions.map((option) => (
                <MenuItem key={option} value={String(option)}>
                  {option}
                </MenuItem>
              ))}
              <MenuItem value="custom" disabled>
                Свое
              </MenuItem>
            </Select>
            <Typography sx={{ display: shouldHideRowsCountLabel ? 'none' : 'block', fontSize, color: 'text.secondary' }}>
              строк
            </Typography>
          </Stack>
        </Stack>
      </Stack>
    </Paper>
  );
}
