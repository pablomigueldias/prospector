// Auth — login / sessão / permissões / administração de usuários.

export interface Usuario {
  id: string;
  email: string;
  nome: string;
  ativo: boolean;
  twofa_ativado: boolean;
  ultimo_login: string | null;
  permissoes: string[];
}

export interface PapelItem {
  nome: string;
  descricao: string | null;
}

export interface UsuarioAdminItem {
  id: string;
  email: string;
  nome: string;
  ativo: boolean;
  twofa_ativado: boolean;
  papeis: string[];
  ultimo_login: string | null;
  created_at: string | null;
}
