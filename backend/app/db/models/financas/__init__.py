"""Models do Organizador Financeiro pessoal (schema `financas`).

Domínio pessoal, isolado do B2B (Prospector) num schema Postgres próprio.
Camadas: contas (onde o dinheiro mora) → transações → itens → anexos.
"""
