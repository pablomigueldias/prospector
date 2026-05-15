import { useMemo } from 'react';

import { useFetch } from './useFetch';
import { api } from '@/lib/api';
import type { Agent } from '@/lib/types';

export function useAgents() {
  const result = useFetch<Agent[]>((signal) => {
    return api.listAgents();
  }, []);

  const grouped = useMemo(() => {
    if (!result.data) return {};
    return result.data.reduce<Record<string, Agent[]>>((acc, agent) => {
      const cat = agent.category || 'Agentes';
      if (!acc[cat]) acc[cat] = [];
      acc[cat].push(agent);
      return acc;
    }, {});
  }, [result.data]);

  const activeAgents = useMemo(
    () => result.data?.filter((a) => a.status === 'active') ?? [],
    [result.data],
  );

  return { ...result, agents: result.data ?? [], grouped, activeAgents };
}

export function useAgent(slug: string | undefined) {
  const result = useFetch<Agent>(
    () => {
      if (!slug) {
        return Promise.reject(new Error('slug não informado'));
      }
      return api.getAgent(slug);
    },
    [slug],
  );

  return { ...result, agent: result.data };
}
