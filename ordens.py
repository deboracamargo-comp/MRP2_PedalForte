"""Ordens de produção (OP) e de compra (OC): geração, ciclo de status
e apontamento de produção (RF09, RF10, RF11)."""

import estoque
import estrutura
import persistencia
import utils


def proximo_numero(dados, tipo):
    """Devolve o próximo número livre para uma ordem do tipo OP ou OC.

    Exemplo: se a maior OP existente é OP-0012, devolve "OP-0013".
    """
    maior = 0
    for numero in dados["ordens"]:
        if numero.startswith(tipo):
            maior = max(maior, int(numero[3:]))
    return f"{tipo}-{maior + 1:04d}"


def texto_status(ordem):
    """Devolve o status para exibição (ATRASADA no lugar de PLANEJADA
    quando a liberação cai antes da semana 1)."""
    if ordem["status"] == "PLANEJADA" and ordem["atrasada"]:
        return "ATRASADA"
    return ordem["status"]


def substituir_planejadas(dados, registros):
    """Apaga as ordens PLANEJADAS e gera as novas a partir do resultado
    do MRP (RF09, RN07, RN08). Devolve a lista das ordens criadas."""
    for numero in list(dados["ordens"]):
        if dados["ordens"][numero]["status"] == "PLANEJADA":
            del dados["ordens"][numero]

    novas = []
    for codigo in registros:
        item = dados["itens"][codigo]
        if item["tipo"] == "MP":
            tipo = "OC"
        else:
            tipo = "OP"
        recebimentos = registros[codigo]["recebimentos_planejados"]
        for semana in range(1, len(recebimentos) + 1):
            quantidade = recebimentos[semana - 1]
            if quantidade > 0:
                liberacao = semana - item["lead_time"]
                numero = proximo_numero(dados, tipo)
                dados["ordens"][numero] = {
                    "tipo": tipo,
                    "item": codigo,
                    "quantidade": quantidade,
                    "semana_liberacao": liberacao,
                    "semana_entrega": semana,
                    "status": "PLANEJADA",
                    "atrasada": liberacao < 1,
                }
                novas.append(numero)

    persistencia.salvar_dados(dados)
    return novas


def exibir_tabela(dados, numeros):
    """Exibe uma tabela com as ordens da lista 'numeros'."""
    print(f"{'Ordem':<9}{'Tipo':<6}{'Item':<8}{'Qtde':>9}"
          f"{'Liberar':>9}{'Entregar':>10}  Status")
    for numero in numeros:
        ordem = dados["ordens"][numero]
        quantidade = utils.formatar_quantidade(ordem["quantidade"])
        liberar = "S" + str(ordem["semana_liberacao"])
        entregar = "S" + str(ordem["semana_entrega"])
        print(f"{numero:<9}{ordem['tipo']:<6}{ordem['item']:<8}"
              f"{quantidade:>9}{liberar:>9}{entregar:>10}  "
              f"{texto_status(ordem)}")


def listar_ordens(dados):
    """Lista todas as ordens: primeiro as OPs, depois as OCs."""
    utils.exibir_titulo("ORDENS DE PRODUÇÃO E DE COMPRA")
    if not dados["ordens"]:
        print("Nenhuma ordem. Execute o MRP para gerar ordens planejadas.")
        return
    numeros = []
    for tipo in ["OP", "OC"]:
        for numero in sorted(dados["ordens"]):
            if numero.startswith(tipo):
                numeros.append(numero)
    exibir_tabela(dados, numeros)


def ler_ordem(dados, mensagem):
    """Lê o número de uma ordem e o devolve se ela existir (ou None)."""
    numero = utils.ler_texto(mensagem).upper()
    if numero not in dados["ordens"]:
        print(f"ERRO: a ordem {numero} não existe.")
        return None
    return numero


def mudar_status(dados, status_atual, novo_status):
    """Passa uma ordem de 'status_atual' para 'novo_status' (RF10)."""
    numero = ler_ordem(dados, "Número da ordem: ")
    if numero is None:
        return
    ordem = dados["ordens"][numero]
    if ordem["status"] != status_atual:
        print(f"ERRO: só uma ordem {status_atual} pode passar para "
              f"{novo_status} (status atual: {ordem['status']}).")
        return
    ordem["status"] = novo_status
    persistencia.salvar_dados(dados)
    print(f"Ordem {numero}: {status_atual} -> {novo_status}.")


def firmar_ordem(dados):
    """Firma uma ordem planejada (PLANEJADA -> FIRME)."""
    mudar_status(dados, "PLANEJADA", "FIRME")


def liberar_ordem(dados):
    """Libera uma ordem firme (FIRME -> LIBERADA)."""
    mudar_status(dados, "FIRME", "LIBERADA")


def encerrar_compra(dados):
    """Encerra uma OC liberada, dando entrada do material no estoque
    (LIBERADA -> ENCERRADA)."""
    numero = ler_ordem(dados, "Número da ordem de compra: ")
    if numero is None:
        return
    ordem = dados["ordens"][numero]
    if ordem["tipo"] != "OC":
        print("ERRO: uma OP é encerrada pelo apontamento de produção.")
        return
    if ordem["status"] != "LIBERADA":
        print(f"ERRO: só uma OC LIBERADA pode ser encerrada "
              f"(status atual: {ordem['status']}).")
        return

    estoque.movimentar(dados, ordem["item"], "ENTRADA", ordem["quantidade"],
                       f"{numero} (recebimento)", utils.data_hoje())
    ordem["status"] = "ENCERRADA"
    persistencia.salvar_dados(dados)
    print(f"Ordem {numero} encerrada: material recebido no estoque.")


def apontar_producao(dados):
    """Aponta a produção total de uma OP liberada (RF11).

    Baixa os componentes do estoque, dá entrada no item produzido e
    encerra a OP. Se faltar qualquer componente, nada é feito.
    """
    numero = ler_ordem(dados, "Número da OP: ")
    if numero is None:
        return
    ordem = dados["ordens"][numero]
    if ordem["tipo"] != "OP":
        print("ERRO: o apontamento é feito apenas em ordens de produção.")
        return
    if ordem["status"] != "LIBERADA":
        print(f"ERRO: só uma OP LIBERADA pode ser apontada "
              f"(status atual: {ordem['status']}).")
        return

    componentes = estrutura.obter_componentes(dados, ordem["item"])
    faltas = []
    for linha in componentes:
        necessario = round(linha["quantidade"] * ordem["quantidade"], 3)
        saldo = estoque.obter_saldo(dados, linha["componente"])
        if saldo < necessario:
            faltas.append(f"{linha['componente']}: necessário "
                          f"{utils.formatar_quantidade(necessario)}, "
                          f"saldo {utils.formatar_quantidade(saldo)}")
    if faltas:
        print("ERRO: falta de componentes. Apontamento rejeitado.")
        for falta in faltas:
            print("  " + falta)
        return

    documento = f"{numero} ({ordem['item']})"
    hoje = utils.data_hoje()
    for linha in componentes:
        necessario = round(linha["quantidade"] * ordem["quantidade"], 3)
        estoque.movimentar(dados, linha["componente"], "SAIDA", necessario,
                           documento, hoje)
    estoque.movimentar(dados, ordem["item"], "ENTRADA", ordem["quantidade"],
                       documento, hoje)

    ordem["status"] = "ENCERRADA"
    persistencia.salvar_dados(dados)
    saldo = utils.formatar_quantidade(
        estoque.obter_saldo(dados, ordem["item"]))
    print(f"Produção apontada. {numero} encerrada. "
          f"Saldo de {ordem['item']}: {saldo}.")
