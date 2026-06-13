import { useCallback, useRef, useState } from 'react';

import { useCategorias } from '@/hooks/useFinancas';
import { api } from '@/lib/api';
import { achatarCategorias } from '@/lib/categorias';
import { formatBRL } from '@/lib/format';
import { ApiError } from '@/lib/types';
import type { ImportarBoletoResponse } from '@/lib/types';

const ACEITA = 'application/pdf,image/*';

interface Props {
  /** Chamado quando o boleto vira despesa (pra recarregar resumo/contas). */
  onImportado?: () => void;
}

/**
 * Importar boleto pela web — arraste (ou escolha) um boleto em PDF/foto, a IA
 * lê e, se as verbas batem com o total, já cria a despesa prevista. Replica o
 * "boleto por foto" do bot do Telegram no desktop.
 */
export function ImportarBoletoSection({ onImportado }: Props) {
  const { arvore } = useCategorias();
  const categorias = achatarCategorias(arvore);

  const [categoriaId, setCategoriaId] = useState('');
  const [arrastando, setArrastando] = useState(false);
  const [enviando, setEnviando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);
  const [resultado, setResultado] = useState<ImportarBoletoResponse | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const enviar = useCallback(
    async (file: File) => {
      setEnviando(true);
      setErro(null);
      setResultado(null);
      try {
        const r = await api.financasImportarBoleto(file, categoriaId || undefined);
        setResultado(r);
        if (r.conferido) onImportado?.();
      } catch (e) {
        setErro(e instanceof ApiError ? e.message : 'Falha ao importar o boleto.');
      } finally {
        setEnviando(false);
      }
    },
    [categoriaId, onImportado],
  );

  const aoSoltar = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setArrastando(false);
      const file = e.dataTransfer.files?.[0];
      if (file) void enviar(file);
    },
    [enviar],
  );

  return (
    <div className="grid gap-4 md:grid-cols-[1fr_320px]">
      {/* Zona de upload */}
      <div>
        <div
          onDragOver={(e) => {
            e.preventDefault();
            setArrastando(true);
          }}
          onDragLeave={() => setArrastando(false)}
          onDrop={aoSoltar}
          onClick={() => !enviando && inputRef.current?.click()}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => {
            if ((e.key === 'Enter' || e.key === ' ') && !enviando) {
              e.preventDefault();
              inputRef.current?.click();
            }
          }}
          className={[
            'card flex flex-col items-center justify-center gap-2 text-center px-6 py-10 cursor-pointer transition-colors',
            arrastando ? 'border-brand bg-brand-soft' : 'hover:border-brand',
            enviando ? 'pointer-events-none opacity-60' : '',
          ].join(' ')}
        >
          <input
            ref={inputRef}
            type="file"
            accept={ACEITA}
            className="hidden"
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) void enviar(file);
              e.target.value = '';
            }}
          />
          <div className="text-3xl leading-none">{enviando ? '⏳' : '🧾'}</div>
          <div className="text-[15px] text-ink font-medium">
            {enviando ? 'Lendo o boleto…' : 'Arraste um boleto aqui'}
          </div>
          <div className="text-[12.5px] text-ink-soft">
            {enviando
              ? 'A IA está extraindo as verbas — pode levar alguns segundos.'
              : 'ou clique pra escolher um PDF ou foto'}
          </div>
        </div>

        {erro && (
          <div className="mt-3 text-[13px] text-red-600">{erro}</div>
        )}

        {resultado && <ResultadoBoleto resultado={resultado} />}
      </div>

      {/* Categoria opcional */}
      <div className="card p-4 h-fit">
        <label className="block text-[12.5px] text-ink-soft mb-1.5">
          Categoria (opcional)
        </label>
        <select
          value={categoriaId}
          onChange={(e) => setCategoriaId(e.target.value)}
          disabled={enviando}
          className="input w-full"
        >
          <option value="">Deixar a IA decidir / sem categoria</option>
          {categorias.map((c) => (
            <option key={c.id} value={c.id}>
              {'  '.repeat(c.depth)}
              {c.nome}
            </option>
          ))}
        </select>
        <p className="mt-2 text-[12px] text-ink-mute leading-relaxed">
          Se as verbas baterem com o total, o boleto já vira uma despesa{' '}
          <strong>prevista</strong> (a pagar). Senão, fica guardado pra revisão.
        </p>
      </div>
    </div>
  );
}

function ResultadoBoleto({ resultado: r }: { resultado: ImportarBoletoResponse }) {
  const ok = r.conferido;
  const criou = !!r.transacao_id; // virou conta a pagar (com ou sem verbas)
  // 3 estados: ✅ conferido | ⚠️ a pagar sem separar verbas | ⛔ não criou
  const titulo = ok
    ? 'Despesa criada'
    : criou
      ? 'Lançado como a pagar'
      : 'Revisão manual';
  const icone = ok ? '✅' : criou ? '⚠️' : '⛔';
  return (
    <div
      className={[
        'card mt-4 p-4 border-l-4',
        ok ? 'border-l-success' : criou ? 'border-l-amber-500' : 'border-l-line',
      ].join(' ')}
    >
      <div className="flex items-center gap-2 mb-1">
        <span className="text-lg leading-none">{icone}</span>
        <strong className="text-[14px] text-ink">{titulo}</strong>
      </div>
      <p className="text-[13px] text-ink-soft m-0">{r.mensagem}</p>

      {r.extraido && (
        <div className="mt-3 border-t border-line-soft pt-3">
          <div className="flex justify-between text-[13px] mb-2">
            <span className="text-ink-soft">
              {r.extraido.beneficiario || 'Boleto'}
              {r.extraido.vencimento && (
                <span className="text-ink-mute">
                  {' '}· vence {r.extraido.vencimento}
                </span>
              )}
            </span>
            <strong className="text-ink">{formatBRL(r.extraido.valor_total)}</strong>
          </div>
          {r.extraido.verbas.length > 0 && (
            <ul className="space-y-1">
              {r.extraido.verbas.map((v, i) => (
                <li key={i} className="flex justify-between text-[12.5px] text-ink-soft">
                  <span className="truncate pr-2">{v.descricao}</span>
                  <span className="font-mono">{formatBRL(v.valor)}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
