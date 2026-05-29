import { useMemo, useState } from 'react';
import {
    Accordion,
    AccordionDetails,
    AccordionSummary,
    Box,
    Button,
    Chip,
    Dialog,
    DialogContent,
    Stack,
    Tooltip,
    Typography
} from '@mui/material';
import HelpOutlineRounded from '@mui/icons-material/HelpOutlineRounded';
import { useTheme } from '@mui/material/styles';
import { useAuth } from '@app/providers/AuthProvider';
import { ActionButton } from '@shared/components/ActionButton';
import { GuideSectionBody, GuideSummaryBody } from '@shared/components/GuideSectionBody';
import { roleGuides } from '@shared/content/roleGuides';
import { blurActiveElement } from '@shared/lib/dom/blurActiveElement';

type RoleGuideButtonProps = {
    iconOnly?: boolean;
    sidebar?: boolean;
};

export const RoleGuideButton = ({ iconOnly = false, sidebar = false }: RoleGuideButtonProps) => {
    const theme = useTheme();
    const { session } = useAuth();
    const [open, setOpen] = useState(false);
    const roleGuide = useMemo(() => roleGuides[session?.roleId ?? 0], [session?.roleId]);

    const handleOpen = () => {
        blurActiveElement();
        setOpen(true);
    };

    if (!roleGuide) {
        return null;
    }

    return (
        <>
            {sidebar ? (
                <Tooltip title="Памятка по роли" placement="right" enterDelay={150} disableHoverListener={!iconOnly}>
                    <Box component="span" sx={{ display: 'block', width: '100%' }}>
                        <ActionButton
                            kind="custom"
                            showNavigationIcons={false}
                            onClick={handleOpen}
                            aria-label="Открыть памятку по роли"
                            sx={{
                                width: '100%',
                                minWidth: 0,
                                minHeight: 42,
                                borderRadius: `${theme.acomShape.buttonRadius}px !important`,
                                justifyContent: iconOnly ? 'center' : 'flex-start',
                                px: iconOnly ? 0 : 1.75,
                                gap: iconOnly ? 0 : 1.25,
                                transition: 'padding 0.32s ease, gap 0.32s ease'
                            }}
                        >
                            <Box component="span" sx={{ display: 'inline-flex', lineHeight: 1 }}>
                                <HelpOutlineRounded fontSize="small" />
                            </Box>
                            <Typography
                                sx={{
                                    maxWidth: iconOnly ? 0 : 160,
                                    opacity: iconOnly ? 0 : 1,
                                    transform: iconOnly ? 'translateX(-4px)' : 'translateX(0)',
                                    overflow: 'hidden',
                                    textOverflow: 'clip',
                                    whiteSpace: 'nowrap',
                                    fontSize: 14,
                                    fontWeight: 500,
                                    lineHeight: 1.2,
                                    transition: 'max-width 0.34s ease, opacity 0.24s ease, transform 0.34s ease'
                                }}
                            >
                                {'Памятка'}
                            </Typography>
                        </ActionButton>
                    </Box>
                </Tooltip>
            ) : iconOnly ? (
                <Tooltip title="Памятка по роли" placement="right" enterDelay={150}>
                    <Box component="span" sx={{ display: 'block', width: '100%' }}>
                        <ActionButton
                            kind="custom"
                            showNavigationIcons={false}
                            onClick={handleOpen}
                            aria-label="Открыть памятку по роли"
                            sx={{
                                width: '100%',
                                minWidth: 0,
                                minHeight: 42,
                                height: 42,
                                borderRadius: `${theme.acomShape.buttonRadius}px !important`,
                                justifyContent: 'center',
                                px: 0,
                                gap: 0
                            }}
                        >
                            <Box component="span" sx={{ display: 'inline-flex', lineHeight: 1 }}>
                                <HelpOutlineRounded fontSize="small" />
                            </Box>
                        </ActionButton>
                    </Box>
                </Tooltip>
            ) : (
            <Button
                variant="outlined"
                onClick={handleOpen}
                startIcon={<HelpOutlineRounded fontSize="small" />}
                sx={{
                    minWidth: 124,
                    height: 42,
                    borderRadius: `${theme.acomShape.buttonRadius}px`,
                    textTransform: 'none',
                    '&:hover': {
                        boxShadow: 'none'
                    }
                }}
                aria-label="Открыть памятку по роли"
            >
                Памятка
            </Button>
            )}

            <Dialog open={open} onClose={() => setOpen(false)} fullWidth maxWidth="md">
                <DialogContent sx={{ p: { xs: 2, md: 3 }, backgroundColor: '#f4f6fb' }}>
                    <Stack spacing={2}>
                        <Stack direction="row" alignItems="center" justifyContent="space-between" flexWrap="wrap" gap={1}>
                            <Typography variant="h5" fontWeight={700}>
                                {roleGuide.title}
                            </Typography>
                            <Chip label="Справка по роли" color="primary" variant="outlined" />
                        </Stack>

                        <Box
                            sx={{
                                p: 2,
                                borderRadius: 1,
                                border: '1px solid',
                                borderColor: 'divider',
                                backgroundColor: 'background.paper'
                            }}
                        >
                            <GuideSummaryBody summary={roleGuide.summary} />
                        </Box>

                        <Box
                            sx={{
                                borderRadius: 1,
                                border: '1px solid',
                                borderColor: 'divider',
                                overflow: 'hidden',
                                backgroundColor: 'background.paper'
                            }}
                        >
                            {roleGuide.sections.map((section) => (
                                <Accordion key={section.title} disableGutters elevation={0}>
                                    <AccordionSummary>
                                        <Typography fontWeight={600}>{section.title}</Typography>
                                    </AccordionSummary>
                                    <AccordionDetails>
                                        <GuideSectionBody blocks={section.blocks} />
                                    </AccordionDetails>
                                </Accordion>
                            ))}
                        </Box>

                        <Typography variant="caption" color="text.secondary" sx={{ textAlign: 'right', pt: 0.5 }}>
                            Created by «Цифровизация проектных задач»
                        </Typography>
                    </Stack>
                </DialogContent>
            </Dialog>
        </>
    );
};
