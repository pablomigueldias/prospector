// Cliente da API, organizado por domínio (vertical slices) sobre um `request`
// compartilhado (client.ts). O objeto `api` é plano — composto pela união dos
// módulos — então `import { api } from '@/lib/api'` e `api.financasContas(...)`
// seguem funcionando igual.

import { coreApi } from './core';
import { prospectorApi } from './prospector';
import { configApi } from './config';
import { agendamentosApi } from './agendamentos';
import { observabilidadeApi } from './observabilidade';
import { crmApi } from './crm';
import { outreachApi } from './outreach';
import { pessoalApi } from './pessoal';
import { freelaApi } from './freela';
import { financasApi } from './financas';
import { blogApi } from './blog';
import { authApi } from './auth';

export { API_URL } from './client';

export const api = {
  ...coreApi,
  ...prospectorApi,
  ...configApi,
  ...agendamentosApi,
  ...observabilidadeApi,
  ...crmApi,
  ...outreachApi,
  ...pessoalApi,
  ...freelaApi,
  ...financasApi,
  ...blogApi,
  ...authApi,
};
