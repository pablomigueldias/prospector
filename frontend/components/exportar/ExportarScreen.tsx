import { useState } from 'react';

import { API_URL } from '@/lib/api';

/**
 * S8 — Export / Backup pela tela. Botões que baixam cada domínio em CSV ou um
 * backup JSON com tudo. Usa fetch com credenciais (cookie de sessão) + blob,
 * porque é download autenticado (não dá pra ser um <a href> simples cross-origin).
 */
const RECURSOS: { slug: string; label: string }[] = [
  { slug: 'empresas', label: 'Empresas' },
  { slug: 'contatos', label: 'Contatos' },
  { slug: 'negocios', label: 'Negócios' },
  { slug: 'vagas', label: 'Vagas' },
  { slug: 'transacoes', label: 'Transações' },
];

export function ExportarScreen() {
  const [baixando, setBaixando] = useState<string | null>(null);
  const [erro, setErro] = useState<string | null>(null);

  async function baixar(path: string, filename: string, chave: string) {
    setBaixando(chave);
    setErro(null);
    try {
      const res = await fetch(`${API_URL}${path}`, { credentials: 'include' });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Falha no download.');
    } finally {
      setBaixando(null);
    }
  }

  const hoje = new Date().toISOString().slice(0, 10);

  return (
    <div className="flex flex-col gap-6 max-w-2xl">
      <header>
        <div className="eyebrow mb-2">Self-service</div>
        <h1 className="font-display font-semibold text-2xl tracking-tight text-ink m-0">
          Export / Backup
        </h1>
        <p className="text-[15px] text-ink-soft mt-1 mb-0 max-w-[60ch]">
          Leve seus dados pra fora quando quiser — CSV por domínio ou um backup
          JSON com tudo.
        </p>
      </header>

      <section className="card p-5">
        <h2 className="font-display font-semibold text-[15px] tracking-tight text-ink mt-0 mb-3">
          Exportar CSV
        </h2>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
          {RECURSOS.map((r) => (
            <button
              key={r.slug}
              type="button"
              className="btn-ghost justify-center"
              disabled={baixando !== null}
              onClick={() =>
                baixar(`/api/export/csv/${r.slug}`, `${r.slug}-${hoje}.csv`, r.slug)
              }
            >
              {baixando === r.slug ? 'Baixando…' : r.label}
            </button>
          ))}
        </div>
      </section>

      <section className="card p-5">
        <h2 className="font-display font-semibold text-[15px] tracking-tight text-ink mt-0 mb-1">
          Backup completo
        </h2>
        <p className="text-[13px] text-ink-mute mt-0 mb-3">
          Um JSON com todos os domínios acima. Bom pra guardar uma cópia sua.
        </p>
        <button
          type="button"
          className="btn-primary"
          disabled={baixando !== null}
          onClick={() =>
            baixar('/api/export/backup', `backup-${hoje}.json`, 'backup')
          }
        >
          {baixando === 'backup' ? 'Gerando…' : 'Backup agora'}
        </button>
      </section>

      {erro && <p className="text-[13px] text-red-600 m-0">{erro}</p>}
    </div>
  );
}
