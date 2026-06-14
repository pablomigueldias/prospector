// Barrel dos tipos do app, organizados por domínio (vertical slices).
//
// Mantém o import público estável: `import { X } from '@/lib/types'` continua
// funcionando. Para mexer num domínio, vá direto no arquivo dele.

export * from './core';
export * from './prospector';
export * from './auth';
export * from './copywriter';
export * from './pessoal';
export * from './financas';
