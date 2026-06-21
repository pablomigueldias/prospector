import Head from 'next/head';

import { AgendamentosScreen } from '@/components/agendamentos/AgendamentosScreen';
import { DashboardLayout } from '@/components/shared/DashboardLayout';
import { useAuth } from '@/contexts/AuthContext';

/**
 * /agendamentos (S4) — self-service dos jobs. Gateado por `usuarios.gerenciar`
 * (admin) na UX; o backend barra de verdade (mesma permissão no router).
 */
export default function AgendamentosPage() {
  const { hasPermission } = useAuth();
  const podeVer = hasPermission('usuarios.gerenciar');

  return (
    <>
      <Head>
        <title>Agendamentos · Reative Systems</title>
      </Head>
      <DashboardLayout currentAgentName="Agendamentos">
        {podeVer ? (
          <AgendamentosScreen />
        ) : (
          <div className="max-w-md mx-auto pt-20 text-center">
            <div className="eyebrow justify-center mb-3">Acesso negado</div>
            <h1 className="font-display font-semibold text-2xl tracking-tight text-ink mb-2">
              Agendamentos são só pra administradores
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
