import { useState } from 'react';

import { useFreelaActions, useFreelaProposta } from '@/hooks/useFreela';
import {
  type FreelaChecklist,
  type FreelaKanbanItem,
  type FreelaVariacaoAbertura,
} from '@/lib/types';

// ── Modal de detalhe/edição da proposta (+ redator IA) ────────────

// Ângulo da 1ª linha (A/B) — rótulos pra UI.
const ANGULOS: { id: string; label: string }[] = [
  { id: 'direto', label: '🎯 Direto' },
  { id: 'prova', label: '🏆 Prova' },
  { id: 'pergunta', label: '❓ Pergunta' },
];
const anguloLabel = (id?: string | null) =>
  ANGULOS.find((a) => a.id === id)?.label ?? id ?? '';

export function PropostaModal({
  item,
  onClose,
  onMudou,
}: {
  item: FreelaKanbanItem;
  onClose: () => void;
  onMudou: () => void;
}) {
  const { proposta, loading, refetch } = useFreelaProposta(item.id);
  const acoes = useFreelaActions();

  const [texto, setTexto] = useState<string | null>(null);
  const [prazo, setPrazo] = useState<string | null>(null);
  const [valor, setValor] = useState<string | null>(null);
  const [liquido, setLiquido] = useState<string | null>(null);
  const [horas, setHoras] = useState<string | null>(null);
  const [instrucoes, setInstrucoes] = useState('');
  const [copiado, setCopiado] = useState(false);
  const [variacoes, setVariacoes] = useState<FreelaVariacaoAbertura[]>([]);
  const [angulo, setAngulo] = useState<string | null>(null);
  const [objecao, setObjecao] = useState('');
  const [negOpcoes, setNegOpcoes] = useState<string[]>([]);
  const [checklist, setChecklist] = useState<FreelaChecklist | null>(null);

  // valores efetivos: o que foi editado, senão o que veio do servidor
  const textoEf = texto ?? proposta?.texto_enviado ?? '';
  const prazoEf = prazo ?? proposta?.prazo_proposto ?? '';
  const valorEf = valor ?? (proposta?.valor_cotado != null ? String(proposta.valor_cotado) : '');
  const liquidoEf = liquido ?? (proposta?.valor_liquido_estimado != null ? String(proposta.valor_liquido_estimado) : '');
  const horasEf = horas ?? (proposta?.horas_estimadas != null ? String(proposta.horas_estimadas) : '');
  const anguloEf = angulo ?? proposta?.angulo_abertura ?? null;

  async function redigir() {
    const r = await acoes.redigirProposta(item.id, instrucoes || null);
    if (r) {
      setTexto(r.redacao.texto);
      setPrazo(r.redacao.prazo_sugerido ?? prazoEf);
      setVariacoes(r.redacao.variacoes_abertura || []);
      void refetch();
    }
  }

  function usarAbertura(ab: FreelaVariacaoAbertura) {
    const base = textoEf;
    const idx = base.indexOf('\n\n');
    const corpo = idx >= 0 ? base.slice(idx) : base ? `\n\n${base}` : '';
    setTexto(`${ab.texto.trim()}${corpo}`);
    setAngulo(ab.angulo); // registra o ângulo usado (A/B)
  }

  async function negociar() {
    if (!objecao.trim()) return;
    const r = await acoes.negociarProposta(item.id, objecao.trim());
    if (r) setNegOpcoes(r.opcoes);
  }

  async function conferir() {
    if (!textoEf.trim()) return;
    // salva o texto atual antes (a avaliação lê o que está persistido)
    await acoes.atualizarProposta(item.id, {
      texto_enviado: textoEf,
      prazo_proposto: prazoEf || null,
    });
    const r = await acoes.avaliarProposta(item.id);
    if (r) setChecklist(r);
  }

  async function corrigir() {
    if (!checklist) return;
    const correcoes = [
      ...checklist.itens
        .filter((i) => !i.ok)
        .map((i) => (i.nota ? `${i.criterio}: ${i.nota}` : i.criterio)),
      ...checklist.sugestoes,
      ...(checklist.alerta_conformidade
        ? ['Remova qualquer e-mail, telefone, WhatsApp ou link do texto.']
        : []),
    ];
    const r = await acoes.corrigirProposta(item.id, correcoes);
    if (r) {
      setTexto(r.redacao.texto);
      setPrazo(r.redacao.prazo_sugerido ?? prazoEf);
      setVariacoes(r.redacao.variacoes_abertura || []);
      setChecklist(null); // limpa pra você reconferir o texto corrigido
      void refetch();
    }
  }

  async function salvar() {
    await acoes.atualizarProposta(item.id, {
      texto_enviado: textoEf,
      prazo_proposto: prazoEf || null,
      valor_cotado: valorEf ? Number(valorEf) : null,
      valor_liquido_estimado: liquidoEf ? Number(liquidoEf) : null,
      horas_estimadas: horasEf ? Number(horasEf) : null,
      angulo_abertura: anguloEf,
    });
    onMudou();
    onClose();
  }

  async function copiar() {
    try {
      await navigator.clipboard.writeText(textoEf);
      setCopiado(true);
      setTimeout(() => setCopiado(false), 1500);
    } catch {
      /* clipboard pode falhar em http; ignora */
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 bg-black/40 flex items-start justify-center overflow-y-auto p-4"
      onClick={onClose}
    >
      <div
        className="card w-full max-w-[680px] my-8 p-6"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between gap-3 mb-4">
          <div className="min-w-0">
            <div className="eyebrow mb-1">Proposta</div>
            <h3 className="font-display font-semibold text-lg text-ink m-0 truncate">
              {item.projeto_titulo}
            </h3>
            {item.cliente_nome && (
              <div className="text-[13px] text-ink-mute">{item.cliente_nome}</div>
            )}
          </div>
          <button type="button" className="text-ink-mute hover:text-ink text-xl leading-none" onClick={onClose}>
            ×
          </button>
        </div>

        {loading && !proposta ? (
          <div className="text-sm text-ink-mute">Carregando…</div>
        ) : (
          <>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4 text-[13px]">
              <label className="text-ink-soft">
                Cotar (R$)
                <input className="input mt-1" type="number" value={valorEf} onChange={(e) => setValor(e.target.value)} />
              </label>
              <label className="text-ink-soft">
                Líquido (R$)
                <input className="input mt-1" type="number" value={liquidoEf} onChange={(e) => setLiquido(e.target.value)} />
              </label>
              <label className="text-ink-soft">
                Horas
                <input className="input mt-1" type="number" value={horasEf} onChange={(e) => setHoras(e.target.value)} />
              </label>
              <label className="text-ink-soft">
                Prazo
                <input className="input mt-1" value={prazoEf} onChange={(e) => setPrazo(e.target.value)} />
              </label>
            </div>

            {item.status === 'fechada' && (
              <PedirAvaliacao projeto={item.projeto_titulo} />
            )}

            {/* Destaques do seletor */}
            {(proposta?.projetos_destacados?.length || proposta?.habilidades_destacadas?.length) ? (
              <div className="mb-4 flex flex-wrap gap-1.5">
                {proposta?.projetos_destacados?.map((p) => (
                  <span key={p} className="text-[11px] px-2 py-0.5 rounded bg-brand-soft text-brand-ink">{p}</span>
                ))}
                {proposta?.habilidades_destacadas?.map((h) => (
                  <span key={h} className="text-[11px] px-2 py-0.5 rounded bg-bg-alt text-ink-soft border border-line">{h}</span>
                ))}
              </div>
            ) : null}

            {/* Redator IA */}
            <div className="rounded border border-line bg-bg-alt/50 p-3 mb-3">
              <div className="text-[13px] font-medium text-ink mb-1.5">✍️ Rascunhar com IA</div>
              <input
                className="input mb-2"
                placeholder="Instruções extra (opcional) — ex: cita teste no Safari iOS"
                value={instrucoes}
                onChange={(e) => setInstrucoes(e.target.value)}
              />
              <button type="button" className="btn-primary" onClick={redigir} disabled={acoes.loading}>
                {acoes.loading ? 'Gerando…' : proposta?.texto_enviado ? 'Regerar rascunho' : 'Gerar rascunho'}
              </button>
              {acoes.error && <div className="text-[12px] text-red-600 mt-1.5">{acoes.error.message}</div>}
            </div>

            {variacoes.length > 0 && (
              <div className="mb-3">
                <div className="text-[12px] font-medium text-ink-soft mb-1.5">
                  Aberturas alternativas (A/B) — clique pra usar e registrar o ângulo
                </div>
                <div className="flex flex-col gap-1.5">
                  {variacoes.map((ab, i) => (
                    <button
                      key={i}
                      type="button"
                      className="text-left text-[13px] text-ink-soft border border-line rounded p-2 hover:border-brand hover:bg-brand-soft/30"
                      onClick={() => usarAbertura(ab)}
                    >
                      <span className="text-[11px] font-medium text-brand-ink mr-1.5">
                        {anguloLabel(ab.angulo)}
                      </span>
                      {ab.texto}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Ângulo de abertura usado (A/B) — alimenta a métrica por ângulo */}
            <div className="flex items-center gap-2 mb-3 text-[12px]">
              <span className="text-ink-soft">Ângulo da abertura:</span>
              {ANGULOS.map((a) => (
                <button
                  key={a.id}
                  type="button"
                  className={`px-2 py-0.5 rounded border ${
                    anguloEf === a.id
                      ? 'bg-brand-soft text-brand-ink border-brand/40'
                      : 'border-line text-ink-mute hover:border-brand'
                  }`}
                  onClick={() => setAngulo(anguloEf === a.id ? null : a.id)}
                >
                  {a.label}
                </button>
              ))}
            </div>

            <label className="text-[13px] text-ink-soft">
              Texto da proposta (revise antes de enviar na Workana)
              <textarea
                className="input mt-1 min-h-[260px] font-mono text-[13px]"
                value={textoEf}
                onChange={(e) => setTexto(e.target.value)}
                placeholder="Gere com a IA ou escreva aqui…"
              />
            </label>

            {/* Gate anti-genérico */}
            <div className="rounded border border-line bg-bg-alt/50 p-3 mt-3">
              <div className="flex items-center justify-between gap-2">
                <div className="text-[13px] font-medium text-ink">
                  ✅ Conferir antes de enviar (anti-genérico)
                </div>
                <button
                  type="button"
                  className="btn-ghost text-[12px] px-2 py-1"
                  onClick={conferir}
                  disabled={acoes.loading || !textoEf.trim()}
                >
                  {acoes.loading ? 'Conferindo…' : 'Conferir proposta'}
                </button>
              </div>
              {checklist && <ChecklistView c={checklist} />}
              {checklist && checklist.selo !== 'pronta' && (
                <button
                  type="button"
                  className="btn-primary text-[12px] mt-2"
                  onClick={corrigir}
                  disabled={acoes.loading}
                >
                  {acoes.loading ? 'Corrigindo…' : '🔧 Corrigir proposta com IA'}
                </button>
              )}
            </div>

            {/* Assistente de negociação */}
            <div className="rounded border border-line bg-bg-alt/50 p-3 mt-3">
              <div className="text-[13px] font-medium text-ink mb-1.5">
                🤝 Cliente pediu desconto? Defenda o valor
              </div>
              <div className="flex gap-2">
                <input
                  className="input flex-1"
                  placeholder='O que o cliente falou — ex: "tá caro, faz por R$3000?"'
                  value={objecao}
                  onChange={(e) => setObjecao(e.target.value)}
                />
                <button type="button" className="btn-primary" onClick={negociar} disabled={acoes.loading || !objecao.trim()}>
                  {acoes.loading ? '…' : 'Sugerir'}
                </button>
              </div>
              {negOpcoes.length > 0 && (
                <div className="flex flex-col gap-1.5 mt-2">
                  {negOpcoes.map((o, i) => (
                    <button
                      key={i}
                      type="button"
                      className="text-left text-[13px] text-ink-soft border border-line rounded p-2 hover:border-brand hover:bg-brand-soft/30"
                      title="Clique pra copiar"
                      onClick={() => navigator.clipboard?.writeText(o)}
                    >
                      {o}
                    </button>
                  ))}
                </div>
              )}
            </div>

            <div className="flex items-center justify-between mt-4">
              <button type="button" className="btn-ghost text-[13px]" onClick={copiar} disabled={!textoEf}>
                {copiado ? '✓ Copiado' : 'Copiar texto'}
              </button>
              <div className="flex gap-2">
                <button type="button" className="btn-ghost" onClick={onClose}>
                  Fechar
                </button>
                <button type="button" className="btn-primary" onClick={salvar} disabled={acoes.loading}>
                  Salvar
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

function ChecklistView({ c }: { c: FreelaChecklist }) {
  const cor =
    c.selo === 'pronta'
      ? 'bg-success-soft text-success-ink'
      : c.selo === 'ajustar'
        ? 'bg-brand-soft text-brand-ink'
        : 'bg-red-100 text-red-700';
  const rotulo =
    c.selo === 'pronta' ? 'Pronta' : c.selo === 'ajustar' ? 'Dá pra melhorar' : 'Fraca';

  return (
    <div className="mt-2.5">
      <div className="flex items-center gap-2 mb-2">
        <span className={`text-[12px] font-medium px-2 py-0.5 rounded ${cor}`}>
          {rotulo}
        </span>
        <span className="font-mono text-[12px] text-ink-mute">{c.score}/100</span>
      </div>

      {c.alerta_conformidade && (
        <div className="text-[12px] text-red-700 bg-red-50 border border-red-200 rounded p-2 mb-2">
          ⚠️ {c.alerta_conformidade}
        </div>
      )}

      <ul className="flex flex-col gap-1 mb-2">
        {c.itens.map((it, i) => (
          <li key={i} className="text-[12px] flex gap-1.5">
            <span className={it.ok ? 'text-success' : 'text-red-600'}>
              {it.ok ? '✓' : '✗'}
            </span>
            <span className="text-ink-soft">
              <span className="text-ink">{it.criterio}.</span>
              {it.nota ? ` ${it.nota}` : ''}
            </span>
          </li>
        ))}
      </ul>

      {c.sugestoes.length > 0 && (
        <div className="text-[12px] text-ink-soft">
          <div className="font-medium text-ink-mute mb-0.5">Pra melhorar:</div>
          <ul className="list-disc pl-4 flex flex-col gap-0.5">
            {c.sugestoes.map((s, i) => (
              <li key={i}>{s}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function PedirAvaliacao({ projeto }: { projeto: string }) {
  const [copiado, setCopiado] = useState(false);
  const msg =
    `Foi um prazer trabalhar no projeto "${projeto}"! 🙌 ` +
    `Se você ficou satisfeito com a entrega, uma avaliação aqui na Workana me ` +
    `ajudaria muito e leva só um minuto. Qualquer ajuste, é só me chamar.`;
  async function copiar() {
    try {
      await navigator.clipboard.writeText(msg);
      setCopiado(true);
      setTimeout(() => setCopiado(false), 1500);
    } catch {
      /* ignora */
    }
  }
  return (
    <div className="rounded border border-emerald-200 bg-emerald-50 p-3 mb-4">
      <div className="text-[13px] font-medium text-emerald-800 mb-1">
        ⭐ Fechou! Peça a avaliação 5★ (a 1ª é a mais valiosa)
      </div>
      <p className="text-[13px] text-ink-soft m-0 mb-2">{msg}</p>
      <button type="button" className="btn-ghost text-[13px]" onClick={copiar}>
        {copiado ? '✓ Copiado' : 'Copiar mensagem'}
      </button>
    </div>
  );
}
