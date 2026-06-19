import { useState } from 'react';

import { pilulaCor } from '@/components/crm/_crmShared';
import { SidePanel } from '@/components/shared/SidePanel';
import { useFetch } from '@/hooks/useFetch';
import { api } from '@/lib/api';
import type { CrmOpcao } from '@/lib/types';

// Rótulos amigáveis e ordem de exibição dos grupos.
const GRUPOS: { grupo: string; label: string }[] = [
  { grupo: 'status', label: 'Status (empresa)' },
  { grupo: 'setor', label: 'Setor (empresa)' },
  { grupo: 'tamanho', label: 'Tamanho (empresa)' },
  { grupo: 'como_conheceu', label: 'Como conheceu (empresa)' },
  { grupo: 'estado', label: 'Estado (empresa)' },
  { grupo: 'origem_contato', label: 'Origem (contato)' },
  { grupo: 'estagio', label: 'Estágio (negócio)' },
  { grupo: 'probabilidade', label: 'Probabilidade (negócio)' },
  { grupo: 'origem_negocio', label: 'Origem (negócio)' },
  { grupo: 'tipo_servico', label: 'Tipo de serviço' },
  { grupo: 'atividade_status', label: 'Status (atividade)' },
  { grupo: 'atividade_tipo', label: 'Tipo (atividade)' },
  { grupo: 'projeto_status', label: 'Status (projeto)' },
  { grupo: 'forma_pagamento', label: 'Forma de pagamento (projeto)' },
];

const PALETA: { token: string; classe: string }[] = [
  { token: '', classe: 'bg-bg-alt border-line' },
  { token: 'red', classe: 'bg-red-200 border-red-300' },
  { token: 'orange', classe: 'bg-orange-200 border-orange-300' },
  { token: 'yellow', classe: 'bg-yellow-200 border-yellow-300' },
  { token: 'green', classe: 'bg-green-200 border-green-300' },
  { token: 'blue', classe: 'bg-blue-200 border-blue-300' },
  { token: 'purple', classe: 'bg-purple-200 border-purple-300' },
  { token: 'gray', classe: 'bg-gray-300 border-gray-400' },
];

export function OpcoesManager({ onClose }: { onClose: () => void }) {
  const [versao, setVersao] = useState(0);
  const { data, loading } = useFetch(() => api.crmOpcoesGerenciar(), [versao]);
  const recarregar = () => setVersao((v) => v + 1);

  const porGrupo = (g: string) =>
    (data ?? []).filter((o) => o.grupo === g).sort((a, b) => a.ordem - b.ordem);

  return (
    <SidePanel open onClose={onClose} title="Configurar opções dos selects">
      <p className="text-[13px] text-ink-soft mt-0 mb-5 leading-relaxed">
        As opções abaixo alimentam os dropdowns coloridos do CRM. Renomear uma
        opção atualiza os registros que já a usam.
      </p>
      {loading && !data ? (
        <div className="animate-pulse h-40" />
      ) : (
        <div className="flex flex-col gap-7">
          {GRUPOS.map(({ grupo, label }) => (
            <Grupo
              key={grupo}
              grupo={grupo}
              label={label}
              opcoes={porGrupo(grupo)}
              onMudou={recarregar}
            />
          ))}
        </div>
      )}
    </SidePanel>
  );
}

function Grupo({
  grupo,
  label,
  opcoes,
  onMudou,
}: {
  grupo: string;
  label: string;
  opcoes: CrmOpcao[];
  onMudou: () => void;
}) {
  const [novo, setNovo] = useState('');
  const [add, setAdd] = useState(false);

  async function adicionar() {
    const v = novo.trim();
    if (!v) return;
    setNovo('');
    setAdd(false);
    await api.crmOpcaoCriar({ grupo, valor: v });
    onMudou();
  }

  async function mover(idx: number, delta: number) {
    const alvo = idx + delta;
    if (alvo < 0 || alvo >= opcoes.length) return;
    const ids = opcoes.map((o) => o.id);
    [ids[idx], ids[alvo]] = [ids[alvo], ids[idx]];
    await api.crmOpcoesReordenar(grupo, ids);
    onMudou();
  }

  return (
    <section>
      <h3 className="font-display font-semibold text-[13.5px] tracking-tight text-ink m-0 mb-2.5">
        {label}
      </h3>
      <div className="flex flex-col gap-1.5">
        {opcoes.map((o, i) => (
          <OpcaoRow
            key={o.id}
            opcao={o}
            primeiro={i === 0}
            ultimo={i === opcoes.length - 1}
            onSubir={() => mover(i, -1)}
            onDescer={() => mover(i, 1)}
            onMudou={onMudou}
          />
        ))}
      </div>
      {add ? (
        <div className="flex items-center gap-2 mt-2">
          <input
            autoFocus
            className="input !py-1 !text-[13px] max-w-[260px]"
            placeholder="Nova opção…"
            value={novo}
            onChange={(e) => setNovo(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') adicionar();
              else if (e.key === 'Escape') {
                setNovo('');
                setAdd(false);
              }
            }}
            onBlur={adicionar}
          />
        </div>
      ) : (
        <button
          type="button"
          className="text-[12.5px] text-brand hover:underline mt-2"
          onClick={() => setAdd(true)}
        >
          + adicionar opção
        </button>
      )}
    </section>
  );
}

function OpcaoRow({
  opcao,
  primeiro,
  ultimo,
  onSubir,
  onDescer,
  onMudou,
}: {
  opcao: CrmOpcao;
  primeiro: boolean;
  ultimo: boolean;
  onSubir: () => void;
  onDescer: () => void;
  onMudou: () => void;
}) {
  const [mostraCores, setMostraCores] = useState(false);

  async function salvarValor(v: string) {
    const novo = v.trim();
    if (!novo || novo === opcao.valor) return;
    await api.crmOpcaoAtualizar(opcao.id, { valor: novo });
    onMudou();
  }
  async function setCor(cor: string) {
    setMostraCores(false);
    await api.crmOpcaoAtualizar(opcao.id, { cor: cor || null });
    onMudou();
  }
  async function toggleAtivo() {
    await api.crmOpcaoAtualizar(opcao.id, { ativo: !opcao.ativo });
    onMudou();
  }
  async function excluir() {
    await api.crmOpcaoExcluir(opcao.id);
    onMudou();
  }

  return (
    <div
      className={`flex items-center gap-1.5 ${opcao.ativo ? '' : 'opacity-45'}`}
    >
      {/* swatch / color picker */}
      <div className="relative">
        <button
          type="button"
          onClick={() => setMostraCores((m) => !m)}
          title="Cor"
          className={`w-4 h-4 rounded-full border shrink-0 ${
            PALETA.find((p) => p.token === (opcao.cor ?? ''))?.classe ??
            'bg-bg-alt border-line'
          }`}
        />
        {mostraCores && (
          <div className="absolute z-10 mt-1 left-0 flex gap-1 p-1.5 card shadow-lg">
            {PALETA.map((p) => (
              <button
                key={p.token || 'none'}
                type="button"
                onClick={() => setCor(p.token)}
                className={`w-4 h-4 rounded-full border ${p.classe}`}
              />
            ))}
          </div>
        )}
      </div>

      <span
        className={`text-[11px] px-2 py-0.5 rounded-full ${pilulaCor(opcao.cor)}`}
      >
        <input
          defaultValue={opcao.valor}
          key={opcao.valor}
          className="bg-transparent outline-none w-[180px]"
          onKeyDown={(e) => {
            if (e.key === 'Enter') (e.target as HTMLInputElement).blur();
          }}
          onBlur={(e) => salvarValor(e.target.value)}
        />
      </span>

      <div className="ml-auto flex items-center gap-0.5 text-ink-mute">
        <button
          type="button"
          disabled={primeiro}
          onClick={onSubir}
          className="px-1 hover:text-ink disabled:opacity-25"
          title="Subir"
        >
          ↑
        </button>
        <button
          type="button"
          disabled={ultimo}
          onClick={onDescer}
          className="px-1 hover:text-ink disabled:opacity-25"
          title="Descer"
        >
          ↓
        </button>
        <button
          type="button"
          onClick={toggleAtivo}
          className="px-1 hover:text-ink text-[12px]"
          title={opcao.ativo ? 'Desativar' : 'Ativar'}
        >
          {opcao.ativo ? '👁' : '🚫'}
        </button>
        <button
          type="button"
          onClick={excluir}
          className="px-1 hover:text-red-600 text-[12px]"
          title="Excluir"
        >
          ✕
        </button>
      </div>
    </div>
  );
}
