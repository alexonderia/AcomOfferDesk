import { Alert, Box, Stack, Typography } from '@mui/material';
import type { FeedbackListItem } from '@shared/api/feedback/getFeedbackList';
import { DataTable, type DataTableColumn } from '@shared/components/DataTable';
import { useFeedbackList } from '../model/useFeedbackList';

const columns: DataTableColumn[] = [
  { key: 'id', label: 'ID', minWidth: 90, fraction: 0.5 },
  { key: 'text', label: 'Текст обратной связи', minWidth: 480, fraction: 3.5 }
];

export const FeedbackPageView = () => {
  const { items, isLoading, error } = useFeedbackList();

  return (
    <Stack spacing={1.5}>
      <Typography variant="h5" sx={{ fontWeight: 700 }}>
        Обратная связь
      </Typography>

      {error ? <Alert severity="error">{error}</Alert> : null}

      <Box sx={{ minWidth: 0 }}>
        <DataTable<FeedbackListItem>
          columns={columns}
          rows={items}
          rowKey={(row) => row.id}
          renderRow={(row) => [row.id, row.text]}
          isLoading={isLoading}
          emptyMessage="Обратная связь пока не поступала"
          storageKey="superadmin-feedback"
          stickyLastColumn={false}
        />
      </Box>
    </Stack>
  );
};
