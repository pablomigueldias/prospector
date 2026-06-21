import { useState } from 'react';

import { AtividadesSection } from '@/components/crm/AtividadesSection';
import { ContatosSection } from '@/components/crm/ContatosSection';
import { DashboardSection } from '@/components/crm/DashboardSection';
import { EmpresasSection } from '@/components/crm/EmpresasSection';
import { NegociosSection } from '@/components/crm/NegociosSection';
import { OpcoesManager } from '@/components/crm/OpcoesManager';
import { ProjetosSection } from '@/components/crm/ProjetosSection';

type Secao =
  | 'dashboard'
  | 'empresas'
  | 'contatos'
  | 'negocios'
  | 'atividades'
  | 'projetos';

const SECOES: { id: Secao; label: string }[] = [
  { id: 'dashboard', label: 'Visão geral' },
  { id: 'empresas', label: 'Empresas' },
  { id: 'contatos', label: 'Contatos' },
  { id: 'negocios', label: 'Negócios' },
  { id: 'atividades', label: 'Atividades' },
  { id: 'projetos', label: 'Projetos' },
];

export default function CrmScreen() {
  const [secao, setSecao] = useState<Secao>('dashboard');
  const [versaoDados, setVersaoDados] = useState(0);
  const [opcoesAberto, setOpcoesAberto] = useState(false);
  // Bump pra forçar o dashboard/seções a recarregarem após CRUD.
  const recarregarMetricas = () => setVersaoDados((v) => v + 1);

  return (
    <div className="max-w-[1280px] mx-auto pb-16">
      <header className="mb-6 flex items-start justify-between gap-4">
        <div>
          <div className="eyebrow mb-3">Reative · CRM</div>
          <h1 className="font-display font-semibold text-[38px] leading-[1.05] tracking-tighter text-ink m-0 mb-2.5">
            CRM
          </h1>
          <p className="text-[15px] text-ink-soft max-w-[60ch] leading-relaxed m-0">
            Empresas, contatos e pipeline dentro do sistema — tudo editável direto
            no Postgres. Esta é a fonte única; o Notion ficou pra trás.
          </p>
        </div>
        <div className="flex flex-col items-end gap-1.5 shrink-0">
          <button
            type="button"
            className="btn-ghost !px-4 !py-2 !text-[13px]"
            onClick={() => setOpcoesAberto(true)}
          >
            ⚙ Opções
          </button>
        </div>
      </header>

      {/* Navegação das seções */}
      <div className="flex gap-1 border-b border-line mb-6 overflow-x-auto">
        {SECOES.map((s) => (
          <button
            key={s.id}
            type="button"
            onClick={() => setSecao(s.id)}
            className={`px-4 py-2.5 text-[13.5px] font-medium border-b-2 -mb-px whitespace-nowrap transition-colors ${
              secao === s.id
                ? 'border-brand text-brand'
                : 'border-transparent text-ink-soft hover:text-ink'
            }`}
          >
            {s.label}
          </button>
        ))}
      </div>

      {secao === 'dashboard' && <DashboardSection key={versaoDados} />}
      {secao === 'empresas' && (
        <EmpresasSection onChanged={recarregarMetricas} />
      )}
      {secao === 'contatos' && (
        <ContatosSection onChanged={recarregarMetricas} />
      )}
      {secao === 'negocios' && <NegociosSection />}
      {secao === 'atividades' && <AtividadesSection />}
      {secao === 'projetos' && <ProjetosSection />}

      {opcoesAberto && <OpcoesManager onClose={() => setOpcoesAberto(false)} />}
    </div>
  );
}
