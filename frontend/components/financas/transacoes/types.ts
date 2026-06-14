/** Valores que pré-preenchem o LancamentoForm quando se edita uma transação.
 *  Compartilhado entre a Section (que monta a partir do detalhe) e o form. */
export interface LancamentoInicial {
  id: string;
  tipo: 'despesa' | 'receita';
  descricao: string;
  valor: string;
  contaId: string;
  categoriaId: string;
  data: string;
  prevista: boolean;
}
