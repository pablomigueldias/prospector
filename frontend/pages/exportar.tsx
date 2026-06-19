import Head from 'next/head';

import { ExportarScreen } from '@/components/exportar/ExportarScreen';
import { DashboardLayout } from '@/components/shared/DashboardLayout';
import { useAuth } from '@/contexts/AuthContext';

/**
 * /exportar (S8) — export/backup. Gateado por `usuarios.gerenciar` (admin).
 */
export default function ExportarPage() {
  const { hasPermission } = useAuth();
  const podeVer = hasPermission('usuarios.gerenciar');

  return (
    <>
      <Head>
        <title>Export / Backup · Reative Systems</title>
      </Head>
      <DashboardLayout currentAgentName="Export / Backup">
        {podeVer ? (
          <ExportarScreen />
        ) : (
          <div className="max-w-md mx-auto pt-20 text-center">
            <div className="eyebrow justify-center mb-3">Acesso negado</div>
            <h1 className="font-display font-semibold text-2xl tracking-tight text-ink mb-2">
              Export é só pra administradores
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
