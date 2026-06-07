import { useEffect, useRef, useState } from 'react';

const API_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, '') || 'http://localhost:8000';

/**
 * Abre um EventSource pro stream SSE do financas e chama `onEvento` a cada
 * evento (ex.: o bot lançou um gasto → o dashboard se atualiza sozinho).
 * Retorna se a conexão está ativa, pra mostrar o "ao vivo".
 */
export function useFinancasEventos(usuarioId: string, onEvento: () => void): boolean {
  const [conectado, setConectado] = useState(false);
  const onEventoRef = useRef(onEvento);
  onEventoRef.current = onEvento;

  useEffect(() => {
    if (typeof window === 'undefined' || typeof EventSource === 'undefined') {
      return;
    }
    const url = `${API_URL}/api/financas/eventos?usuario_id=${encodeURIComponent(
      usuarioId,
    )}`;
    const es = new EventSource(url);
    es.onopen = () => setConectado(true);
    es.onerror = () => setConectado(false);
    es.addEventListener('financas', () => onEventoRef.current());

    return () => {
      es.close();
      setConectado(false);
    };
  }, [usuarioId]);

  return conectado;
}
