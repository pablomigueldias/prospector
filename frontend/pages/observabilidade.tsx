import Head from 'next/head';

import { ObservabilidadeScreen } from '@/components/observabilidade/ObservabilidadeScreen';
import { DashboardLayout } from '@/components/shared/DashboardLayout';
import { useAuth } from '@/contexts/AuthContext';

/**
 * /observabilidade (S2) — custos/erros de IA. Gateado por `usuarios.gerenciar`
 * (admin) na UX.
 */
export default function ObservabilidadePage() {
  const { hasPermission } = useAuth();
  const podeVer = hasPermission('usuarios.gerenciar');

  return (
    <>
      <Head>
        <title>Observabilidade · Reative Systems</title>
      </Head>
      <DashboardLayout currentAgentName="Observabilidade">
        {podeVer ? (
          <ObservabilidadeScreen />
        ) : (
          <div className="max-w-md mx-auto pt-20 text-center">
            <div className="eyebrow justify-center mb-3">Acesso negado</div>
            <h1 className="font-display font-semibold text-2xl tracking-tight text-ink mb-2">
              Observabilidade é só pra administradores
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
