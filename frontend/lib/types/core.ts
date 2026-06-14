// Tipos transversais: catálogo de agentes da plataforma + erro de API.

export type AgentStatus = 'active' | 'soon' | 'experimental';

export interface Agent {
  slug: string;
  name: string;
  description: string;
  icon: string; // ex: "ti-radar", "ti-cash"
  status: AgentStatus;
  order: number;
  category: string;
  capabilities: Record<string, boolean>;
  roadmap_label: string | null;
}

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly detail: string | null = null,
  ) {
    super(message);
    this.name = 'ApiError';
  }

  get isClientError(): boolean {
    return this.status >= 400 && this.status < 500;
  }

  get isServerError(): boolean {
    return this.status >= 500 || this.status === 0;
  }
}
