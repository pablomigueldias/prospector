'use client';

import { useState, useRef, useCallback } from 'react';
import { api } from '../lib/api';
import type { CopywriterRequest, CopywriterResponse } from '../lib/types';

interface UseCopywriterRetorno {
  gerar: (dados: CopywriterRequest) => Promise<void>;
  resultado: CopywriterResponse | null;
  carregando: boolean;
  erro: string | null;
  limpar: () => void;
}

export function useCopywriter(): UseCopywriterRetorno {
  const [resultado, setResultado] = useState<CopywriterResponse | null>(null);
  const [carregando, setCarregando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  // Permite cancelar uma requisição anterior se outra começar.
  const abortRef = useRef<AbortController | null>(null);

  const gerar = useCallback(async (dados: CopywriterRequest) => {
    // Cancela qualquer geração em andamento.
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setCarregando(true);
    setErro(null);

    try {
      const resp = await api.copywriterGerar(dados, {
        signal: controller.signal,
      });
      setResultado(resp);
    } catch (e: unknown) {
      // Requisição cancelada de propósito não é erro a mostrar.
      if (e instanceof DOMException && e.name === 'AbortError') return;

      const msg =
        e instanceof Error ? e.message : 'Erro inesperado ao gerar o e-mail.';
      setErro(msg);
      setResultado(null);
    } finally {
      // Só desliga o loading se este controller ainda for o atual.
      if (abortRef.current === controller) {
        setCarregando(false);
      }
    }
  }, []);

  const limpar = useCallback(() => {
    abortRef.current?.abort();
    setResultado(null);
    setErro(null);
    setCarregando(false);
  }, []);

  return { gerar, resultado, carregando, erro, limpar };
}