import NavigateNextRounded from '@mui/icons-material/NavigateNextRounded';
import Breadcrumbs from '@mui/material/Breadcrumbs';
import ButtonBase from '@mui/material/ButtonBase';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';

export type BreadcrumbItem = {
  key: string;
  label: string;
  onClick?: () => void;
};

type BreadcrumbsNavProps = {
  items: BreadcrumbItem[];
};

export const BreadcrumbsNav = ({ items }: BreadcrumbsNavProps) => {
  if (items.length === 0) {
    return null;
  }

  return (
    <Stack
      sx={{
        px: 0,
        py: 0.75,
      }}
    >
      <Breadcrumbs separator={<NavigateNextRounded sx={{ fontSize: 20 }} />} aria-label="breadcrumb">
        {items.map((item, index) => {
          const isLast = index === items.length - 1;
          if (!item.onClick || isLast) {
            return (
              <Typography
                key={item.key}
                sx={{
                  color: isLast ? 'text.primary' : 'text.secondary',
                  fontWeight: isLast ? 600 : 500,
                  fontSize: 20,
                  lineHeight: 1.25,
                  maxWidth: 320,
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                }}
              >
                {item.label}
              </Typography>
            );
          }

          return (
            <ButtonBase
              key={item.key}
              onClick={item.onClick}
              sx={{
                borderRadius: 1,
                px: 0.4,
                py: 0.1,
                color: 'text.secondary',
                fontSize: 20,
                lineHeight: 1.25,
                fontWeight: 500,
                maxWidth: 320,
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                '&:hover': {
                  textDecoration: 'none',
                },
              }}
            >
              {item.label}
            </ButtonBase>
          );
        })}
      </Breadcrumbs>
    </Stack>
  );
};
