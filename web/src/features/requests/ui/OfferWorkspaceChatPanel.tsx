import React from 'react';

import { zodResolver } from '@hookform/resolvers/zod';
import AttachFileRoundedIcon from '@mui/icons-material/AttachFileRounded';
import CloseRoundedIcon from '@mui/icons-material/CloseRounded';
import DoneAllRoundedIcon from '@mui/icons-material/DoneAllRounded';
import DoneRoundedIcon from '@mui/icons-material/DoneRounded';
import SendRoundedIcon from '@mui/icons-material/SendRounded';
import { alpha } from '@mui/material/styles';
import { Box, Button, Chip, Divider, IconButton, Menu, MenuItem, Paper, Stack, TextField, Typography } from '@mui/material';
import { Controller, useForm } from 'react-hook-form';
import { z } from 'zod';
import type { OfferWorkspaceMessage } from '@shared/api/offers/offerWorkspaceActions';
import { getFileKey, mergeUniqueFiles } from '@shared/lib/files';

const AUTO_SCROLL_THRESHOLD_PX = 64;

const chatSchema = z.object({
  text: z.string().trim().min(1, 'Введите сообщение').max(3000, 'Максимум 3000 символов'),
  files: z.array(z.instanceof(File)).default([])
});

type ChatFormValues = z.infer<typeof chatSchema>;

const formatTime = (value: string | null) => {
  if (!value) return '--:--';

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;

  return new Intl.DateTimeFormat('ru-RU', { hour: '2-digit', minute: '2-digit' }).format(date);
};

const formatReadAt = (value: string | null) => {
  if (!value) return '';

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '';

  return new Intl.DateTimeFormat('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  }).format(date);
};

const startOfDay = (d: Date) => new Date(d.getFullYear(), d.getMonth(), d.getDate());

const isSameDay = (a: Date, b: Date) =>
  a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate();

const AUTO_EMAIL_MESSAGE_LABEL = 'Сообщение сформировано автоматически из письма';
const AUTO_EMAIL_PREFIXES = ['📧 Из письма контрагента', AUTO_EMAIL_MESSAGE_LABEL, '🤖 Сообщение сформировано автоматически из письма'];
const AUTO_EMAIL_OFFER_CREATED_TEXTS = [
  'КП сформировано автоматически из письма',
  '📧 КП создано из ответа на e-mail',
  '🤖 КП сформировано автоматически из письма',
  'КП сформировано автоматически из письма',
  '📧 КП создано из ответа на e-mail',
  '🤖 КП сформировано автоматически из письма'
];

const parseEmailOriginText = (text: string) => {
  const normalized = text.trimStart();
  const prefix = AUTO_EMAIL_PREFIXES.find((item) => normalized.startsWith(item));
  if (!prefix) {
    return { isEmailOrigin: false, body: text };
  }

  const body = normalized.slice(prefix.length).trimStart();
  return { isEmailOrigin: true, body };
};

const formatDayLabel = (iso: string | null) => {
  if (!iso) return 'Без даты';

  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return 'Без даты';

  const today = startOfDay(new Date());
  const msgDay = startOfDay(d);

  const diffDays = Math.round((today.getTime() - msgDay.getTime()) / 86400000);

  if (diffDays === 0) return 'Сегодня';
  if (diffDays === 1) return 'Вчера';

  return new Intl.DateTimeFormat('ru-RU', {
    day: 'numeric',
    month: 'long',
    year: 'numeric'
  }).format(d);
};

const getMessageStatusLabel = (status: OfferWorkspaceMessage['status']) => {
  if (status === 'send') {
    return 'Отправлено на сервер';
  }
  if (status === 'received') {
    return 'Доставлено получателю';
  }
  return 'Прочитано получателем';
};

const MessageStatusIcon = ({ status }: { status: OfferWorkspaceMessage['status'] }) => {
  const statusMeta: Record<OfferWorkspaceMessage['status'], { color: string; label: string }> = {
    send: {
      color: 'rgba(255,255,255,0.78)',
      label: 'Отправлено на сервер'
    },
    received: {
      color: 'rgba(255,255,255,0.82)',
      label: 'Доставлено получателю'
    },
    read: {
      color: '#9fe4ff',
      label: 'Прочитано получателем'
    }
  };

  const meta = statusMeta[status];

  return (
    <Box
      component="span"
      sx={{
        position: 'relative',
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        width: 22,
        height: 22,
        ml: 0.35,
        flexShrink: 0,
        transform: 'translateY(2px)'
      }}
      aria-label={`message-status-${status}`}
    >
      {status === 'send' ? (
        <DoneRoundedIcon sx={{ fontSize: 18, color: meta.color }} aria-hidden="true" />
      ) : (
        <DoneAllRoundedIcon sx={{ fontSize: 18, color: meta.color }} aria-hidden="true" />
      )}
    </Box>
  );
};

type OfferWorkspaceChatPanelProps = {
  offerId: number;
  isOpen: boolean;
  onToggleOpen: (next: boolean) => void;
  messages: OfferWorkspaceMessage[];
  typingUserIds: string[];
  sessionLogin?: string;
  canSendMessage: boolean;
  canSendMessageWithAttachments: boolean;
  isSending: boolean;
  onSendMessage: (text: string, files: File[]) => Promise<void>;
  onMessageInputClick: () => Promise<void> | void;
  onMessageDraftChange: (text: string) => Promise<void> | void;
  onDownloadAttachment: (downloadUrl: string, name: string) => void;
  readOnlyNotice?: string | null;
  contractorUserId?: string;
};

export const OfferWorkspaceChatPanel = ({
  offerId,
  isOpen,
  onToggleOpen,
  messages,
  typingUserIds,
  sessionLogin,
  canSendMessage,
  canSendMessageWithAttachments,
  isSending,
  onSendMessage,
  onMessageInputClick,
  onMessageDraftChange,
  onDownloadAttachment,
  readOnlyNotice,
  contractorUserId
}: OfferWorkspaceChatPanelProps) => {
  const {
    control,
    handleSubmit,
    watch,
    setValue,
    reset,
    formState: { errors }
  } = useForm<ChatFormValues>({
    resolver: zodResolver(chatSchema),
    defaultValues: { text: '', files: [] }
  });

  const attachedFiles = watch('files');
  const messageText = watch('text');
  const messagesContainerRef = React.useRef<HTMLDivElement | null>(null);
  const messageInputRef = React.useRef<HTMLTextAreaElement | null>(null);
  const [statusMenuState, setStatusMenuState] = React.useState<{
    mouseX: number;
    mouseY: number;
    message: OfferWorkspaceMessage;
  } | null>(null);

  const scrollToBottom = React.useCallback((force = false) => {
    const container = messagesContainerRef.current;
    if (!container) {
      return;
    }

    const distanceToBottom = container.scrollHeight - container.scrollTop - container.clientHeight;
    if (!force && distanceToBottom > AUTO_SCROLL_THRESHOLD_PX) {
      return;
    }

    container.scrollTop = container.scrollHeight;
  }, []);

  const sortedMessages = React.useMemo(() => {
    return [...messages].sort(
      (a, b) => new Date(a.created_at ?? 0).getTime() - new Date(b.created_at ?? 0).getTime()
    );
  }, [messages]);

  const handleRemoveAttachedFile = (fileToRemove: File) => {
    const nextFiles = attachedFiles.filter((file) => getFileKey(file) !== getFileKey(fileToRemove));
    setValue('files', nextFiles, { shouldDirty: true, shouldTouch: true, shouldValidate: true });
  };

  React.useEffect(() => {
    scrollToBottom(true);
  }, [scrollToBottom, isOpen]);

  React.useEffect(() => {
    scrollToBottom();
  }, [scrollToBottom, sortedMessages]);

  React.useEffect(() => {
    void onMessageDraftChange(messageText);
  }, [messageText, onMessageDraftChange]);

  const handleStatusContextMenu = React.useCallback(
    (event: React.MouseEvent, message: OfferWorkspaceMessage) => {
      event.preventDefault();
      setStatusMenuState({
        mouseX: event.clientX + 2,
        mouseY: event.clientY - 6,
        message
      });
    },
    []
  );

  const handleCloseStatusMenu = React.useCallback(() => {
    setStatusMenuState(null);
  }, []);

  const onSubmitMessage = async (values: ChatFormValues) => {
    if (!canSendMessage) return;

    const trimmedText = values.text.trim();
    if (!trimmedText) return;

    await onSendMessage(trimmedText, values.files);
    reset({ text: '', files: [] });
    window.requestAnimationFrame(() => {
      if (messageInputRef.current) {
        messageInputRef.current.style.height = 'auto';
      }
    });
    scrollToBottom(true);
  };

  return (
    <Paper
      sx={{
        width: { xs: '100%', lg: isOpen ? 430 : 72 },
        borderRadius: 0,
        borderLeft: { lg: '1px solid #d6dbe4' },
        p: 0,
        display: 'flex',
        flexDirection: 'column',
        minHeight: 0,
        height: '100%',
        overflow: 'hidden',
        transition: 'width 0.2s ease'
      }}
    >
      {isOpen ? (
        <>
          <Box sx={{ display: 'flex', alignItems: 'center', p: 2 }}>
            <Typography variant="h6" fontWeight={600} sx={{ flex: 1 }}>
              Чат по КП №{offerId}
            </Typography>
            <IconButton onClick={() => onToggleOpen(false)} aria-label="Скрыть чат">
              <CloseRoundedIcon fontSize="small" />
            </IconButton>
          </Box>
          <Divider />


          <Stack spacing={1} sx={{ p: 2, height: '100%', minHeight: 0 }}>
            <Box
              ref={messagesContainerRef}
              sx={{
                flex: 1,
                minHeight: 0,
                overflowY: 'auto',
                scrollbarWidth: 'none',
                '&::-webkit-scrollbar': {
                  display: 'none'
                },
                borderRadius: 2,
                backgroundColor: (theme) => alpha(theme.palette.primary.main, 0.05),
                p: 2
              }}
            >
              {sortedMessages.length === 0 ? (
                <Typography variant="body2" color="text.secondary">
                  Сообщений пока нет.
                </Typography>
              ) : (
                <Stack spacing={0} alignItems="stretch">
                  {sortedMessages.map((item, idx) => {
                    const ownMessage = item.user_id === sessionLogin;
                    const isContractorMessage = Boolean(contractorUserId) && item.user_id === contractorUserId;
                    const isSystemMessage = Boolean(item.is_system);
                    const parsedEmailText = parseEmailOriginText(item.text);
                    const isEmailOriginMessage = !isSystemMessage && parsedEmailText.isEmailOrigin;
                    const normalizedText = item.text.trim();
                    const isAutoOfferCreatedMessage = !isSystemMessage
                      && AUTO_EMAIL_OFFER_CREATED_TEXTS.some((text) => normalizedText.startsWith(text));
                    const isSystemVisualMessage = isSystemMessage || isAutoOfferCreatedMessage;
                    const displayText = isEmailOriginMessage ? parsedEmailText.body : item.text;
                    const normalizedDisplayText = displayText.trim();
                    const hasVisibleText = normalizedDisplayText.length > 0;
                    const shouldHideEmptyAutoMessage =
                      isAutoOfferCreatedMessage &&
                      normalizedDisplayText.length === 0 &&
                      item.attachments.length === 0;

                    if (shouldHideEmptyAutoMessage) {
                      return null;
                    }

                    const prev = idx > 0 ? sortedMessages[idx - 1] : null;

                    const showDateDivider = !prev
                      ? true
                      : (() => {
                        const a = new Date(prev.created_at ?? '');
                        const b = new Date(item.created_at ?? '');
                        if (Number.isNaN(a.getTime()) || Number.isNaN(b.getTime())) return false;
                        return !isSameDay(a, b);
                      })();

                    const isGroupedWithPrev = Boolean(
                      prev &&
                      prev.user_id === item.user_id &&
                      isSameDay(new Date(prev.created_at ?? ''), new Date(item.created_at ?? ''))
                    );

                    const senderName = item.user_full_name?.trim() || item.user_id;

                    return (
                      <Box key={item.id}>
                        {showDateDivider ? (
                          <Box sx={{ display: 'flex', justifyContent: 'center', my: 1 }}>
                            <Box
                              sx={(theme) => ({
                                px: 1.5,
                                py: 0.5,
                                borderRadius: 999,
                                fontSize: 12,
                                fontWeight: 600,
                                color: theme.palette.text.secondary,
                                backgroundColor: alpha(theme.palette.common.white, 0.75),
                                border: `1px solid ${alpha(theme.palette.divider, 0.6)}`,
                                boxShadow: '0 1px 2px rgba(0,0,0,0.04)'
                              })}
                            >
                              {formatDayLabel(item.created_at)}
                            </Box>
                          </Box>
                        ) : null}

                        <Box
                          sx={{
                            display: 'flex',
                            justifyContent: isSystemVisualMessage ? 'center' : ownMessage ? 'flex-end' : 'flex-start',
                            mt: showDateDivider ? 0.9 : isGroupedWithPrev ? 0.25 : 0.9
                          }}
                        >
                          <Box
                            sx={(theme) => {
                              const R = 18;
                              const CUT = 6;
                              const top = isGroupedWithPrev ? 10 : R;

                              return {
                                maxWidth: isSystemVisualMessage ? '100%' : '82%',
                                px: 1.6,
                                py: isSystemVisualMessage ? 0.7 : 1.1,

                                borderRadius: isSystemVisualMessage  ? '999px' : `${R}px`,
                                borderTopLeftRadius: ownMessage ? `${top}px` : `${CUT}px`,
                                borderTopRightRadius: ownMessage ? `${CUT}px` : `${top}px`,
                                borderBottomLeftRadius: `${R}px`,
                                borderBottomRightRadius: `${R}px`,

                                backgroundColor: isSystemVisualMessage 
                                  ? alpha(theme.palette.warning.main, 0.12)
                                  : isEmailOriginMessage
                                    ? alpha(theme.palette.primary.main, 0.12)
                                    : ownMessage
                                      ? theme.palette.primary.main
                                      : isContractorMessage
                                        ? '#eaf4ff'
                                        : alpha(theme.palette.background.paper, 0.98),
                                color: isSystemVisualMessage
                                  ? theme.palette.text.secondary
                                  : isEmailOriginMessage
                                    ? theme.palette.text.primary
                                    : ownMessage
                                      ? 'rgba(255,255,255,0.96)'
                                      : theme.palette.text.primary,
                                opacity: item.is_muted ? 0.6 : 1,

                                boxShadow: isSystemVisualMessage
                                  ? 'none'
                                  : ownMessage
                                  ? `0 6px 18px ${alpha(theme.palette.primary.main, 0.18)}`
                                  : '0 1px 4px rgba(0,0,0,0.06)',

                                border: isSystemVisualMessage
                                  ? `1px dashed ${alpha(theme.palette.warning.main, 0.4)}`
                                  : isEmailOriginMessage
                                    ? `1px dashed ${alpha(theme.palette.primary.main, 0.35)}`
                                    : ownMessage
                                      ? 'none'
                                      : isContractorMessage
                                        ? `1px solid ${alpha(theme.palette.primary.main, 0.16)}`
                                        : 'none',

                                overflowWrap: 'anywhere'
                              };
                            }}
                            onContextMenu={
                              ownMessage && !isSystemVisualMessage
                                ? (event) => handleStatusContextMenu(event, item)
                                : undefined
                            }
                          >
                            {!isGroupedWithPrev && !isSystemVisualMessage  ? (
                              <Typography
                                variant="caption"
                                sx={{
                                  display: 'block',
                                  mb: 0.5,
                                  fontWeight: 600,
                                  color: ownMessage ? alpha('#fff', 0.9) : 'text.secondary',
                                  letterSpacing: 0.1
                                }}
                              >
                                {ownMessage ? 'Я' : senderName}
                              </Typography>
                            ) : null}

                            {isEmailOriginMessage ? (
                              <Typography
                                variant="caption"
                                sx={{
                                  display: 'block',
                                  mb: 0.45,
                                  fontStyle: 'italic',
                                  color: 'text.secondary'
                                }}
                              >
                                {AUTO_EMAIL_MESSAGE_LABEL}
                              </Typography>
                            ) : null}

                            <Box
                              sx={{
                                position: 'relative',
                                pr: isSystemVisualMessage ? 0 : hasVisibleText ? 8.8 : 7.4,
                                pb: 0,
                                minHeight: isSystemVisualMessage ? 'auto' : 18
                              }}
                            >
                              {hasVisibleText ? (
                                <Typography
                                  variant={isSystemVisualMessage ? 'caption' : 'body1'}
                                  component="div"
                                sx={{
                                    mb: item.attachments.length > 0 ? 0.8 : 0.35,
                                    lineHeight: 1.32,
                                    whiteSpace: 'pre-wrap',
                                    fontStyle: isSystemVisualMessage ? 'italic' : 'normal',
                                    textAlign: isSystemVisualMessage ? 'center' : 'left',
                                    display: 'block'
                                  }}
                                >
                                  {displayText}
                                </Typography>
                              ) : null}

                              {item.attachments.length > 0 ? (
                                <Stack spacing={0.5} sx={{ mb: 0 }}>
                                  {item.attachments.map((attachment) => (
                                    <Chip
                                      key={attachment.id}
                                      size="small"
                                      label={attachment.name}
                                      variant="outlined"
                                      onClick={() => onDownloadAttachment(attachment.download_url, attachment.name)}
                                      sx={(theme) => ({
                                        alignSelf: isSystemVisualMessage ? 'center' : ownMessage ? 'flex-end' : 'flex-start',
                                        borderColor: ownMessage
                                          ? alpha(theme.palette.common.white, 0.35)
                                          : theme.palette.divider,
                                        color: ownMessage ? 'rgba(255,255,255,0.92)' : theme.palette.text.primary,
                                        backgroundColor: ownMessage
                                          ? alpha(theme.palette.primary.dark, 0.34)
                                          : theme.palette.background.default,
                                        '& .MuiChip-label': { color: 'inherit' }
                                      })}
                                    />
                                  ))}
                                </Stack>
                              ) : null}

                              {!isSystemVisualMessage ? (
                                <Box
                                  sx={{
                                    position: 'absolute',
                                    right: 0,
                                    bottom: -5,
                                    display: 'inline-flex',
                                    alignItems: 'flex-end',
                                    gap: 0.15,
                                    whiteSpace: 'nowrap',
                                    color: ownMessage ? alpha('#fff', 0.82) : 'text.secondary'
                                  }}
                                >
                                  <Typography
                                    component="span"
                                    variant="caption"
                                    sx={{
                                      fontSize: 12,
                                      lineHeight: '12px',
                                      color: 'inherit'
                                    }}
                                  >
                                    {formatTime(item.created_at)}
                                  </Typography>

                                  {ownMessage ? <MessageStatusIcon status={item.status} /> : null}
                                </Box>
                              ) : null}
                            </Box>
                          </Box>
                        </Box>
                      </Box>
                    );
                  })}
                </Stack>
              )}

              {typingUserIds.length > 0 ? (
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1.5, textAlign: 'center' }}>
                  {typingUserIds.length === 1 ? `${typingUserIds[0]} печатает...` : 'Несколько участников печатают...'}
                </Typography>
              ) : null}
            </Box>

            {readOnlyNotice ? (
              <Typography variant="caption" color="text.secondary">{readOnlyNotice}</Typography>
            ) : null}

            <Box component="form" onSubmit={handleSubmit(onSubmitMessage)} sx={{ flexShrink: 0 }}>
              <Controller
                control={control}
                name="text"
                render={({ field }) => (
                  <TextField
                    placeholder="Введите сообщение"
                    multiline
                    minRows={3}
                    fullWidth
                    disabled={isSending}
                    error={Boolean(errors.text)}
                    helperText={errors.text?.message}
                    InputProps={{ readOnly: !canSendMessage }}
                    name={field.name}
                    value={field.value}
                    inputRef={(element) => {
                      field.ref(element);
                      messageInputRef.current = element;
                    }}
                    onBlur={field.onBlur}
                    onChange={field.onChange}
                    onClick={() => void onMessageInputClick()}
                    onFocus={() => void onMessageInputClick()}
                  />
                )}
              />

              <Stack direction="row" flexWrap="wrap" gap={1} sx={{ mt: 1 }}>
                {attachedFiles.map((file) => (
                  <Chip
                    key={getFileKey(file)}
                    label={file.name}
                    size="small"
                    onDelete={() => handleRemoveAttachedFile(file)}
                  />
                ))}
              </Stack>

              <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mt: 1 }}>
                {canSendMessageWithAttachments ? (
                  <IconButton
                    component="label"
                    disabled={isSending}
                    color="primary"
                    aria-label="Прикрепить файлы"
                    sx={{
                      border: (theme) => `1px solid ${alpha(theme.palette.primary.main, 0.24)}`,
                      backgroundColor: (theme) => alpha(theme.palette.primary.main, 0.08),
                      '&:hover': {
                        backgroundColor: (theme) => alpha(theme.palette.primary.main, 0.16)
                      }
                    }}
                  >
                    <AttachFileRoundedIcon fontSize="small" />
                    <Controller
                      control={control}
                      name="files"
                      render={({ field: { value, onChange } }) => (
                        <input
                          type="file"
                          hidden
                          multiple
                          onChange={(event) => {
                            const nextFiles = Array.from(event.target.files ?? []);
                            onChange(mergeUniqueFiles(value ?? [], nextFiles));
                            event.target.value = '';
                          }}
                        />
                      )}
                    />
                  </IconButton>
                ) : (
                  <Box />
                )}

                <IconButton
                  type="submit"
                  color="primary"
                  disabled={!canSendMessage || isSending || !messageText.trim()}
                  aria-label={isSending ? 'Отправка сообщения' : 'Отправить сообщение'}
                  sx={{
                    border: (theme) => `1px solid ${alpha(theme.palette.primary.main, 0.24)}`,
                    backgroundColor: (theme) => alpha(theme.palette.primary.main, 0.1),
                    '&:hover': {
                      backgroundColor: (theme) => alpha(theme.palette.primary.main, 0.2)
                    }
                  }}
                >
                  <SendRoundedIcon fontSize="small" />
                </IconButton>
              </Stack>
            </Box>
          </Stack>

          <Menu
            open={statusMenuState !== null}
            onClose={handleCloseStatusMenu}
            anchorReference="anchorPosition"
            anchorPosition={
              statusMenuState !== null
                ? { top: statusMenuState.mouseY, left: statusMenuState.mouseX }
                : undefined
            }
            transformOrigin={{ horizontal: 'left', vertical: 'top' }}
          >
            {statusMenuState ? (
              <Box sx={{ minWidth: 260, maxWidth: 340, py: 0.5 }}>
                <MenuItem onClick={handleCloseStatusMenu}>
                  <Box sx={{ display: 'inline-flex', alignItems: 'center', mr: 1 }}>
                    <MessageStatusIcon status={statusMenuState.message.status} />
                  </Box>
                  <Typography variant="body2">
                    {getMessageStatusLabel(statusMenuState.message.status)}
                  </Typography>
                </MenuItem>

                <Divider />

                {statusMenuState.message.read_by.length > 0 ? (
                  statusMenuState.message.read_by.map((reader) => (
                    <MenuItem key={reader.user_id} onClick={handleCloseStatusMenu}>
                      <Box sx={{ minWidth: 0 }}>
                        <Typography variant="body2" noWrap>
                          {reader.user_full_name?.trim() || reader.user_id}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          Прочитал(а) {formatReadAt(reader.read_at)}
                        </Typography>
                      </Box>
                    </MenuItem>
                  ))
                ) : (
                  <MenuItem onClick={handleCloseStatusMenu}>
                    <Typography variant="body2" color="text.secondary">
                      Пока никто не прочитал
                    </Typography>
                  </MenuItem>
                )}
              </Box>
            ) : null}
          </Menu>
        </>
      ) : (
        <Box sx={{ p: 1 }}>
          <Button variant="text" size="small" onClick={() => onToggleOpen(true)}>
            Чат
          </Button>
        </Box>
      )}
    </Paper>
  );
};
