/**
 * Quem é o "dono" dos dados no dashboard financeiro.
 *
 * IMPORTANTE: a partir do endurecimento do `usuario_id` (Step B), o backend
 * deriva o dono SEMPRE da sessão logada — este valor enviado nas chamadas é
 * ignorado pelo servidor (mantido só por compatibilidade do payload). Não é
 * mais um controle de acesso; trocar isto não dá acesso a dados de outro perfil.
 */
export const FINANCAS_USUARIO_ID =
  process.env.NEXT_PUBLIC_FINANCAS_USUARIO_ID ||
  '00000000-0000-0000-0000-000000000001';
