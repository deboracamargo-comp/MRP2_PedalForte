# MRP II — Pedal Forte Bicicletas

Sistema de Planejamento dos Recursos de Manufatura (MRP II) em modo texto,
desenvolvido em Python para a fábrica fictícia **Pedal Forte Bicicletas Ltda.**
(Divinópolis-MG). O sistema integra cadastro de itens, estrutura de produto
(BOM), estoques, Plano Mestre de Produção (MPS), cálculo MRP, ordens de
produção e de compra, carga x capacidade (CRP), custo padrão, relatórios CSV e
gráficos de gestão.

A cada execução, o sistema responde: **o que produzir ou comprar, quanto,
quando e se há capacidade para isso.**

- **Disciplina:** Programação em Python — CEFET-MG, Campus Divinópolis
- **Professor:** Guido Pantuza
- **Aluna:** Débora Cristina Barbosa Camargo
- **Trabalho:** 2º trabalho — Sistema MRP II (2026/2)

## Sumário

1. [Requisitos e instalação](#1-requisitos-e-instalação)
2. [Como executar](#2-como-executar)
3. [Estrutura do projeto](#3-estrutura-do-projeto)
4. [Requisitos funcionais atendidos](#4-requisitos-funcionais-atendidos)
5. [Regras de negócio](#5-regras-de-negócio)
6. [Requisitos não funcionais](#6-requisitos-não-funcionais)
7. [Base de demonstração](#7-base-de-demonstração)
8. [Instruções de uso: ciclo completo](#8-instruções-de-uso-ciclo-completo)
9. [Decisões de projeto](#9-decisões-de-projeto)
10. [Persistência dos dados](#10-persistência-dos-dados)
11. [Vídeos de demonstração](#11-vídeos-de-demonstração)

---

## 1. Requisitos e instalação

- Python **3.10 ou superior**
- Biblioteca **matplotlib** (usada apenas nos gráficos, RF16)

No Linux:

```bash
git clone https://github.com/deboracamargo-comp/MRP2_PedalForte.git
cd MRP2_PedalForte
python3 -m pip install -r requirements.txt
```

## 2. Como executar

```bash
python3 main.py
```

Os dados da pasta `data/` são carregados automaticamente ao iniciar (RF15).
Toda operação que altera dados grava os arquivos na hora, então nada se perde
se o programa for fechado (inclusive com Ctrl+C).

Os relatórios CSV e os gráficos PNG são gravados na pasta `exports/`, criada
automaticamente.

## 3. Estrutura do projeto

A organização segue a arquitetura definida no enunciado:

```
MRP2_PedalForte/
├── main.py           # ponto de entrada: carrega os dados e abre o menu
├── menu.py           # menus e navegação (RF01)
├── itens.py          # cadastro, listagem e alteração de itens (RF02)
├── estrutura.py      # BOM e explosão indentada recursiva (RF03)
├── estoque.py        # movimentações, saldo, kardex e alertas (RF04, RF05)
├── capacidade.py     # centros, roteiros (RF06) e CRP (RF12)
├── mps.py            # plano mestre de produção (RF07)
├── mrp.py            # cálculo MRP e registro por item (RF08)
├── ordens.py         # OPs, OCs, ciclo de status e apontamento (RF09-RF11)
├── custos.py         # custo padrão recursivo (RF13)
├── relatorios.py     # exportação CSV (RF14)
├── graficos.py       # gráficos de gestão com matplotlib (RF16)
├── persistencia.py   # leitura e gravação de arquivos (RF15)
├── utils.py          # validação de entradas e formatação
├── requirements.txt
├── data/             # base de demonstração (JSON + kardex em CSV)
└── docs/
```

**Organização:** o programa é estruturado em funções, agrupadas em módulos
coesos (RNF04). Todos os dados ficam em um único dicionário `dados`, carregado
pelo `main.py` e passado para as funções. O `persistencia.py` é o único módulo
que lê e grava os arquivos de dados.

## 4. Requisitos funcionais atendidos

| RF | Descrição | Onde está | Menu |
|----|-----------|-----------|------|
| RF01 | Menu principal | `menu.py` | — |
| RF02 | Cadastrar, listar e alterar itens | `itens.py` | 1 → 1, 2, 3 |
| RF03 | BOM em até 3 níveis e explosão indentada | `estrutura.py` | 1 → 4 |
| RF04 | Movimentações (entrada, saída, ajuste) | `estoque.py` | 2 → 1 |
| RF05 | Saldo, kardex e alerta de estoque de segurança | `estoque.py` | 2 → 2, 3 |
| RF06 | Centros de trabalho e roteiros | `capacidade.py` | 1 → 5, 6 |
| RF07 | Cadastrar e alterar o MPS (8 semanas) | `mps.py` | 3 |
| RF08 | Cálculo MRP e registro de um item | `mrp.py` | 4 → 1, 2 |
| RF09 | Geração de OPs e OCs planejadas | `ordens.py` | 4 → 1 |
| RF10 | Firmar, liberar e encerrar ordens | `ordens.py` | 5 → F, L, E |
| RF11 | Apontamento de produção de OP liberada | `ordens.py` | 5 → A |
| RF12 | Carga x capacidade (CRP) com sobrecarga | `capacidade.py` | 6 |
| RF13 | Custo padrão (materiais + mão de obra) | `custos.py` | 7 |
| RF14 | Exportar CSV de estoque e de ordens | `relatorios.py` | 8 |
| RF15 | Persistência em `data/` com carga automática | `persistencia.py` | — |
| RF16 | Gráficos de gestão (matplotlib, tela + PNG) | `graficos.py` | 9 |

## 5. Regras de negócio

| RN | Regra | Como foi implementada |
|----|-------|-----------------------|
| RN01 | Código único no formato Tipo-Número | O código é a chave do dicionário de itens; `utils.validar_codigo` exige `PA`, `SA` ou `MP` + hífen + 3 dígitos |
| RN02 | Saldo nunca negativo | `estoque.verificar_saldo` recusa a operação com mensagem explicativa |
| RN03 | BOM com no máximo 3 níveis (PA → SA → MP) | `estrutura.COMPONENTES_PERMITIDOS`; a regra também impede ciclos |
| RN04 | MRP processado por tipo (PA, SA, MP) | `mrp.calcular_mrp`; a necessidade bruta do componente soma as liberações dos pais × quantidade |
| RN05 | NL(t) = máx(0, NB(t) + ES − (EP(t−1) + RP(t))) | `mrp.calcular_registro` |
| RN06 | Recebimento planejado = máx(NL, lote mínimo) | `mrp.calcular_registro` |
| RN07 | Liberação = entrega − lead time; antes da semana 1 → ATRASADA | `ordens.substituir_planejadas` + mensagens de exceção em `mrp.executar_mrp` |
| RN08 | Só ordens FIRMES/LIBERADAS são recebimentos programados; PLANEJADAS são recalculadas | `mrp.recebimentos_programados` e `ordens.substituir_planejadas` |
| RN09 | Carga = quantidade da OP × tempo unitário; sobrecarga se carga > capacidade | `capacidade.calcular_carga` e `capacidade.exibir_crp` |
| RN10 | Toda movimentação vai para o kardex e não pode ser excluída | `estoque.movimentar` + `persistencia.registrar_movimento` (arquivo só recebe linhas novas) |

## 6. Requisitos não funcionais

| RNF | Como foi atendido |
|-----|-------------------|
| RNF01 | Projeto individual |
| RNF02 | Python 3.10+ (sem recursos de versões mais novas) |
| RNF03 | Código verificado com `pycodestyle` (PEP 8), sem avisos |
| RNF04 | 14 módulos, um por responsabilidade, conforme a arquitetura do enunciado |
| RNF05 | Todas as entradas passam pelas funções `ler_...` do `utils.py`, que repetem a pergunta até o valor ser válido; Ctrl+C encerra sem erro |
| RNF06 | Execução validada em Linux |
| RNF07 | Persistência em JSON (cadastros) e CSV (kardex) |
| RNF08 | Cálculos de MRP, CRP, custos e estoques implementados no projeto; matplotlib usado só nos gráficos |
| RNF09 | Base de demonstração com 2 PA, 2 SA, 10 MP e 3 centros (seção 7) |

## 7. Base de demonstração

A pasta `data/` já vem com a fábrica Pedal Forte cadastrada:

**Produtos e estruturas (BOM):**

```
PA-001 Bicicleta Aro 29 MTB              PA-002 Bicicleta Aro 29 Urbana
├── SA-010 Quadro aro 29 soldado .. 1    ├── SA-010 Quadro aro 29 soldado .. 1
│   ├── MP-100 Tubo de aco ...... 3 m    ├── SA-020 Roda aro 29 montada .... 2
│   └── MP-101 Tinta epoxi .... 0,5 L    ├── MP-302 Guidao urbano .......... 1
├── SA-020 Roda aro 29 montada .... 2    ├── MP-303 Kit transmissao 7v ..... 1
│   ├── MP-200 Aro 29 aluminio .... 1    └── MP-304 Selim conforto ......... 1
│   ├── MP-201 Raio inox ......... 36
│   └── MP-202 Pneu 29 x 2.20 ..... 1
├── MP-300 Guidao MTB ............. 1
└── MP-301 Kit transmissao 12v .... 1
```

**Centros de trabalho e roteiros:**

| Centro | Descrição | Capacidade | Custo-hora | Itens (tempo por unidade) |
|--------|-----------|-----------:|-----------:|---------------------------|
| CT-01 | Soldagem e pintura | 40 h/sem | R$ 36,00 | SA-010 (0,5 h) |
| CT-02 | Montagem de rodas | 40 h/sem | R$ 40,00 | SA-020 (0,25 h) |
| CT-03 | Montagem final | 16 h/sem | R$ 40,00 | PA-001 (0,5 h), PA-002 (0,4 h) |

**Situação inicial preparada para a demonstração:**

- MPS de 8 semanas para PA-001 e PA-002.
- MP-202 (pneu) e MP-303 (kit 7v) abaixo do estoque de segurança → alertas.
- OP-0001 (SA-020, 50 un) **FIRME** e OC-0001 (MP-202, 50 un) **LIBERADA**,
  que aparecem como recebimentos programados no MRP.
- Ao executar o MRP: ordens atrasadas com mensagens de exceção e
  **sobrecarga no CT-03 nas semanas 3 e 6**.
- Custo padrão: PA-001 = R$ 792,60; PA-002 = R$ 666,60.

## 8. Instruções de uso: ciclo completo

Roteiro sugerido para conhecer o sistema com a base de demonstração:

1. **Cadastros → Estrutura → Exibir estrutura** de `PA-001`: explosão da BOM
   com os níveis.
2. **Estoque → Consultar kardex** de `MP-202`: histórico e alerta de estoque
   de segurança.
3. **MPS → Exibir MPS**: demanda das 8 semanas.
4. **Executar MRP → Executar**: ordens planejadas e mensagens de exceção.
   Depois, **Exibir registro** de `SA-020`.
5. **Ordens:** liberar a `OP-0001` (`L`) e tentar apontar (`A`): o
   apontamento é **rejeitado** por falta de pneus (MP-202).
6. **Ordens:** encerrar a `OC-0001` (`E`): os 50 pneus entram no estoque.
7. **Ordens:** apontar a `OP-0001` (`A`): componentes baixados, 50 rodas
   entram no estoque e a OP é encerrada.
8. **Estoque → Consultar kardex** de `MP-202`: o recebimento e a baixa
   aparecem com o número das ordens.
9. **Carga x capacidade:** sobrecarga do CT-03 nas semanas 3 e 6.
10. **Custo padrão:** detalhar `PA-001`.
11. **Relatórios** e **Gráficos**: arquivos gerados em `exports/`.

Para voltar à base original depois de testar, restaure a pasta `data/` com
`git checkout -- data/`.

## 9. Decisões de projeto

1. **Programação estruturada com dicionários.** Os dados vêm e voltam de JSON,
   e um dicionário é gravado direto, sem conversão.
2. **Um dicionário central `dados`.** Carregado uma vez pelo `main.py` e
   passado para as funções. Cada operação que altera dados salva os arquivos
   na mesma hora.
3. **Só o `persistencia.py` acessa arquivos de dados.** Os demais módulos
   trabalham com dicionários.
4. **Só `estoque.movimentar` altera saldos.** Ela atualiza o saldo e grava o
   kardex na mesma operação, então os dois nunca ficam diferentes. Até o
   apontamento de produção e o recebimento de OC usam essa função.
5. **O tipo do item vem do código** (`PA-001` → PA). Assim código e tipo nunca
   ficam inconsistentes. O código usa exatamente 3 dígitos, como nos exemplos
   do enunciado.
6. **Itens sem movimentação têm saldo zero.** O saldo só é criado na primeira
   movimentação.
7. **Datas:** gravadas como `aaaa-mm-dd` (ordenam corretamente como texto) e
   exibidas como `dd/mm/aaaa`.
8. **Quantidades decimais** (metros, litros); exibidas sem `.0` e com vírgula.
   A demanda do MPS é inteira (bicicletas).
9. **Saída no kardex com sinal negativo**, de modo que a soma das quantidades
   do kardex é o saldo.
10. **ATRASADA não é um quinto status.** A ordem continua PLANEJADA com a
    marcação `atrasada`, e a tela mostra "ATRASADA" (mockup 6.5). O ciclo da
    RF10 mantém os 4 status.
11. **Liberação atrasada no MRP:** os componentes de uma ordem atrasada são
    considerados na semana 1, para a necessidade não se perder.
12. **Encerrar uma OC** = receber o material (entrada no estoque). **Uma OP**
    é encerrada pelo apontamento (RF11).
13. **Apontamento "tudo ou nada":** todos os componentes são verificados antes
    de qualquer baixa; se faltar um, nada é movimentado.
14. **CRP:** a RN09 fala em "OPs liberadas naquela semana". Foi interpretado
    como as OPs não encerradas cuja liberação cai naquela semana (planejadas,
    firmes ou liberadas). Para considerar só as de status LIBERADA, basta
    alterar `STATUS_CARGA` em `capacidade.py`.
15. **Custo padrão** calculado de forma recursiva pela BOM. O custo unitário
    cadastrado de PA e SA é informativo; o de MP é o preço de compra.
16. **Gráfico de ordens** conta o número de ordens por semana (OP e OC têm
    unidades diferentes e não podem ser somadas).
17. **Exportação CSV** com `;` e codificação `utf-8-sig`, para abrir
    corretamente no Excel em português.
18. **Recursividade** usada na explosão da BOM (`estrutura.exibir_componentes`)
    e no custo padrão (`custos.custo_padrao`).

## 10. Persistência dos dados

| Arquivo | Conteúdo |
|---------|----------|
| `data/itens.json` | itens, com o código como chave |
| `data/estrutura.json` | componentes de cada item pai |
| `data/estoque.json` | saldo atual de cada item |
| `data/movimentos.csv` | kardex (somente inclusão de linhas) |
| `data/centros.json` | centros de trabalho |
| `data/roteiros.json` | centro e tempo por unidade de cada item fabricado |
| `data/mps.json` | demanda das 8 semanas de cada produto acabado |
| `data/ordens.json` | ordens de produção e de compra |

Se um arquivo JSON for corrompido, ele é renomeado para `.corrompido` (os dados
não são sobrescritos) e o sistema continua com o cadastro vazio.

## 11. Vídeos de demonstração

- Demonstração do sistema em funcionamento: *(link do vídeo)*
- Demonstração do código (arquitetura, estruturas de dados e decisões de
  projeto): *(link do vídeo)*
