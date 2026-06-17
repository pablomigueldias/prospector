import Head from 'next/head';
import { useCallback, useEffect, useState, type FormEvent } from 'react';

import { DashboardLayout } from '@/components/shared/DashboardLayout';
import { useAuth } from '@/contexts/AuthContext';
import { api } from '@/lib/api';
import { ApiError, type PapelItem, type UsuarioAdminItem } from '@/lib/types';

export default function AdminUsuariosPage() {
  const { hasPermission } = useAuth();
  const pode = hasPermission('usuarios.gerenciar');

  const [usuarios, setUsuarios] = useState<UsuarioAdminItem[]>([]);
  const [papeis, setPapeis] = useState<PapelItem[]>([]);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState('');

  // form de criação
  const [email, setEmail] = useState('');
  const [nome, setNome] = useState('');
  const [senha, setSenha] = useState('');
  const [novoPapeis, setNovoPapeis] = useState<string[]>(['padrao']);
  const [criando, setCriando] = useState(false);
  const [msg, setMsg] = useState<{ tipo: 'ok' | 'erro'; texto: string } | null>(null);

  const carregar = useCallback(async () => {
    setCarregando(true);
    setErro('');
    try {
      const [us, ps] = await Promise.all([
        api.adminListarUsuarios(),
        api.adminListarPapeis(),
      ]);
      setUsuarios(us.items);
      setPapeis(ps);
    } catch (e) {
      setErro(e instanceof ApiError ? e.message : 'Falha ao carregar.');
    } finally {
      setCarregando(false);
    }
  }, []);

  useEffect(() => {
    if (pode) void carregar();
    else setCarregando(false);
  }, [pode, carregar]);

  async function criar(e: FormEvent) {
    e.preventDefault();
    setMsg(null);
    setCriando(true);
    try {
      await api.adminCriarUsuario({ email: email.trim(), nome: nome.trim(), senha, papeis: novoPapeis });
      setMsg({ tipo: 'ok', texto: `Usuário ${email} criado.` });
      setEmail('');
      setNome('');
      setSenha('');
      setNovoPapeis(['padrao']);
      await carregar();
    } catch (err) {
      setMsg({ tipo: 'erro', texto: err instanceof ApiError ? err.message : 'Falha ao criar.' });
    } finally {
      setCriando(false);
    }
  }

  async function alterar(id: string, body: { ativo?: boolean; papeis?: string[] }) {
    try {
      await api.adminAtualizarUsuario(id, body);
      await carregar();
    } catch (err) {
      setMsg({ tipo: 'erro', texto: err instanceof ApiError ? err.message : 'Falha ao salvar.' });
    }
  }

  function togglePapelNovo(p: string) {
    setNovoPapeis((atual) =>
      atual.includes(p) ? atual.filter((x) => x !== p) : [...atual, p],
    );
  }

  function togglePapelUsuario(u: UsuarioAdminItem, p: string) {
    const novos = u.papeis.includes(p)
      ? u.papeis.filter((x) => x !== p)
      : [...u.papeis, p];
    void alterar(u.id, { papeis: novos });
  }

  if (!pode) {
    return (
      <DashboardLayout currentAgentName="Usuários">
        <div className="max-w-md mx-auto pt-20 text-center">
          <div className="eyebrow justify-center mb-3">Acesso negado</div>
          <h1 className="font-display font-semibold text-2xl text-ink">
            Só administradores podem gerenciar usuários
          </h1>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <>
      <Head>
        <title>Usuários · Reative Systems</title>
      </Head>
      <DashboardLayout currentAgentName="Usuários">
        <div className="max-w-4xl mx-auto">
          <header className="mb-7">
            <div className="eyebrow mb-3">Admin</div>
            <h1 className="font-display font-semibold text-3xl tracking-tight text-ink">
              Usuários
            </h1>
          </header>

          {/* Criar */}
          <section className="card p-6 mb-6">
            <h2 className="font-display font-semibold text-lg text-ink mb-4">Novo usuário</h2>
            <form onSubmit={criar} className="grid sm:grid-cols-2 gap-4">
              <label className="flex flex-col gap-1.5">
                <span className="text-xs font-medium text-ink-mute">Email</span>
                <input type="email" className="input" value={email}
                       onChange={(e) => setEmail(e.target.value)} required />
              </label>
              <label className="flex flex-col gap-1.5">
                <span className="text-xs font-medium text-ink-mute">Nome</span>
                <input className="input" value={nome}
                       onChange={(e) => setNome(e.target.value)} required />
              </label>
              <label className="flex flex-col gap-1.5 sm:col-span-2">
                <span className="text-xs font-medium text-ink-mute">
                  Senha inicial (mín. 12 caracteres)
                </span>
                <input type="password" className="input" autoComplete="new-password"
                       value={senha} onChange={(e) => setSenha(e.target.value)} required />
              </label>
              <div className="sm:col-span-2 flex flex-wrap gap-3">
                {papeis.map((p) => (
                  <label key={p.nome} className="flex items-center gap-1.5 text-sm text-ink-soft">
                    <input type="checkbox" checked={novoPapeis.includes(p.nome)}
                           onChange={() => togglePapelNovo(p.nome)} />
                    {p.nome}
                  </label>
                ))}
              </div>
              {msg && (
                <p className={`sm:col-span-2 text-sm ${msg.tipo === 'ok' ? 'text-success-ink' : 'text-red-600'}`}>
                  {msg.texto}
                </p>
              )}
              <div className="sm:col-span-2">
                <button type="submit" className="btn-primary" disabled={criando}>
                  {criando ? 'Criando…' : 'Criar usuário'}
                </button>
              </div>
            </form>
          </section>

          {/* Lista */}
          <section className="card p-0 overflow-hidden">
            {carregando && <div className="p-6 text-ink-mute text-sm">Carregando…</div>}
            {erro && <div className="p-6 text-red-600 text-sm">{erro}</div>}
            {!carregando && !erro && (
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-ink-mute border-b border-line">
                    <th className="p-3 font-medium">Usuário</th>
                    <th className="p-3 font-medium">Papéis</th>
                    <th className="p-3 font-medium">Ativo</th>
                  </tr>
                </thead>
                <tbody>
                  {usuarios.map((u) => (
                    <tr key={u.id} className="border-b border-line-soft last:border-0">
                      <td className="p-3">
                        <div className="font-medium text-ink">{u.nome}</div>
                        <div className="text-ink-mute text-[12px]">{u.email}</div>
                      </td>
                      <td className="p-3">
                        <div className="flex flex-wrap gap-2.5">
                          {papeis.map((p) => (
                            <label key={p.nome} className="flex items-center gap-1 text-[12.5px] text-ink-soft">
                              <input type="checkbox" checked={u.papeis.includes(p.nome)}
                                     onChange={() => togglePapelUsuario(u, p.nome)} />
                              {p.nome}
                            </label>
                          ))}
                        </div>
                      </td>
                      <td className="p-3">
                        <button
                          type="button"
                          onClick={() => void alterar(u.id, { ativo: !u.ativo })}
                          className={`text-[12px] font-medium px-2 py-1 rounded-sm ${
                            u.ativo ? 'bg-success-ink/10 text-success-ink' : 'bg-bg-alt text-ink-mute'
                          }`}
                        >
                          {u.ativo ? 'ativo' : 'inativo'}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </section>
        </div>
      </DashboardLayout>
    </>
  );
}
