'use client';

import { useEffect, useState } from 'react';

import { api } from '@/lib/api';
import { ApiError } from '@/lib/types';
import type { CartaCandidatura, ContatoPessoal } from '@/lib/types';
import { esc, imprimirDocumento, slug, slugNome } from './_pdf';

/**
 * Carta de apresentação como DOCUMENTO pra anexar (a que muitas vagas pedem).
 * PDF gerado via "Imprimir → Salvar como PDF" — mesma mecânica do currículo.
 * Cabeçalho com nome/contato + data + referência da vaga; o corpo é o texto que
 * a IA redigiu (com saudação e assinatura), renderizado em parágrafos.
 */

const linhaContato = (c?: ContatoPessoal | null): string => {
  if (!c) return '';
  return [c.email, c.telefone, c.linkedin, c.github, c.portfolio]
    .filter(Boolean)
    .map((v) => esc(v))
    .join('  ·  ');
};

/** Vira `carta-pabloortiz-{vaga}` (sem `.pdf`; o navegador anexa). */
function nomeArquivoCarta(nome: string, vaga?: string | null): string {
  return ['carta', slugNome(nome), slug(vaga)].filter(Boolean).join('-');
}

function cartaHtml(
  carta: CartaCandidatura,
  nome: string,
  contato?: ContatoPessoal | null,
  empresa?: string | null,
  vagaTitulo?: string | null,
): string {
  const contatoLinha = linhaContato(contato);
  const hoje = new Date().toLocaleDateString('pt-BR', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  });
  const paras = String(carta.corpo)
    .trim()
    .split(/\n\s*\n/)
    .filter(Boolean)
    .map((p) => `<p>${esc(p).replace(/\n/g, '<br>')}</p>`)
    .join('');

  return `<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8" />
<title>${esc(nomeArquivoCarta(nome, vagaTitulo))}</title>
<style>
  * { box-sizing: border-box; }
  html, body { margin: 0; padding: 0; }
  body {
    font-family: Arial, Helvetica, sans-serif;
    color: #1a1a1a; font-size: 11pt; line-height: 1.5;
    margin: 0; padding: 18mm 20mm;
  }
  h1 { font-size: 20pt; margin: 0 0 2px; font-weight: 700; }
  .contato { font-size: 9.5pt; color: #333; margin: 0; }
  header { border-bottom: 1px solid #999; padding-bottom: 10px; margin-bottom: 22px; }
  .meta { color: #555; font-size: 10pt; margin: 0 0 18px; }
  .meta .dest { color: #1a1a1a; font-weight: 700; margin: 10px 0 0; }
  p { margin: 0 0 11px; text-align: justify; }
  @page { margin: 0; }
</style></head>
<body>
  <header>
    <h1>${esc(nome)}</h1>
    ${contatoLinha ? `<p class="contato">${contatoLinha}</p>` : ''}
  </header>
  <div class="meta">
    <p>${esc(hoje)}</p>
    ${empresa ? `<p class="dest">À ${esc(empresa)}</p>` : ''}
    ${vagaTitulo ? `<p>Ref.: candidatura para ${esc(vagaTitulo)}</p>` : ''}
  </div>
  ${paras}
</body></html>`;
}

export function CartaPdf({
  carta,
  nome,
  contato,
  empresa,
  vagaTitulo,
  vagaId,
  rascunhoId,
  onSalvo,
}: {
  carta: CartaCandidatura;
  nome: string;
  contato?: ContatoPessoal | null;
  empresa?: string | null;
  vagaTitulo?: string | null;
  vagaId?: string;
  rascunhoId?: string | null;
  onSalvo?: (corpo: string) => void;
}) {
  // Corpo local: edição imediata na prévia/PDF; o pai é avisado via onSalvo.
  const [corpo, setCorpo] = useState(carta.corpo);
  const [editando, setEditando] = useState(false);
  const [rascunho, setRascunho] = useState(carta.corpo);
  const [salvando, setSalvando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  // Se o pai trocar a carta (regerou), ressincroniza.
  useEffect(() => {
    setCorpo(carta.corpo);
    setRascunho(carta.corpo);
    setEditando(false);
  }, [carta.corpo]);

  const podeEditar = Boolean(vagaId && rascunhoId);

  async function salvar() {
    if (!vagaId || !rascunhoId) return;
    if (!rascunho.trim()) {
      setErro('O corpo não pode ficar vazio.');
      return;
    }
    setSalvando(true);
    setErro(null);
    try {
      const r = await api.vagaAtualizarRascunho(vagaId, rascunhoId, {
        corpo: rascunho,
      });
      setCorpo(r.corpo);
      setEditando(false);
      onSalvo?.(r.corpo);
    } catch (e) {
      setErro(e instanceof ApiError ? e.detail || e.message : 'Falha ao salvar.');
    } finally {
      setSalvando(false);
    }
  }

  return (
    <div className="card p-5">
      <div className="flex items-center justify-between gap-3 flex-wrap mb-4">
        <h4 className="font-display font-semibold text-sm text-ink m-0">
          Carta de apresentação — sob medida pra esta vaga
        </h4>
        <div className="flex items-center gap-2">
          {podeEditar && !editando && (
            <button
              type="button"
              className="btn-ghost text-[13px]"
              onClick={() => {
                setRascunho(corpo);
                setErro(null);
                setEditando(true);
              }}
            >
              ✏️ Editar
            </button>
          )}
          <button
            type="button"
            className="btn-primary"
            onClick={() =>
              imprimirDocumento(
                cartaHtml({ ...carta, corpo }, nome, contato, empresa, vagaTitulo),
                nomeArquivoCarta(nome, vagaTitulo),
              )
            }
          >
            Baixar PDF (imprimir)
          </button>
        </div>
      </div>

      {erro && (
        <div className="text-[13px] text-red-600 bg-red-50 border border-red-200 rounded p-2 mb-3">
          {erro}
        </div>
      )}

      {editando ? (
        <div className="flex flex-col gap-3">
          <textarea
            className="input resize-y min-h-[280px] text-[13px] leading-relaxed font-sans"
            value={rascunho}
            onChange={(e) => setRascunho(e.target.value)}
            autoFocus
          />
          <p className="text-[11px] text-ink-mute m-0">
            Parágrafos separados por linha em branco. O cabeçalho (nome, contato,
            data) é montado automático — edite só o texto da carta.
          </p>
          <div className="flex gap-2">
            <button
              type="button"
              className="btn-primary disabled:opacity-40"
              onClick={() => void salvar()}
              disabled={salvando || !rascunho.trim()}
            >
              {salvando ? 'Salvando…' : 'Salvar alterações'}
            </button>
            <button
              type="button"
              className="btn-ghost"
              onClick={() => {
                setRascunho(corpo);
                setEditando(false);
                setErro(null);
              }}
              disabled={salvando}
            >
              Cancelar
            </button>
          </div>
        </div>
      ) : (
        <>
          {/* Prévia fiel ao PDF */}
          <div className="curriculo-preview border border-line rounded bg-white text-ink p-6 text-[13px] leading-relaxed">
            <div className="font-display font-bold text-xl">{nome}</div>
            {linhaContato(contato) && (
              <div className="text-[12px] text-ink-mute mt-1 border-b border-line pb-3">
                {[
                  contato?.email,
                  contato?.telefone,
                  contato?.linkedin,
                  contato?.github,
                  contato?.portfolio,
                ]
                  .filter(Boolean)
                  .join('  ·  ')}
              </div>
            )}
            <div className="text-[12px] text-ink-mute mt-3">
              {new Date().toLocaleDateString('pt-BR', {
                day: 'numeric',
                month: 'long',
                year: 'numeric',
              })}
              {empresa ? ` · À ${empresa}` : ''}
              {vagaTitulo ? ` · Ref.: ${vagaTitulo}` : ''}
            </div>
            <div className="mt-4 whitespace-pre-line">{corpo}</div>
          </div>

          <p className="text-[11px] text-ink-mute mt-3">
            Anexe junto com o currículo quando a vaga pedir carta. Revise antes de
            enviar.
          </p>
        </>
      )}
    </div>
  );
}
