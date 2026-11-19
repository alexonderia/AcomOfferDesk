import { useMemo, useState, type ReactNode } from 'react';
import { Alert, Box, Link, Stack, Table, TableBody, TableCell, TableHead, TableRow, Typography } from '@mui/material';
import type { GuideBlock } from '@shared/content/roleGuides';

const listSx = { m: 0, pl: 2.5, '& li': { display: 'list-item' } };

export const formatGuideText = (text: string): ReactNode => {
    const parts = text.split(/(\*\*.*?\*\*|\*.*?\*)/g);

    return parts.map((part, index) => {
        if (part.startsWith('**') && part.endsWith('**')) {
            return <strong key={index}>{part.slice(2, -2)}</strong>;
        }

        if (part.startsWith('*') && part.endsWith('*')) {
            return <em key={index}>{part.slice(1, -1)}</em>;
        }

        return part;
    });
};

const GuideList = ({ ordered, items }: { ordered: boolean; items: string[] }) => {
    const ListTag = ordered ? 'ol' : 'ul';

    return (
        <Box component={ListTag} sx={listSx}>
            {items.map((item, index) => (
                <Typography key={`${index}-${item}`} component="li" variant="body2">
                    {formatGuideText(item)}
                </Typography>
            ))}
        </Box>
    );
};

const GuideTable = ({ headers, rows }: { headers: string[]; rows: string[][] }) => (
    <Box
        role="region"
        aria-label={`Таблица: ${headers.join(', ')}`}
        tabIndex={0}
        sx={{
            overflowX: 'auto',
            border: '1px solid',
            borderColor: 'divider',
            borderRadius: 1
        }}
    >
        <Table size="small" sx={{ minWidth: headers.length > 2 ? 640 : 460, '& th:first-of-type, & td:first-of-type': { minWidth: 150 } }}>
            <TableHead>
                <TableRow>
                    {headers.map((header) => (
                        <TableCell component="th" scope="col" key={header} sx={{ fontWeight: 600, backgroundColor: 'action.hover' }}>
                            {formatGuideText(header)}
                        </TableCell>
                    ))}
                </TableRow>
            </TableHead>
            <TableBody>
                {rows.map((row, rowIndex) => (
                    <TableRow key={rowIndex}>
                        {row.map((cell, cellIndex) => (
                            <TableCell key={cellIndex} sx={{ verticalAlign: 'top' }}>
                                {formatGuideText(cell)}
                            </TableCell>
                        ))}
                    </TableRow>
                ))}
            </TableBody>
        </Table>
    </Box>
);

const GuideImage = ({ block }: { block: Extract<GuideBlock, { type: 'image' }> }) => {
    const [failed, setFailed] = useState(false);
    return (
        <Box component="figure" sx={{ m: 0, minWidth: 0 }}>
            {failed ? <Alert severity="info" role="note">Иллюстрация недоступна. Пользуйтесь текстовой инструкцией этой главы.</Alert> : (
                <Box component="a" href={block.src} target="_blank" rel="noopener noreferrer" aria-label={`Открыть иллюстрацию: ${block.alt}`}
                    sx={{
                        display: 'inline-block', maxWidth: '100%', verticalAlign: 'top', borderRadius: 1,
                        '&:focus-visible': { outline: '2px solid', outlineColor: 'primary.main', outlineOffset: 2 },
                    }}>
                    <Box component="img" src={block.src} alt={block.alt} loading="lazy" onError={() => setFailed(true)}
                        sx={{ display: 'block', maxWidth: '100%', maxHeight: 'min(50dvh, 480px)', width: 'auto', height: 'auto', borderRadius: 'inherit' }} />
                </Box>
            )}
            <Typography component="figcaption" variant="caption" color="text.secondary" sx={{ mt: 0.5 }}>
                {block.caption}{!failed && ' Нажмите иллюстрацию, чтобы открыть оригинал.'}
            </Typography>
        </Box>
    );
};

const GuideBlockView = ({ block }: { block: GuideBlock }) => {
    switch (block.type) {
        case 'paragraph':
            return (
                <Typography variant="body2" component="p" sx={{ m: 0 }}>
                    {formatGuideText(block.text)}
                </Typography>
            );
        case 'subheading':
            return (
                <Typography variant="subtitle1" component="h3" sx={{ m: 0, mt: 1, fontWeight: 700 }}>
                    {formatGuideText(block.text)}
                </Typography>
            );
        case 'list':
            return <GuideList ordered={block.ordered} items={block.items} />;
        case 'table':
            return <GuideTable headers={block.headers} rows={block.rows} />;
        case 'notice':
            return <Alert severity={block.tone} role="note">{formatGuideText(block.text)}</Alert>;
        case 'link':
            return <Link href={block.href} target="_blank" rel="noopener noreferrer" variant="body2" sx={{ alignSelf: 'flex-start' }}>{block.text}</Link>;
        case 'image':
            return <GuideImage key={block.src} block={block} />;
        default: {
            const _exhaustive: never = block;
            return _exhaustive;
        }
    }
};

export const GuideSectionBody = ({ blocks }: { blocks: GuideBlock[] }) => (
    <Stack spacing={1.25}>
        {blocks.map((block, index) => (
            <GuideBlockView key={index} block={block} />
        ))}
    </Stack>
);

export const GuideSummaryBody = ({ summary }: { summary: string }) => {
    const paragraphs = useMemo(
        () => summary.split(/\n\n+/).map((part) => part.trim()).filter(Boolean),
        [summary]
    );

    return (
        <Stack spacing={1}>
            {paragraphs.map((paragraph, index) => (
                <Typography key={index} variant="body2" color="text.secondary" sx={{ m: 0 }}>
                    {formatGuideText(paragraph)}
                </Typography>
            ))}
        </Stack>
    );
};
