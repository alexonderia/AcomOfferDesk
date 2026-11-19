import { existsSync } from 'node:fs';
import path from 'node:path';
import { describe, expect, it } from 'vitest';
import { ROLE } from '@shared/constants/roles';
import { MAX_CONTACT_LINK } from '@shared/constants/supportContacts';
import { roleGuides } from './roleGuides';
import { findGuideSections, guideBlockText } from './roleGuideTypes';

describe('User documentation contracts', () => {
  it('covers every existing role with unique chapters and available illustrations', () => {
    expect(Object.keys(roleGuides).map(Number).sort()).toEqual(Object.values(ROLE).sort());
    for (const guide of Object.values(roleGuides)) {
      expect(guide.sections.length).toBeGreaterThan(5);
      expect(new Set(guide.sections.map((chapter) => chapter.id)).size).toBe(guide.sections.length);
      const blocks = guide.sections.flatMap((chapter) => chapter.blocks);
      const content = [guide.title, guide.summary, ...guide.sections.map((chapter) => chapter.title), ...blocks.map(guideBlockText)];
      expect(content.join(' ')).not.toMatch(/суперадмин/i);
      expect(blocks).toContainEqual(expect.objectContaining({ type: 'link', href: MAX_CONTACT_LINK }));
      for (const chapter of guide.sections) {
        const images = chapter.blocks.filter((block) => block.type === 'image');
        expect(images.length, `${guide.title}: ${chapter.title}`).toBeGreaterThan(0);
        for (const block of images) {
          expect(block.caption).toMatch(/учебн/i);
          expect(existsSync(path.join(process.cwd(), 'public', block.src.replace(/^\//, '')))).toBe(true);
        }
      }
    }
  });

  it.each(Object.values(ROLE).filter((role) => role !== ROLE.CONTRACTOR))('explains role differences and hierarchy for staff role %s', (role) => {
    const ids = roleGuides[role].sections.map((chapter) => chapter.id);
    expect(ids).toEqual(expect.arrayContaining(['role-comparison', 'hierarchy', 'hierarchy-scope', 'hierarchy-tasks']));
  });

  it('keeps contractor chapters and their searchable content independent from internal instructions', () => {
    const guide = roleGuides[ROLE.CONTRACTOR];
    const content = guide.sections.flatMap((chapter) => [chapter.title, ...chapter.blocks.map(guideBlockText)]).join(' ');
    expect(content).not.toMatch(/иерархи|подплан|корневой план|ведущий экономист|руководитель проекта|суперадминистратор/i);
    const contractorExamples = new Set([
      'contractor-guide', 'login', 'contractor-available', 'contractor-respond', 'requests-contractor',
      'contractor-edit', 'contractor-chat', 'contractor-files', 'file-preview', 'password',
      'contractor-notifications', 'feedback',
    ]);
    for (const chapter of guide.sections) {
      for (const block of chapter.blocks) {
        if (block.type !== 'image') continue;
        const name = path.basename(block.src, '.png');
        expect(contractorExamples.has(name), name).toBe(true);
      }
    }
    expect(findGuideSections(guide.sections, 'иерархия')).toEqual([]);
    expect(findGuideSections(guide.sections, 'подплан')).toEqual([]);
    expect(findGuideSections(guide.sections, 'пароль').length).toBeGreaterThan(0);
  });

  it('finds instructions inside tables and handles case, ё and multiple search words', () => {
    const guide = roleGuides[ROLE.ECONOMIST];
    expect(findGuideSections(guide.sections, '900 000').map((chapter) => chapter.id)).toEqual(['closing']);
    expect(findGuideSections(guide.sections, 'ПОДЧИНЕННЫМ экономист').length).toBeGreaterThan(0);
    expect(findGuideSections(guide.sections, '   ')).toEqual(guide.sections);
  });
});
