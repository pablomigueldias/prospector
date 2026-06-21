import Head from 'next/head';

import { CockpitScreen } from '@/components/cockpit/CockpitScreen';
import { DashboardLayout } from '@/components/shared/DashboardLayout';

/**
 * Home = Central de Agentes (cockpit, S1). É pra cá que o login leva e onde o
 * logo do menu aponta. A proteção de auth é global (AuthContext redireciona
 * quem não está logado pra /login).
 */
export default function Home() {
  return (
    <>
      <Head>
        <title>Central de Agentes · Reative Systems</title>
      </Head>
      <DashboardLayout currentAgentName="Central de Agentes">
        <CockpitScreen />
      </DashboardLayout>
    </>
  );
}
