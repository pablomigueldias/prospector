import Head from 'next/head';

import { ConfiguracoesScreen } from '@/components/config/ConfiguracoesScreen';
import { DashboardLayout } from '@/components/shared/DashboardLayout';
import { useAuth } from '@/contexts/AuthContext';

/**
 * /configuracoes (S3) — self-service. Gateado por `usuarios.gerenciar` (admin)
 * na UX; o backend é quem barra de verdade (mesma permissão no router).
 */
export default function ConfiguracoesPage() {
  const { hasPermission } = useAuth();
  const podeVer = hasPermission('usuarios.gerenciar');

  return (
    <>
      <Head>
        <title>Configurações · Reative Systems</title>
      </Head>
      <DashboardLayout currentAgentName="Configurações">
        {podeVer ? (
          <ConfiguracoesScreen />
        ) : (
          <div className="max-w-md mx-auto pt-20 text-center">
            <div className="eyebrow justify-center mb-3">Acesso negado</div>
            <h1 className="font-display font-semibold text-2xl tracking-tight text-ink mb-2">
              Configurações são só pra administradores
            </h1>
            <p className="text-[15px] text-ink-soft">
              Fale com o administrador se precisar dessa permissão.
            </p>
          </div>
        )}
      </DashboardLayout>
    </>
  );
}
