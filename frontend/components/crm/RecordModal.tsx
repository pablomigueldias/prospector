import { useState } from 'react';

import { AtividadeForm } from '@/components/crm/AtividadeForm';
import { ContatoForm } from '@/components/crm/ContatoForm';
import { InlineCell } from '@/components/crm/InlineCell';
import { NegocioForm } from '@/components/crm/NegocioForm';
import { ProjetoForm } from '@/components/crm/ProjetoForm';
import { Timeline } from '@/components/crm/Timeline';
import { SidePanel } from '@/components/shared/SidePanel';
import { useFetch } from '@/hooks/useFetch';
import { api } from '@/lib/api';
import type {
  AtividadeUpsert,
  ContatoUpsert,
  CrmFacetas,
  NegocioUpsert,
  ProjetoUpsert,
  RecordDetalhe,
  RecordTipo,
} from '@/lib/types';

type Ref = { tipo: RecordTipo; id: string };

const ROTULO: Record<RecordTipo, string> = {
  empresa: 'Empresa',
  contato: 'Contato',
  negocio: 'Negócio',
  projeto: 'Projeto',
  atividade: 'Atividade',
};

// Criar registro relacionado a partir do registro aberto (FK pré-preenchida).
type CriarIntent =
  | { form: 'contato'; inicial: Partial<ContatoUpsert>; rotulo: string }
  | { form: 'negocio'; inicial: Partial<NegocioUpsert>; rotulo: string }
  | { form: 'projeto'; inicial: Partial<ProjetoUpsert>; rotulo: string }
  | { form: 'atividade'; inicial: Partial<AtividadeUpsert>; rotulo: string };

function configCriar(
  tipo: RecordTipo,
  titulo: string,
  id: string,
): CriarIntent | null {
  switch (`${tipo}/${titulo}`) {
    case 'empresa/Contatos':
      return { form: 'contato', inicial: { empresa_id: id }, rotulo: 'contato' };
    case 'empresa/Negócios':
      return { form: 'negocio', inicial: { empresa_id: id }, rotulo: 'negócio' };
    case 'empresa/Projetos':
      return { form: 'projeto', inicial: { empresa_id: id }, rotulo: 'projeto' };
    case 'negocio/Projetos':
      return { form: 'projeto', inicial: { negocio_id: id }, rotulo: 'projeto' };
    case 'negocio/Atividades':
      return { form: 'atividade', inicial: { negocio_id: id }, rotulo: 'atividade' };
    case 'contato/Negócios':
      return { form: 'negocio', inicial: { contato_id: id }, rotulo: 'negócio' };
    case 'contato/Atividades':
      return { form: 'atividade', inicial: { contato_id: id }, rotulo: 'atividade' };
    default:
      return null;
  }
}

export function RecordModal({
  tipo,
  id,
  onClose,
  onEditar,
  onChanged,
}: {
  tipo: RecordTipo;
  id: string;
  onClose: () => void;
  onEditar?: () => void;
  /** Avisa a seção quando algo mudou aqui dentro (pra atualizar a lista/board). */
  onChanged?: () => void;
}) {
  // Pilha de navegação: o topo é o registro aberto agora.
  const [pilha, setPilha] = useState<Ref[]>([{ tipo, id }]);
  const [versao, setVersao] = useState(0);
  const [criar, setCriar] = useState<CriarIntent | null>(null);
  const atual = pilha[pilha.length - 1];

  const { data: rec, loading } = useFetch<RecordDetalhe>(
    () => api.crmRecord(atual.tipo, atual.id),
    [atual.tipo, atual.id, versao],
  );
  const { data: opcoes } = useFetch<CrmFacetas>(() => api.crmOpcoes(), []);
  const { data: cores } = useFetch(() => api.crmOpcoesCores(), []);
  const { data: empresasResp } = useFetch(
    () => api.crmEmpresas({ limit: 500, ordenar_por: 'nome' }),
    [],
  );
  const empresas = empresasResp?.items ?? [];

  const abrir = (r: Ref) => setPilha((p) => [...p, r]);
  const voltar = () => setPilha((p) => (p.length > 1 ? p.slice(0, -1) : p));
  const recarregar = () => {
    setVersao((v) => v + 1);
    onChanged?.();
  };

  return (
    <SidePanel
      open
      onClose={onClose}
      title={rec?.titulo ?? ROTULO[atual.tipo]}
      acoes={
        onEditar && pilha.length === 1 ? (
          <button
            type="button"
            className="btn-primary !px-3 !py-1.5 !text-[12px]"
            onClick={onEditar}
          >
            Editar
          </button>
        ) : undefined
      }
    >
      <div className="flex items-center gap-2 text-[12px] text-ink-mute mb-4 -mt-1">
        {pilha.length > 1 && (
          <button type="button" className="hover:text-ink" onClick={voltar}>
            ← voltar
          </button>
        )}
        <span className="uppercase tracking-wide bg-bg-alt px-1.5 py-0.5 rounded-sm">
          {ROTULO[atual.tipo]}
        </span>
      </div>

      {loading || !rec ? (
        <div className="animate-pulse h-40" />
      ) : (
        <div className="flex flex-col gap-5">
          {rec.campos.length > 0 && (
            <div className="flex flex-col text-[13px]">
              {rec.campos.map((c) => (
                <div
                  key={c.label}
                  className="grid grid-cols-[150px_1fr] items-center gap-2 py-1.5 border-b border-line/40 last:border-0"
                >
                  <span className="text-ink-mute">{c.label}</span>
                  {c.campo ? (
                    <InlineCell
                      tipo={atual.tipo}
                      id={atual.id}
                      campo={c.campo}
                      valor={c.kind === 'bool' ? c.raw === 'true' : (c.raw ?? '')}
                      display={c.valor || '—'}
                      kind={c.kind ?? 'text'}
                      opcoes={c.opcoes_key ? opcoes?.[c.opcoes_key] : undefined}
                      coresPorValor={
                        c.opcoes_key ? cores?.[c.opcoes_key] : undefined
                      }
                      onSaved={recarregar}
                    />
                  ) : (
                    <span className="text-ink break-words">{c.valor}</span>
                  )}
                </div>
              ))}
            </div>
          )}

          {rec.grupos
            .map((g) => ({ g, cfg: configCriar(atual.tipo, g.titulo, atual.id) }))
            .filter(({ g, cfg }) => g.itens.length > 0 || cfg)
            .map(({ g, cfg }) => (
              <div key={g.titulo}>
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-display font-semibold text-[13px] tracking-tight text-ink m-0">
                    {g.titulo} ({g.itens.length})
                  </h3>
                  {cfg && (
                    <button
                      type="button"
                      className="text-[12px] text-brand hover:underline"
                      onClick={() => setCriar(cfg)}
                    >
                      + {cfg.rotulo}
                    </button>
                  )}
                </div>
                <div className="flex flex-col gap-1.5">
                  {g.itens.length === 0 ? (
                    <p className="text-[12.5px] text-ink-mute m-0">
                      Nenhum ainda.
                    </p>
                  ) : (
                    g.itens.map((it) => (
                      <button
                        key={`${it.tipo}-${it.id}`}
                        type="button"
                        onClick={() => abrir({ tipo: it.tipo, id: it.id })}
                        className="flex items-center justify-between gap-2 text-left card px-3 py-2 hover:border-brand/40 transition-colors"
                      >
                        <span className="text-[13px] text-ink">{it.nome}</span>
                        <span className="text-[12px] text-ink-mute shrink-0">
                          {it.sub ?? ''} ›
                        </span>
                      </button>
                    ))
                  )}
                </div>
              </div>
            ))}

          {rec.notas && (
            <div>
              <h3 className="font-display font-semibold text-[13px] tracking-tight text-ink m-0 mb-2">
                Notas
              </h3>
              <pre className="text-[12.5px] text-ink-soft whitespace-pre-wrap font-sans m-0 leading-relaxed">
                {rec.notas}
              </pre>
            </div>
          )}

          <Timeline key={`${atual.tipo}-${atual.id}-${versao}`} tipo={atual.tipo} id={atual.id} />
        </div>
      )}

      {criar?.form === 'contato' && (
        <ContatoForm
          inicial={criar.inicial}
          empresas={empresas}
          onClose={() => setCriar(null)}
          onSaved={recarregar}
        />
      )}
      {criar?.form === 'negocio' && (
        <NegocioForm
          inicial={criar.inicial}
          onClose={() => setCriar(null)}
          onSaved={recarregar}
        />
      )}
      {criar?.form === 'projeto' && (
        <ProjetoForm
          inicial={criar.inicial}
          onClose={() => setCriar(null)}
          onSaved={recarregar}
        />
      )}
      {criar?.form === 'atividade' && (
        <AtividadeForm
          inicial={criar.inicial}
          onClose={() => setCriar(null)}
          onSaved={recarregar}
        />
      )}
    </SidePanel>
  );
}
