export type GuideBlock =
  | { type: 'paragraph' | 'subheading'; text: string }
  | { type: 'list'; ordered: boolean; items: string[] }
  | { type: 'table'; headers: string[]; rows: string[][] }
  | { type: 'notice'; tone: 'info' | 'warning' | 'success'; text: string }
  | { type: 'link'; text: string; href: string }
  | { type: 'image'; src: string; alt: string; caption: string };

export type GuideSection = {
  id: string;
  title: string;
  blocks: GuideBlock[];
};

export type GuideRole = {
  title: string;
  summary: string;
  sections: GuideSection[];
};

export const guideBlockText = (block: GuideBlock): string => {
  switch (block.type) {
    case 'paragraph':
    case 'subheading':
    case 'notice':
    case 'link':
      return block.text;
    case 'list':
      return block.items.join(' ');
    case 'table':
      return [...block.headers, ...block.rows.flat()].join(' ');
    case 'image':
      return `${block.alt} ${block.caption}`;
  }
};

export const findGuideSections = (sections: GuideSection[], query: string): GuideSection[] => {
  const words = query.toLocaleLowerCase('ru-RU').replace(/ё/g, 'е').trim().split(/\s+/).filter(Boolean);
  return sections.filter((section) => {
    const text = [section.title, ...section.blocks.map(guideBlockText)].join(' ').toLocaleLowerCase('ru-RU').replace(/ё/g, 'е');
    return words.every((word) => text.includes(word));
  });
};
