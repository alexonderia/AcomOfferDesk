export type ParentLinkedTreeNode<T> = T & { children: ParentLinkedTreeNode<T>[] };

export const buildTreeFromParentId = <T extends { user_id: string }>(
  items: T[],
  getParentId: (item: T) => string | null,
): ParentLinkedTreeNode<T>[] => {
  if (items.length === 0) {
    return [];
  }

  const nodes = new Map<string, ParentLinkedTreeNode<T>>(
    items.map((item) => [item.user_id, { ...item, children: [] }]),
  );
  const childIds = new Set<string>();

  items.forEach((item) => {
    const parentId = getParentId(item);
    if (!parentId || parentId === item.user_id || !nodes.has(parentId)) {
      return;
    }
    nodes.get(parentId)!.children.push(nodes.get(item.user_id)!);
    childIds.add(item.user_id);
  });

  return items
    .filter((item) => !childIds.has(item.user_id))
    .map((item) => nodes.get(item.user_id)!);
};
