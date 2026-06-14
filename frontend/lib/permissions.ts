/**
 * Qual permissão cada agente exige pra aparecer/abrir.
 *
 * Isto é só UX (esconder o que o usuário não pode usar). A trava de verdade
 * está no backend (require_permission). Agente sem entrada aqui = visível pra
 * qualquer usuário logado.
 */
export const AGENT_PERMISSAO: Record<string, string> = {
  'perfil-mestre': 'pessoal.ver',
  vagas: 'pessoal.ver',
  freela: 'pessoal.ver',
  financas: 'financas.ver',
};

export function permissaoDoAgente(slug: string): string | undefined {
  return AGENT_PERMISSAO[slug];
}
