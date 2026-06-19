// Observabilidade de IA (S2) — agregações sobre ai_calls.

export interface ObsTotais {
  chamadas: number;
  falhas: number;
  taxa_erro: number;
  tokens: number;
  custo_usd: number;
  latencia_media_ms: number | null;
}

export interface ObsPorAgente {
  agente: string;
  chamadas: number;
  falhas: number;
  taxa_erro: number;
  tokens: number;
  custo_usd: number;
  latencia_media_ms: number | null;
}

export interface ObsPorDia {
  dia: string;
  chamadas: number;
  tokens: number;
  custo_usd: number;
}

export interface ObsChamada {
  created_at: string | null;
  agente: string;
  operacao: string | null;
  provider: string;
  modelo: string;
  tokens_total: number | null;
  custo_usd: number;
  latencia_ms: number | null;
  sucesso: boolean;
  error_message: string | null;
}

export interface ObsResumo {
  periodo_dias: number;
  totais: ObsTotais;
  por_agente: ObsPorAgente[];
  por_dia: ObsPorDia[];
  ultimas: ObsChamada[];
}
