/**
 * Quem é o "dono" dos dados no dashboard financeiro.
 *
 * Multi-tenant leve: por enquanto o front assume um único perfil (você).
 * Defina NEXT_PUBLIC_FINANCAS_USUARIO_ID com o seu usuario_id real; o default
 * abaixo serve só pra dev não quebrar.
 */
export const FINANCAS_USUARIO_ID =
  process.env.NEXT_PUBLIC_FINANCAS_USUARIO_ID ||
  '00000000-0000-0000-0000-000000000001';
