import { ReactNode, useMemo } from "react";
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import { useTheme } from "@mui/material/styles";
import { TableTemplate, type TableTemplateColumn } from "./TableTemplate";

function alignToFlex(align: "left" | "center" | "right" | undefined) {
  if (align === "center") {
    return "center";
  }

  if (align === "right") {
    return "flex-end";
  }

  return "flex-start";
}

function valueToText(value: unknown): string {
  if (value === null || value === undefined) {
    return "";
  }

  if (typeof value === "string" || typeof value === "number" || typeof value === "boolean" || typeof value === "bigint") {
    return String(value);
  }

  if (value instanceof Date) {
    return value.toISOString();
  }

  if (Array.isArray(value)) {
    return value.map(valueToText).join(" ");
  }

  if (typeof value === "object") {
    return Object.values(value as Record<string, unknown>).map(valueToText).join(" ");
  }

  return "";
}

export type DataTableColumn = {
  key: string;
  label: ReactNode;
  align?: "left" | "center" | "right";
  width?: number;
  minWidth?: number;
  fraction?: number;
};

type LegacyDataViewMode = "table" | "cards";

type DataTableProps<T> = {
  columns: DataTableColumn[];
  rows: T[];
  rowKey: (row: T) => string | number;
  renderRow: (row: T) => ReactNode[];
  isLoading?: boolean;
  emptyMessage?: string;
  statusContent?: ReactNode;
  onRowClick?: (row: T) => void;
  rowHoverOutlineColor?: string;
  showHeader?: boolean;
  enableColumnControls?: boolean;
  defaultHiddenColumnKeys?: string[];
  storageKey?: string;
  stickyFirstColumn?: boolean;
  stickyLastColumn?: boolean;
  pageSize?: number;
  showSearch?: boolean;
  searchPlaceholder?: string;
  getRowSearchText?: (row: T) => string;
  toolbarContent?: ReactNode;
  addButtonLabel?: string;
  onAddClick?: () => void;
  showAddAction?: boolean;
  showSettingsAction?: boolean;
  showViewToggle?: boolean;
  defaultViewMode?: LegacyDataViewMode;
  renderCard?: (row: T, rowIndex: number) => ReactNode;
  cardExpansionControl?: {
    checked: boolean;
    onChange: (checked: boolean) => void;
    openLabel?: string;
    closeLabel?: string;
  };
};

export function DataTable<T>({
  columns,
  rows,
  rowKey,
  renderRow,
  isLoading = false,
  emptyMessage = "Данные отсутствуют.",
  statusContent,
  onRowClick,
  showHeader = true,
  pageSize = 8,
  showSearch = true,
  searchPlaceholder = "Найти",
  getRowSearchText,
  addButtonLabel = "Добавить",
  onAddClick,
  showAddAction = true,
  showSettingsAction = true,
  showViewToggle = true,
  defaultViewMode,
  renderCard,
  cardExpansionControl
}: DataTableProps<T>) {
  const theme = useTheme();

  const rowContentByKey = useMemo(() => {
    const map = new Map<string, ReactNode[]>();
    rows.forEach((row) => {
      map.set(String(rowKey(row)), renderRow(row));
    });
    return map;
  }, [renderRow, rowKey, rows]);

  const tableColumns = useMemo<TableTemplateColumn<T>[]>(() => {
    return columns.map((column, index) => ({
      id: column.key,
      header: typeof column.label === "string" ? column.label : typeof column.label === "number" ? String(column.label) : column.key,
      width: typeof column.width === "number" ? `${column.width}px` : column.fraction ? `${column.fraction}fr` : undefined,
      minWidth: column.minWidth,
      align: column.align,
      renderCell: (row) => {
        const currentCells = rowContentByKey.get(String(rowKey(row))) ?? renderRow(row);
        const content = currentCells[index];

        return (
          <Stack
            sx={{ minWidth: 0, width: "100%", cursor: onRowClick ? "pointer" : "default" }}
            onClick={() => onRowClick?.(row)}
          >
            {content}
          </Stack>
        );
      },
      getSearchValue: getRowSearchText
        ? (row) => getRowSearchText(row)
        : (row) => {
          const currentCells = rowContentByKey.get(String(rowKey(row))) ?? renderRow(row);
          return valueToText(currentCells[index]);
        }
    }));
  }, [columns, getRowSearchText, onRowClick, renderRow, rowContentByKey, rowKey]);

  if (statusContent) {
    return (
      <Paper
        sx={{
          borderRadius: `${theme.acomShape.panelRadius}px`,
          border: "1px solid",
          borderColor: "divider",
          p: 2
        }}
      >
        {statusContent}
      </Paper>
    );
  }

  if (isLoading) {
    return (
      <Paper
        sx={{
          borderRadius: `${theme.acomShape.panelRadius}px`,
          border: "1px solid",
          borderColor: "divider",
          p: 2
        }}
      >
        <Typography variant="body2">{"Загрузка..."}</Typography>
      </Paper>
    );
  }

  if (!showHeader) {
    return (
      <Paper
        sx={{
          borderRadius: `${theme.acomShape.panelRadius}px`,
          border: "1px solid",
          borderColor: "divider",
          p: 1.5
        }}
      >
        {rows.length === 0 ? (
          <Typography variant="body2">{emptyMessage}</Typography>
        ) : (
          <Stack spacing={0.75}>
            {rows.map((row) => {
              const cells = renderRow(row);

              return (
                <Stack
                  key={rowKey(row)}
                  sx={{
                    display: "grid",
                    gridTemplateColumns: `repeat(${Math.max(columns.length, 1)}, minmax(0, 1fr))`,
                    border: "1px solid",
                    borderColor: "divider",
                    borderRadius: `${theme.acomShape.controlRadius}px`,
                    overflow: "hidden",
                    backgroundColor: "background.paper"
                  }}
                >
                  {columns.map((column, index) => (
                    <Stack
                      key={`${rowKey(row)}-${column.key}`}
                      alignItems={alignToFlex(column.align)}
                      sx={{
                        minWidth: 0,
                        px: 1.5,
                        py: 1.2,
                        borderRight: index === columns.length - 1 ? "none" : "1px solid",
                        borderColor: "divider"
                      }}
                    >
                      {cells[index]}
                    </Stack>
                  ))}
                </Stack>
              );
            })}
          </Stack>
        )}
      </Paper>
    );
  }

  return (
    <TableTemplate
      columns={tableColumns}
      rows={rows}
      getRowId={(row) => rowKey(row)}
      renderCard={renderCard}
      searchPlaceholder={searchPlaceholder}
      showSearch={showSearch}
      addButtonLabel={addButtonLabel}
      onAddClick={showAddAction ? onAddClick : undefined}
      showAddAction={showAddAction}
      showSettingsAction={showSettingsAction}
      showViewToggle={showViewToggle}
      defaultViewMode={defaultViewMode}
      rowsPerPageOptions={[pageSize]}
      defaultRowsPerPage={pageSize}
      noRowsLabel={emptyMessage}
      noSearchResultsLabel={"Ничего не найдено по запросу."}
      cardExpansionControl={cardExpansionControl}
    />
  );
}

export { TableTemplate } from "./TableTemplate";
export type { TableTemplateColumn, TableTemplateProps } from "./TableTemplate";
