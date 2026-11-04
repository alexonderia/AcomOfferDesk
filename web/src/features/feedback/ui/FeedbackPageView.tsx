import { Alert, Box, Button, MenuItem, Stack, TablePagination, TextField, Typography } from '@mui/material';
import type { FeedbackListItem } from '@shared/api/feedback/getFeedbackList';
import { DataTable, type DataTableColumn } from '@shared/components/DataTable';
import { useFeedbackList } from '../model/useFeedbackList';

const columns: DataTableColumn[] = [
  { key: 'id', label: 'ID', minWidth: 90, fraction: 0.5 },
  { key: 'text', label: 'Текст обратной связи', minWidth: 320, fraction: 3.5 },
  { key: 'author', label: 'Автор', minWidth: 160, fraction: 1 },
  { key: 'created_at', label: 'Отправлено', minWidth: 160, fraction: 1 },
];

export const FeedbackPageView = () => {
  const { items, isLoading, error, query, setQuery, total, reload } = useFeedbackList();

  return (
    <Stack spacing={1.5}>
      <Typography variant="h5" sx={{ fontWeight: 700 }}>
        Обратная связь
      </Typography>

      {error ? <Alert severity="error">{error}</Alert> : null}

      <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1}>
        <TextField size="small" label="Поиск по тексту или автору" value={query.search} onChange={(e) => setQuery({ ...query, search: e.target.value, page: 0 })} />
        <TextField size="small" label="Логин автора" value={query.author} onChange={(e) => setQuery({ ...query, author: e.target.value, page: 0 })} />
        <TextField size="small" select label="Порядок" value={query.sortOrder} onChange={(e) => setQuery({ ...query, sortOrder: e.target.value, page: 0 })} sx={{ minWidth: 160 }}>
          <MenuItem value="desc">Сначала новые</MenuItem><MenuItem value="asc">Сначала старые</MenuItem>
        </TextField>
        <Button onClick={reload} disabled={isLoading}>Обновить</Button>
      </Stack>

      <Box sx={{ minWidth: 0 }}>
        <DataTable<FeedbackListItem>
          columns={columns}
          rows={items}
          rowKey={(row) => row.id}
          renderRow={(row) => [row.id, row.text, row.author_name || row.author_user_id || 'Автор неизвестен', row.created_at ? new Date(row.created_at).toLocaleString('ru-RU') : 'Время неизвестно']}
          isLoading={isLoading}
          emptyMessage="Обратная связь пока не поступала"
          storageKey="superadmin-feedback"
          stickyLastColumn={false}
        />
      </Box>
      <TablePagination component="div" count={total} page={query.page} rowsPerPage={query.pageSize} rowsPerPageOptions={[20, 50, 100]} onPageChange={(_, page) => setQuery({ ...query, page })} onRowsPerPageChange={(e) => setQuery({ ...query, pageSize: Number(e.target.value), page: 0 })} labelRowsPerPage="Строк на странице" />
    </Stack>
  );
};
