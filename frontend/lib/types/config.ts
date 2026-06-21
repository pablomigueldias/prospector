// Configurações na UI (S3, self-service). Espelha o catálogo do backend.

export type ConfigTipo = 'bool' | 'int' | 'select';

export interface ConfigItem {
  chave: string;
  categoria: string;
  label: string;
  tipo: ConfigTipo;
  ajuda: string;
  opcoes: string[];
  minimo: number | null;
  maximo: number | null;
  requer_restart: boolean;
  valor: boolean | number | string;
  default: boolean | number | string;
  sobrescrito: boolean;
}
