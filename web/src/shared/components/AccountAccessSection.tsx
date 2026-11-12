import InfoOutlined from '@mui/icons-material/InfoOutlined';
import { Box, ClickAwayListener, IconButton, Stack, Tooltip, Typography } from '@mui/material';
import { useState, type ReactNode } from 'react';
import { sectionTitleSx } from '@shared/theme/sectionTitleSx';

export const AccountAccessSection = ({ children, emailEnabled = false }: {
  children?: ReactNode;
  emailEnabled?: boolean;
}) => {
  const [infoOpen, setInfoOpen] = useState(false);
  return (
    <Stack
      component="section"
      role="group"
      aria-label="Данные для входа"
      spacing={2}
      sx={{ border: '1px solid', borderColor: 'divider', borderRadius: 2, p: { xs: 1.5, sm: 2 }, backgroundColor: 'background.paper', minWidth: 0 }}
    >
      <Stack direction="row" spacing={0.5} alignItems="center">
        <Typography sx={sectionTitleSx}>Данные для входа</Typography>
        <ClickAwayListener onClickAway={() => setInfoOpen(false)}>
          <Box component="span" sx={{ display: 'inline-flex' }}>
          <Tooltip
            open={infoOpen}
            onOpen={() => setInfoOpen(true)}
            onClose={() => setInfoOpen(false)}
            title={
              <Typography variant="body2">
                Если пароль не задан или забыт, администратор вашего подразделения или суперадминистратор может установить новый и передать данные для входа. Свой пароль можно поменять в профиле, указав текущий.
                {emailEnabled ? ' Если к учётной записи привязан e-mail, задать или восстановить пароль также можно через «Восстановить доступ» на странице входа.' : ''}
              </Typography>
            }
            arrow
            describeChild
            placement="top"
            disableTouchListener
            disableHoverListener
            disableFocusListener
            componentsProps={{ tooltip: { sx: { maxWidth: 360, p: 1.25, borderRadius: 1.5 } } }}
          >
            <IconButton type="button" size="small" color="primary" aria-label="Как получить доступ и сменить пароль" onClick={() => setInfoOpen(true)} onMouseEnter={() => setInfoOpen(true)} onFocus={() => setInfoOpen(true)}>
              <InfoOutlined fontSize="small" />
            </IconButton>
          </Tooltip>
          </Box>
        </ClickAwayListener>
      </Stack>
      {children}
    </Stack>
  );
};
