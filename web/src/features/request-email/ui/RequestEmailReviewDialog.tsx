import { useState } from 'react';
import { Alert, Box, Button, Stack, TextField, MenuItem, Typography } from '@mui/material';
import type { RequestEmailPreview, RequestEmailPreviewAttachment } from '@shared/api/requests/previewRequestEmails';
import { ConfirmationDialog } from '@shared/components/ConfirmationDialog';
import { FilePreviewTrigger } from '@shared/components/file-preview/FilePreviewTrigger';
import type { FilePreviewSource } from '@shared/lib/files/preview';

export type RequestEmailReviewSummary = {
  id: string;
  description: string | null;
  deadline: string;
  amount: string | number | null;
  files: FilePreviewSource[];
  sourceFiles?: FilePreviewSource[];
  extractionFiles?: string[];
  specification?: { itemCount: number; usedOcr: boolean };
  hiddenContractors?: string[];
};

const PreviewFile = ({ source }: { source: FilePreviewSource }) => (
  <FilePreviewTrigger source={source}>
    {(open) => <Button variant="outlined" size="small" onClick={open} sx={{ alignSelf: 'flex-start', maxWidth: '100%', overflowWrap: 'anywhere' }}>
      Предпросмотр: {source.name}
    </Button>}
  </FilePreviewTrigger>
);

export const RequestEmailReviewDialog = ({ preview, summary, fontStyles, localFiles = [], isPending, pendingHint, onCancel, onConfirm, creating = false }: {
  preview: RequestEmailPreview;
  summary: RequestEmailReviewSummary;
  fontStyles: string;
  localFiles?: File[];
  isPending: boolean;
  pendingHint?: string;
  creating?: boolean;
  onCancel: () => void;
  onConfirm: () => Promise<void>;
}) => {
  const [selectedEmail, setSelectedEmail] = useState(preview.messages[0]?.to_email ?? '');
  const message = preview.messages.find((item) => item.to_email === selectedEmail);
  const fileSource = (item: RequestEmailPreviewAttachment): FilePreviewSource | null => {
    if (item.upload_index !== null && localFiles[item.upload_index]) return { name: item.name, file: localFiles[item.upload_index] };
    return item.download_url ? { name: item.name, downloadUrl: item.download_url } : null;
  };

  return <ConfirmationDialog open title="Проверка перед отправкой" maxWidth="md"
    description="Проверьте заявку, файлы и письма получателям. Отправка начнётся только после подтверждения."
    confirmLabel={creating ? 'Подтвердить и создать заявку' : 'Подтвердить и отправить'}
    pendingLabel={creating ? 'Создание и отправка...' : 'Отправка...'} isPending={isPending}
    confirmDisabled={!creating && preview.messages.length === 0} onCancel={onCancel} onConfirm={onConfirm}>
    <Stack spacing={2} sx={{ mt: 2 }}>
      {isPending && pendingHint ? <Alert severity="info">{pendingHint}</Alert> : null}
      <Stack spacing={0.5}>
        <Typography variant="h6">1. Содержимое заявки</Typography>
        <Typography>Заявка №{summary.id}</Typography>
        <Typography sx={{ whiteSpace: 'pre-wrap' }}>{summary.description || 'Описание не указано'}</Typography>
        <Typography>Сбор откликов до: {new Date(summary.deadline).toLocaleString('ru-RU')}</Typography>
        {summary.amount !== null ? <Typography>Сумма по ТЗ: {summary.amount} ₽</Typography> : null}
        {summary.hiddenContractors?.length ? <Typography>Скрыта от: {summary.hiddenContractors.join(', ')}</Typography> : null}
      </Stack>
      <Stack spacing={1}>
        <Typography variant="h6">2. Предпросмотр файлов</Typography>
        {summary.specification ? <Typography>Выделено позиций: {summary.specification.itemCount}</Typography> : null}
        {summary.specification?.usedOcr ? <Alert severity="warning">Часть документа распознана со скана. Сверьте наименования, артикулы и количество с исходником.</Alert> : null}
        {summary.extractionFiles ? <Typography variant="body2">Для формирования заявки: {summary.extractionFiles.join(', ')}</Typography> : null}
        {summary.sourceFiles?.length ? <>
          <Alert severity="info">Контрагенты получат только спецификацию и публичные вложения. Сравните спецификацию с исходниками: проверьте позиции, количество и отсутствие цен и реквизитов.</Alert>
          <Typography variant="subtitle2">Исходники — доступны только сотрудникам с доступом к заявке</Typography>
          {summary.sourceFiles.map((source, index) => <PreviewFile key={`source-${index}`} source={source} />)}
        </> : null}
        {creating || summary.sourceFiles?.length ? <Typography variant="subtitle2">Файлы для контрагентов</Typography> : null}
        {summary.files.length ? summary.files.map((source, index) => <PreviewFile key={index} source={source} />)
          : <Typography color="text.secondary">Файлов нет</Typography>}
      </Stack>
      <Stack spacing={1}>
        <Typography variant="h6">3. Получатели и письма ({preview.messages.length})</Typography>
        <Alert severity="info">Каждому получателю отправляется отдельное письмо. Адреса других участников рассылки ему не видны.</Alert>
        {preview.warnings.map((warning) => <Alert key={warning} severity="warning">{warning}</Alert>)}
        {message ? <>
          <TextField select fullWidth label="Получатель и вариант письма" value={selectedEmail}
            onChange={(event) => setSelectedEmail(event.target.value)}>
            {preview.messages.map((item) => <MenuItem key={item.to_email} value={item.to_email} sx={{ whiteSpace: 'normal', overflowWrap: 'anywhere' }}>
              {item.to_email} — {item.kind === 'registered' ? 'Новая заявка' : 'Заявка с приглашением'}
            </MenuItem>)}
          </TextField>
          <Typography>Кому: {message.to_email}</Typography>
          <Typography>Тема: {message.subject}</Typography>
          <Box component="iframe" title={`Письмо для ${message.to_email}`} sandbox="" referrerPolicy="no-referrer"
            srcDoc={`<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; font-src data:; img-src data:">${message.html_content}<style>${fontStyles}body,table,td,a,p,span{font-family:'Alabuga Sans',sans-serif}</style>`}
            sx={{ width: '100%', minWidth: 0, height: { xs: 440, sm: 520 }, border: '1px solid', borderColor: 'divider', borderRadius: 1, bgcolor: 'white' }} />
          <Typography variant="subtitle2">Вложения этого письма</Typography>
          {message.attachments.length ? message.attachments.map((item, index) => {
            const source = fileSource(item);
            return source ? <PreviewFile key={index} source={source} /> : <Typography key={index}>{item.name}</Typography>;
          }) : <Typography color="text.secondary">Без вложений</Typography>}
          <Typography variant="caption" color="text.secondary">Персональный код ответа создаётся при отправке. Получатели и доступность файлов повторно проверяются сервером.</Typography>
        </> : null}
      </Stack>
    </Stack>
  </ConfirmationDialog>;
};
