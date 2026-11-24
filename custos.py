"""Custo padrão dos itens fabricados (RF13)."""

import capacidade
import estrutura
import itens
import utils


def custo_mao_de_obra(dados, codigo):
    """Devolve o custo de mão de obra de uma unidade do item.

    Mão de obra = tempo por unidade x custo-hora do centro do roteiro.
    Devolve 0 se o item não tiver roteiro.
    """
    roteiro = capacidade.obter_roteiro(dados, codigo)
    if roteiro is None:
        return 0
    custo_hora = dados["centros"][roteiro["centro"]]["custo_hora"]
    return roteiro["tempo_unitario"] * custo_hora


def custo_padrao(dados, codigo):
    """Calcula o custo padrão de uma unidade do item (RF13).

    MP: custo unitário cadastrado. PA e SA: soma dos custos dos
    componentes (calculados da mesma forma, de forma recursiva) mais a
    mão de obra do próprio item.
    """
    item = dados["itens"][codigo]
    if item["tipo"] == "MP":
        return item["custo_unitario"]

    total = 0
    for linha in estrutura.obter_componentes(dados, codigo):
        total += linha["quantidade"] * custo_padrao(dados,
                                                    linha["componente"])
    total += custo_mao_de_obra(dados, codigo)
    return round(total, 2)


def exibir_detalhe(dados, codigo):
    """Exibe a composição do custo padrão de um item (mockup 6.7)."""
    item = dados["itens"][codigo]
    print(f"\nCUSTO PADRÃO - {codigo} {item['descricao']}")
    print(f"{'Item':<8}{'Descrição':<28}{'Qtde':>6}{'Custo un.':>12}"
          f"{'Total':>12}")

    for linha in estrutura.obter_componentes(dados, codigo):
        componente = linha["componente"]
        unitario = custo_padrao(dados, componente)
        total = linha["quantidade"] * unitario
        descricao = dados["itens"][componente]["descricao"][:27]
        print(f"{componente:<8}{descricao:<28}"
              f"{utils.formatar_quantidade(linha['quantidade']):>6}"
              f"{utils.formatar_moeda(unitario)[3:]:>12}"
              f"{utils.formatar_moeda(total)[3:]:>12}")

    roteiro = capacidade.obter_roteiro(dados, codigo)
    if roteiro is None:
        print(f"{'':<8}{'Mão de obra (sem roteiro)':<28}{'':>6}{'':>12}"
              f"{'0,00':>12}")
    else:
        centro = roteiro["centro"]
        custo_hora = dados["centros"][centro]["custo_hora"]
        horas = utils.formatar_quantidade(roteiro["tempo_unitario"]) + " h"
        mao_de_obra = custo_mao_de_obra(dados, codigo)
        print(f"{'':<8}{'Mão de obra ' + centro:<28}{horas:>6}"
              f"{utils.formatar_moeda(custo_hora)[3:]:>12}"
              f"{utils.formatar_moeda(mao_de_obra)[3:]:>12}")

    utils.exibir_linha()
    print(f"CUSTO PADRÃO TOTAL: "
          f"{utils.formatar_moeda(custo_padrao(dados, codigo))}")


def exibir_custos(dados):
    """Exibe o custo padrão de todos os itens fabricados e permite
    detalhar a composição de um deles (RF13)."""
    utils.exibir_titulo("CUSTO PADRÃO DOS PRODUTOS")
    fabricados = []
    for tipo in ["PA", "SA"]:
        for codigo in sorted(dados["itens"]):
            if dados["itens"][codigo]["tipo"] == tipo:
                fabricados.append(codigo)
    if not fabricados:
        print("Nenhum item fabricado (PA ou SA) cadastrado.")
        return

    print(f"{'Item':<8}{'Descrição':<28}{'Custo padrão':>15}")
    for codigo in fabricados:
        descricao = dados["itens"][codigo]["descricao"][:27]
        custo = utils.formatar_moeda(custo_padrao(dados, codigo))
        print(f"{codigo:<8}{descricao:<28}{custo:>15}")

    if utils.confirmar("\nDeseja detalhar o custo de um item?"):
        codigo = itens.ler_codigo_existente(dados, "Código do item: ")
        if codigo is None:
            return
        if dados["itens"][codigo]["tipo"] == "MP":
            print("Matéria-prima: o custo é o custo unitário cadastrado.")
            return
        exibir_detalhe(dados, codigo)
