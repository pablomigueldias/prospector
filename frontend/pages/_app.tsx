import type { AppProps } from 'next/app';

import { AuthProvider } from '@/contexts/AuthContext';
import '@/styles/globals.css';
// Tema de syntax highlight pra prévia de posts do blog (react-markdown + hljs).
import 'highlight.js/styles/github-dark.css';

export default function App({ Component, pageProps }: AppProps) {
  return (
    <AuthProvider>
      <Component {...pageProps} />
    </AuthProvider>
  );
}
