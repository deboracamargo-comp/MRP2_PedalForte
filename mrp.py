"""Cálculo MRP e registro por item (RF08, RN04 a RN08)."""

import estoque
import itens
import mps
import ordens
import utils

STATUS_PROGRAMADOS = ["FIRME", "LIBERADA"]


def recebimentos_programados(dados, codigo):
    """Soma, por semana de entrega, as ordens FIRMES e LIBERADAS de um
    item (RN08)."""
    recebimentos = [0] * mps.HORIZONTE
    for ordem in dados["ordens"].values():
        semana = ordem["semana_entrega"]
        if (ordem["item"] == codigo
                and ordem["status"] in STATUS_PROGRAMADOS
                and 1 <= semana <= mps.HORIZONTE):
            recebimentos[semana - 1] += ordem["quantidade"]
    return recebimentos


def calcular_necessidade_bruta(dados, codigo, liberacoes):
    """Calcula a necessidade bruta de um item em cada semana (RN04).

    PA: vem do MPS. SA e MP: soma das liberações planejadas de todos os
    itens pai, multiplicadas pela quantidade por unidade da BOM.
    """
    if dados["itens"][codigo]["tipo"] == "PA":
        return list(mps.obter_demanda(dados, codigo))

    necessidade = [0] * mps.HORIZONTE
    for pai, componentes in dados["estrutura"].items():
        for linha in componentes:
            if linha["componente"] == codigo and pai in liberacoes:
                for semana in range(mps.HORIZONTE):
                    necessidade[semana] += (liberacoes[pai][semana]
                                            * linha["quantidade"])
    for semana in range(mps.HORIZONTE):
        necessidade[semana] = round(necessidade[semana], 3)
    return necessidade


def calcular_registro(dados, codigo, necessidade_bruta):
    """Calcula o registro MRP de um item, semana a semana (RN05 a RN07).

    Devolve um dicionário com as listas de cada linha do registro.
    """
    item = dados["itens"][codigo]
    seguranca = item["estoque_seguranca"]
    lote = item["lote_minimo"]
    lead_time = item["lead_time"]

    programados = recebimentos_programados(dados, codigo)
    projetado = []
    liquida = []
    planejados = []
    liberacoes = [0] * mps.HORIZONTE
    liberacoes_componentes = [0] * mps.HORIZONTE

    anterior = estoque.obter_saldo(dados, codigo)
    for semana in range(mps.HORIZONTE):
        necessidade = round(max(0, necessidade_bruta[semana] + seguranca
                                - (anterior + programados[semana])), 3)
        if necessidade > 0:
            recebimento = max(necessidade, lote)
        else:
            recebimento = 0
        atual = round(anterior + programados[semana] + recebimento
                      - necessidade_bruta[semana], 3)

        liquida.append(necessidade)
        planejados.append(recebimento)
        projetado.append(atual)
        anterior = atual

        if recebimento > 0:
            semana_liberacao = semana - lead_time
            if semana_liberacao >= 0:
                liberacoes[semana_liberacao] += recebimento
                liberacoes_componentes[semana_liberacao] += recebimento
            else:
                liberacoes_componentes[0] += recebimento

    return {
        "necessidade_bruta": necessidade_bruta,
        "recebimentos_programados": programados,
        "estoque_projetado": projetado,
        "necessidade_liquida": liquida,
        "recebimentos_planejados": planejados,
        "liberacoes_planejadas": liberacoes,
        "liberacoes_componentes": liberacoes_componentes,
    }


def calcular_mrp(dados):
    """Calcula o registro MRP de todos os itens, na ordem PA, SA e MP
    (RN04). Não altera nenhum dado; só devolve os registros."""
    registros = {}
    liberacoes = {}
    for tipo in utils.TIPOS_ITEM:
        for codigo in sorted(dados["itens"]):
            if dados["itens"][codigo]["tipo"] == tipo:
                necessidade = calcular_necessidade_bruta(dados, codigo,
                                                         liberacoes)
                registro = calcular_registro(dados, codigo, necessidade)
                registros[codigo] = registro
                liberacoes[codigo] = registro["liberacoes_componentes"]
    return registros


def executar_mrp(dados):
    """Executa o MRP, recria as ordens planejadas e as exibe (RF08,
    RF09)."""
    utils.exibir_titulo("EXECUTAR MRP")
    if not dados["mps"]:
        print("Cadastre o MPS antes de executar o MRP.")
        return

    registros = calcular_mrp(dados)
    novas = ordens.substituir_planejadas(dados, registros)

    hoje = utils.formatar_data(utils.data_hoje())
    print(f"ORDENS PLANEJADAS - execução do MRP em {hoje}")
    if not novas:
        print("Nenhuma ordem necessária no horizonte.")
        return
    ordens.exibir_tabela(dados, novas)

    atrasadas = []
    for numero in novas:
        if dados["ordens"][numero]["atrasada"]:
            atrasadas.append(numero)
    if atrasadas:
        print(f"\n{len(atrasadas)} mensagem(ns) de exceção: ordens com "
              f"liberação antes da semana 1 (RN07):")
        for numero in atrasadas:
            ordem = dados["ordens"][numero]
            print(f"  {numero} ({ordem['item']}): liberar na semana "
                  f"{ordem['semana_liberacao']} - ATRASADA")


def exibir_registro(dados):
    """Exibe o registro MRP de um item escolhido, por semana (RF08)."""
    codigo = itens.ler_codigo_existente(dados, "Código do item: ")
    if codigo is None:
        return
    registro = calcular_mrp(dados)[codigo]
    item = dados["itens"][codigo]

    print(f"\nREGISTRO MRP - {codigo} {item['descricao']}")
    print(f"Lead time: {item['lead_time']} sem | Est. segurança: "
          f"{utils.formatar_quantidade(item['estoque_seguranca'])} | "
          f"Lote mín.: {utils.formatar_quantidade(item['lote_minimo'])} | "
          f"Estoque: "
          f"{utils.formatar_quantidade(estoque.obter_saldo(dados, codigo))}")

    cabecalho = f"{'Semana':<21}"
    for semana in range(1, mps.HORIZONTE + 1):
        cabecalho += f"{semana:>7}"
    print(cabecalho)

    linhas = [
        ("Necessidade bruta", "necessidade_bruta"),
        ("Receb. programados", "recebimentos_programados"),
        ("Estoque projetado", "estoque_projetado"),
        ("Necessidade líquida", "necessidade_liquida"),
        ("Receb. planejados", "recebimentos_planejados"),
        ("Liberação planejada", "liberacoes_planejadas"),
    ]
    for nome, chave in linhas:
        texto = f"{nome:<21}"
        for valor in registro[chave]:
            texto += f"{utils.formatar_quantidade(valor):>7}"
        print(texto)
