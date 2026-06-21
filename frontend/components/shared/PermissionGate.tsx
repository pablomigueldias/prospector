import type { ReactNode } from 'react';

import { useAuth } from '@/contexts/AuthContext';

/**
 * Só renderiza os filhos se o usuário logado tiver a permissão ``need``.
 * Puramente UX — o backend é quem barra de verdade (require_permission).
 */
export function PermissionGate({
  need,
  children,
  fallback = null,
}: {
  need: string;
  children: ReactNode;
  fallback?: ReactNode;
}) {
  const { hasPermission } = useAuth();
  return <>{hasPermission(need) ? children : fallback}</>;
}
