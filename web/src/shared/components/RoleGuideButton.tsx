import { useMemo, useRef, useState } from 'react';
import {
  Box, Button, Chip, Dialog, DialogContent, DialogTitle, IconButton, InputAdornment,
  List, ListItemButton, ListItemText, Stack, TextField, Tooltip, Typography,
} from '@mui/material';
import HelpOutlineRounded from '@mui/icons-material/HelpOutlineRounded';
import CloseRounded from '@mui/icons-material/CloseRounded';
import SearchRounded from '@mui/icons-material/SearchRounded';
import { alpha, useTheme } from '@mui/material/styles';
import { useAuth } from '@app/providers/AuthProvider';
import { ActionButton } from '@shared/components/ActionButton';
import { GuideSectionBody, GuideSummaryBody } from '@shared/components/GuideSectionBody';
import { roleGuides, type GuideRole } from '@shared/content/roleGuides';
import { findGuideSections } from '@shared/content/roleGuideTypes';
import { blurActiveElement } from '@shared/lib/dom/blurActiveElement';
import { dialogContentSx, dialogPaperSx } from '@shared/ui/dialogSurface';

export const RoleGuideDialog = ({ guide, open, onClose }: { guide: GuideRole; open: boolean; onClose: () => void }) => {
  const [query, setQuery] = useState('');
  const [selectedId, setSelectedId] = useState(guide.sections[0]?.id);
  const chapters = useMemo(() => findGuideSections(guide.sections, query), [guide.sections, query]);
  const active = chapters.find((chapter) => chapter.id === selectedId) ?? chapters[0];
  const articleRef = useRef<HTMLElement>(null);
  const contentRef = useRef<HTMLDivElement>(null);

  const resetReadingScroll = () => {
    contentRef.current?.scrollTo?.({ top: 0 });
    articleRef.current?.scrollTo?.({ top: 0 });
  };

  const updateQuery = (value: string) => {
    setQuery(value);
    resetReadingScroll();
  };

  const selectChapter = (id: string) => {
    setSelectedId(id);
    resetReadingScroll();
    articleRef.current?.focus({ preventScroll: true });
  };

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="lg" aria-labelledby="role-guide-title"
      PaperProps={{ sx: (theme) => ({
        ...dialogPaperSx(theme),
        height: 760,
        maxHeight: 'calc(100dvh - 64px)',
      }) }}>
      <DialogTitle id="role-guide-titlebar" component="div" sx={{ p: 0, pb: 2 }}>
        <Stack direction="row" alignItems="flex-start" justifyContent="space-between" gap={1}>
          <Box sx={{ minWidth: 0 }}>
            <Typography id="role-guide-title" component="h1" variant="h5" fontWeight={700}>{guide.title}</Typography>
            <Typography variant="caption" color="text.secondary">Документация и инструкции</Typography>
          </Box>
          <IconButton onClick={onClose} aria-label="Закрыть руководство" sx={{ minWidth: 44, minHeight: 44 }}><CloseRounded /></IconButton>
        </Stack>
      </DialogTitle>
      <TextField label="Поиск по руководству" value={query} onChange={(event) => updateQuery(event.target.value)} size="small" fullWidth
        InputProps={{
          startAdornment: <InputAdornment position="start"><SearchRounded fontSize="small" /></InputAdornment>,
          endAdornment: query ? <InputAdornment position="end"><IconButton aria-label="Очистить поиск" onClick={() => updateQuery('')} edge="end" sx={{ minWidth: 44, minHeight: 44 }}><CloseRounded fontSize="small" /></IconButton></InputAdornment> : undefined,
        }} />
      <DialogContent ref={contentRef} sx={{ ...dialogContentSx, mt: 2, minHeight: 0, overflowY: { xs: 'auto', md: 'hidden' } }}>
        <Box sx={{
          display: 'grid',
          height: { md: '100%' },
          gridTemplateColumns: { xs: 'minmax(0, 1fr)', md: '240px minmax(0, 1fr)' },
          gridTemplateRows: { md: 'minmax(0, 1fr)' },
          gap: { xs: 2, md: 3 },
        }}>
          <Box component="nav" aria-label="Оглавление руководства"
            sx={{ display: 'flex', flexDirection: 'column', minWidth: 0, minHeight: 0 }}>
            <Stack direction="row" alignItems="center" justifyContent="space-between" sx={{ mb: 1, flexShrink: 0 }}>
              <Typography fontWeight={700}>Оглавление</Typography>
              <Chip size="small" label={chapters.length} aria-label={`Найдено глав: ${chapters.length}`} />
            </Stack>
            <List disablePadding sx={(theme) => {
              const thumb = alpha(theme.palette.text.primary, 0.38);
              return {
                flex: { md: 1 },
                minHeight: 0,
                maxHeight: { xs: 190, md: 'none' },
                overflowY: 'auto',
                scrollbarWidth: 'thin',
                scrollbarColor: `${thumb} transparent`,
                '&::-webkit-scrollbar': { width: 6, background: 'transparent' },
                '&::-webkit-scrollbar-track': { background: 'transparent' },
                '&::-webkit-scrollbar-thumb': { borderRadius: 8, backgroundColor: thumb },
                '&::-webkit-scrollbar-button': { display: 'none' },
              };
            }}>
              {chapters.map((chapter) => (
                <ListItemButton key={chapter.id} component="button" type="button" selected={active?.id === chapter.id}
                  aria-current={active?.id === chapter.id ? 'page' : undefined} aria-controls="role-guide-chapter"
                  onClick={() => selectChapter(chapter.id)} sx={{ width: '100%', minHeight: 44, textAlign: 'left', borderRadius: 1, mb: 0.5 }}>
                  <ListItemText primary={chapter.title} primaryTypographyProps={{ variant: 'body2' }} />
                </ListItemButton>
              ))}
            </List>
          </Box>
          <Box component="article" ref={articleRef} id="role-guide-chapter" tabIndex={-1}
            sx={{ ...dialogContentSx, minWidth: 0, minHeight: 0, overflowY: { xs: 'visible', md: 'auto' },
              overflowX: { xs: 'visible', md: 'hidden' }, overflowWrap: 'break-word', pb: 1, outline: 0,
              '&:focus-visible': { outline: '2px solid', outlineColor: 'primary.main', outlineOffset: -2, borderRadius: 1 } }}>
            {active ? <Stack spacing={2}>
              <Typography component="h2" variant="h6" fontWeight={700}>{active.title}</Typography>
              {!query && active.id === guide.sections[0]?.id ? <GuideSummaryBody summary={guide.summary} /> : null}
              <GuideSectionBody blocks={active.blocks} />
            </Stack> : <Box role="status" sx={{ p: 2 }}>
              <Typography fontWeight={700}>Ничего не найдено</Typography>
              <Typography variant="body2" color="text.secondary">Попробуйте другое слово или очистите поиск. Поиск работает только по вашему руководству.</Typography>
            </Box>}
          </Box>
        </Box>
      </DialogContent>
    </Dialog>
  );
};

type RoleGuideButtonProps = { iconOnly?: boolean; sidebar?: boolean };

export const RoleGuideButton = ({ iconOnly = false, sidebar = false }: RoleGuideButtonProps) => {
  const theme = useTheme();
  const { session } = useAuth();
  const [open, setOpen] = useState(false);
  const guide = roleGuides[session?.roleId ?? 0];
  if (!guide) return null;

  const handleOpen = () => { blurActiveElement(); setOpen(true); };
  return <>
    {sidebar || iconOnly ? <Tooltip title="Руководство пользователя" placement="right" disableHoverListener={!iconOnly}>
      <Box component="span" sx={{ display: 'block', width: '100%' }}>
        <ActionButton kind="custom" showNavigationIcons={false} onClick={handleOpen} aria-label="Открыть памятку по роли"
          sx={{ width: '100%', minWidth: 0, minHeight: 44, borderRadius: `${theme.acomShape.buttonRadius}px !important`,
            justifyContent: iconOnly ? 'center' : 'flex-start', px: iconOnly ? 0 : 1.75, gap: iconOnly ? 0 : 1.25 }}>
          <HelpOutlineRounded fontSize="small" />
          {!iconOnly ? <Typography sx={{ fontSize: 14, fontWeight: 500 }}>Памятка</Typography> : null}
        </ActionButton>
      </Box>
    </Tooltip> : <Button variant="outlined" onClick={handleOpen} startIcon={<HelpOutlineRounded fontSize="small" />}
      aria-label="Открыть памятку по роли" sx={{ minWidth: 124, height: 44, textTransform: 'none' }}>Памятка</Button>}
    {open ? <RoleGuideDialog key={session?.roleId} guide={guide} open onClose={() => setOpen(false)} /> : null}
  </>;
};
