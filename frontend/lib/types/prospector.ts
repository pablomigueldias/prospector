// Prospector — coleta/enriquecimento de leads (CNPJ, contatos, histórico).

export interface ProspectorManualRequest {
  cnpj: string;
  site?: string | null;
  instagram?: string | null;
  facebook?: string | null;
  linkedin?: string | null;
  email?: string | null;
  telefone?: string | null;
  whatsapp?: string | null;
}

export interface Contato {
  nome: string | null;
  cargo: string | null;
  email: string | null;
  telefone: string | null;
  whatsapp: string | null;
  linkedin: string | null;
  decisor: boolean;
}

export interface Empresa {
  nome: string | null;
  razao_social: string | null;
  cnpj: string | null;
  cidade: string | null;
  estado: string | null;
  setor: string | null;
  tamanho: string | null;
  capital_social: number | null;
  site: string | null;
  instagram: string | null;
  facebook: string | null;
  notas: string | null;
  notion_page_id: string | null;
}

export interface Lead {
  empresa: Empresa;
  contatos: Contato[];
}

export type FonteCnpj = 'brasilapi' | 'opencnpj' | null;

export interface ProspectorPreviewResponse {
  success: boolean;
  fonte_cnpj: FonteCnpj;
  lead: Lead;
}

export interface ProspectorRunResponse {
  success: boolean;
  fonte_cnpj: FonteCnpj;
  lead: Lead;
  notion_empresa_id: string | null;
  notion_contatos_ids: string[];
}

export interface LeadHistoryItem {
  empresa_nome: string;
  cnpj: string | null;
  cidade: string | null;
  estado: string | null;
  setor: string | null;
  qtd_contatos: number;
  notion_empresa_id: string | null;
  enviado_em: string | null; // ISO 8601
  arquivo: string;
}

export interface LeadHistoryResponse {
  items: LeadHistoryItem[];
  total: number;
}
