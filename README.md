# Wattson — ADR 0 (Fitness Engine v0)

Autoanálise, Diagnóstico e Fitness Arquitetural. **Observa e diagnostica; não controla.**
Só usa a biblioteca padrão (Python 3.10+), então roda igual no VAIO e no Pi 4.

## Uso

```bash
python -m wattson_core.adr0                     # analisa a pasta atual
python -m wattson_core.adr0 /caminho/projeto    # ou outra pasta
python -m wattson_core.adr0 --category architecture
python -m wattson_core.adr0 --only R002 R007
python -m wattson_core.adr0 --format json       # para o Event Log / integrações
python -m wattson_core.adr0 --list-rules
```

Código de saída: `0` ok · `1` achado com severidade ≥ `--fail-on` (padrão `high`) ·
`2` diagnóstico incompleto (regra com erro ou projeto não encontrado).

## Integração com OpenBot (MCP)

O Wattson pode ser usado como servidor MCP (stdio) pelo OpenBot, sem dependências
extras. O processo fala JSON-RPC 2.0 por linha e expõe:

| Ferramenta | O que faz |
|---|---|
| `wattson_chat` | Envia uma mensagem ao cérebro do Wattson (conversa, diagnóstico, busca ou `opencode:`). |
| `wattson_diagnose` | Roda a autoavaliação ADR0 e devolve o relatório formatado. |

```bash
python -m wattson_core.mcp_server   # fica ouvindo no stdin/stdout
```

No OpenBot, cadastre o servidor em MCP com transporte `stdio`, comando
`<caminho>/.venv/bin/python`, argumentos `-m wattson_core.mcp_server` e diretório
de trabalho na raiz do projeto. As ferramentas aparecem para os agentes no turno
seguinte. O servidor não imprime nada no stdout além das respostas do protocolo;
erros de ferramenta voltam como `isError` em vez de derrubar o processo.

## Testes

```bash
python -m unittest discover -s tests -t . -v
```

## Onde mexer

| Quero… | Arquivo |
|---|---|
| Mudar uma decisão arquitetural (fronteiras, zonas, limites) | `wattson_core/adr0/contract.py` |
| Criar uma regra nova | `wattson_core/adr0/rules/` + registrar em `rules/__init__.py` |
| Mudar o formato do relatório | `wattson_core/adr0/report.py` |

Uma regra nova precisa de teste nos dois sentidos (detecta a violação, não acusa o saudável).

## Princípios embutidos

- **Independente:** o ADR 0 nunca importa o resto do Wattson (regra R002/R010 verifica isso nele mesmo).
- **Somente leitura:** nunca escreve arquivos, executa comandos nem usa a rede (R010).
- **Honesto:** cada achado tem confiança CONFIRMADO / PROVÁVEL / POSSÍVEL / INDETERMINADO.
- **Resiliente:** uma regra que falha vira `ERROR` (INDETERMINADO); as demais continuam.
- **Sem falso alarme por ausência:** componente que ainda não existe vira `SKIP`, não `FAIL`.

## Ainda não cobre

Verificações de **runtime** (serviços, latência, estado do Runtime, Heartbeat, Event Log)
dependem da Fase 1 e entram como novas regras quando esses componentes existirem.
A análise atual é estática: detecta onde uma fronteira *pode* ser contornada, não prova o
comportamento em execução.
