// Agendamentos (S4) — jobs do scheduler vistos na UI.

export interface Job {
  id: string;
  nome: string;
  descricao: string;
  hora: number;
  ligado: boolean;
  hora_key: string; // chave de config p/ editar a hora (via S3)
  enabled_key: string; // chave de config p/ ligar/desligar (via S3)
}

export interface JobRunResult {
  job: string;
  executado_em: string;
  resultado: Record<string, unknown>;
}
