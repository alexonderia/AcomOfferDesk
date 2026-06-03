import { useMemo, type ReactNode } from 'react';
import { Box, Stack, Table, TableBody, TableCell, TableHead, TableRow, Typography } from '@mui/material';
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
        sx={{
            overflowX: 'auto',
            border: '1px solid',
            borderColor: 'divider',
            borderRadius: 1
        }}
    >
        <Table size="small">
            <TableHead>
                <TableRow>
                    {headers.map((header) => (
                        <TableCell key={header} sx={{ fontWeight: 600, backgroundColor: 'action.hover' }}>
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
                <Typography variant="body2" component="p" sx={{ m: 0, fontWeight: 600 }}>
                    {formatGuideText(block.text)}
                </Typography>
            );
        case 'list':
            return <GuideList ordered={block.ordered} items={block.items} />;
        case 'table':
            return <GuideTable headers={block.headers} rows={block.rows} />;
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
