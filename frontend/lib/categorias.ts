import type { CategoriaTreeItem } from './types';

export interface CategoriaPlana {
  id: string;
  nome: string;
  depth: number;
}

/** Achata a árvore de categorias numa lista com profundidade (pra <select>). */
export function achatarCategorias(
  itens: CategoriaTreeItem[],
  depth = 0,
  acc: CategoriaPlana[] = [],
): CategoriaPlana[] {
  for (const c of itens) {
    acc.push({ id: c.id, nome: c.nome, depth });
    if (c.filhos?.length) achatarCategorias(c.filhos, depth + 1, acc);
  }
  return acc;
}
