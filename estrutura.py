"""Estrutura de produto (BOM) e explosão indentada (RF03, RN03)."""

import itens
import persistencia
import utils

# RN03: quais tipos cada tipo de item pode ter como componente.
COMPONENTES_PERMITIDOS = {
    "PA": ["SA", "MP"],
    "SA": ["MP"],
    "MP": [],
}


def obter_componentes(dados, codigo):
    """Devolve a lista de componentes de um item (vazia se não tiver)."""
    return dados["estrutura"].get(codigo, [])


def adicionar_componente(dados):
    """Adiciona um componente à estrutura de um item pai (RF03, RN03).

    Se o componente já estiver na estrutura, a quantidade é atualizada.
    """
    utils.exibir_titulo("ADICIONAR COMPONENTE")
    pai = itens.ler_codigo_existente(dados, "Código do item pai: ")
    if pai is None:
        return
    tipo_pai = dados["itens"][pai]["tipo"]
    if tipo_pai == "MP":
        print("ERRO: matéria-prima não possui estrutura (RN03).")
        return

    componente = itens.ler_codigo_existente(dados, "Código do componente: ")
    if componente is None:
        return
    tipo_componente = dados["itens"][componente]["tipo"]
    if tipo_componente not in COMPONENTES_PERMITIDOS[tipo_pai]:
        permitidos = " ou ".join(COMPONENTES_PERMITIDOS[tipo_pai])
        print(f"ERRO: um {tipo_pai} só pode ter componentes do tipo "
              f"{permitidos} (RN03).")
        return

    unidade = dados["itens"][componente]["unidade"]
    quantidade = utils.ler_decimal(
        f"Quantidade por unidade do pai ({unidade}): ", 0.001)

    if pai not in dados["estrutura"]:
        dados["estrutura"][pai] = []

    for linha in dados["estrutura"][pai]:
        if linha["componente"] == componente:
            linha["quantidade"] = quantidade
            persistencia.salvar_dados(dados)
            print(f"{componente} já estava na estrutura de {pai}: "
                  f"quantidade atualizada.")
            return

    dados["estrutura"][pai].append({"componente": componente,
                                    "quantidade": quantidade})
    persistencia.salvar_dados(dados)
    print(f"{componente} adicionado à estrutura de {pai}.")


def remover_componente(dados):
    """Remove um componente da estrutura de um item pai."""
    utils.exibir_titulo("REMOVER COMPONENTE")
    pai = itens.ler_codigo_existente(dados, "Código do item pai: ")
    if pai is None:
        return
    componentes = obter_componentes(dados, pai)
    if not componentes:
        print(f"O item {pai} não possui estrutura cadastrada.")
        return

    componente = utils.ler_codigo("Código do componente a remover: ")
    for linha in componentes:
        if linha["componente"] == componente:
            componentes.remove(linha)
            if not componentes:
                del dados["estrutura"][pai]
            persistencia.salvar_dados(dados)
            print(f"{componente} removido da estrutura de {pai}.")
            return
    print(f"ERRO: {componente} não faz parte da estrutura de {pai}.")


def exibir_componentes(dados, codigo_pai, prefixo, nivel, niveis):
    """Exibe os componentes de um item e, de forma recursiva, os
    componentes de cada componente, montando a árvore indentada.

    'niveis' é um dicionário {nível: [códigos]} preenchido durante a
    exibição, usado para mostrar o resumo de níveis no final.
    """
    componentes = obter_componentes(dados, codigo_pai)
    for posicao in range(len(componentes)):
        linha = componentes[posicao]
        codigo = linha["componente"]
        item = dados["itens"][codigo]

        ultimo = posicao == len(componentes) - 1
        if ultimo:
            conector = "└── "
            prefixo_filhos = prefixo + "    "
        else:
            conector = "├── "
            prefixo_filhos = prefixo + "│   "

        texto = f"{prefixo}{conector}{codigo} {item['descricao'][:28]} "
        quantidade = utils.formatar_quantidade(linha["quantidade"])
        print(f"{texto.ljust(48, '.')} {quantidade} {item['unidade']}")

        if nivel not in niveis:
            niveis[nivel] = []
        niveis[nivel].append(codigo)

        exibir_componentes(dados, codigo, prefixo_filhos, nivel + 1,
                           niveis)


def exibir_estrutura(dados):
    """Exibe a explosão da BOM de um item, com os níveis (RF03)."""
    utils.exibir_titulo("ESTRUTURA DE PRODUTO (BOM)")
    codigo = itens.ler_codigo_existente(dados, "Código do produto: ")
    if codigo is None:
        return
    if not obter_componentes(dados, codigo):
        print(f"O item {codigo} não possui estrutura cadastrada.")
        return

    print()
    print(f"{codigo} {dados['itens'][codigo]['descricao']}")
    niveis = {0: [codigo]}
    exibir_componentes(dados, codigo, "", 1, niveis)

    partes = []
    for nivel in sorted(niveis):
        partes.append(f"{nivel} = {', '.join(niveis[nivel])}")
    print("\nNíveis: " + " | ".join(partes))
