"""Centros de trabalho, roteiros (RF06) e carga x capacidade - CRP
(RF12, RN09)."""

import itens
import mps
import persistencia
import utils

# Status das OPs que geram carga nos centros (ver README).
STATUS_CARGA = ["PLANEJADA", "FIRME", "LIBERADA"]


# ---------------------------------------------------------------------
# Centros de trabalho
# ---------------------------------------------------------------------

def validar_codigo_centro(codigo):
    """Verifica se o código do centro segue o formato CT-00."""
    return (len(codigo) == 5
            and codigo[:3] == "CT-"
            and codigo[3:].isdigit())


def ler_codigo_centro(mensagem):
    """Lê um código de centro no formato CT-00 (em maiúsculas)."""
    while True:
        codigo = input(mensagem).strip().upper()
        if validar_codigo_centro(codigo):
            return codigo
        print("ERRO: código inválido. Use o formato CT-00, ex.: CT-03.")


def ler_centro_existente(dados, mensagem):
    """Lê um código de centro e o devolve se ele estiver cadastrado.

    Devolve None se o centro não existir.
    """
    codigo = ler_codigo_centro(mensagem)
    if codigo not in dados["centros"]:
        print(f"ERRO: o centro {codigo} não está cadastrado.")
        return None
    return codigo


def cadastrar_centro(dados):
    """Cadastra um centro de trabalho (RF06)."""
    utils.exibir_titulo("CADASTRAR CENTRO DE TRABALHO")
    codigo = ler_codigo_centro("Código (ex.: CT-01): ")
    if codigo in dados["centros"]:
        print(f"ERRO: o centro {codigo} já está cadastrado.")
        return

    dados["centros"][codigo] = {
        "descricao": utils.ler_texto("Descrição: "),
        "capacidade_horas": utils.ler_decimal(
            "Capacidade (horas/semana): ", 0.1),
        "custo_hora": utils.ler_decimal("Custo-hora (R$): ", 0),
    }
    persistencia.salvar_dados(dados)
    print(f"Centro {codigo} cadastrado com sucesso.")


def listar_centros(dados):
    """Lista os centros de trabalho cadastrados."""
    utils.exibir_titulo("CENTROS DE TRABALHO")
    if not dados["centros"]:
        print("Nenhum centro cadastrado.")
        return

    print(f"{'Código':<8}{'Descrição':<26}{'Capac.(h/sem)':>14}"
          f"{'Custo-hora':>14}")
    for codigo in sorted(dados["centros"]):
        centro = dados["centros"][codigo]
        capacidade = utils.formatar_quantidade(centro["capacidade_horas"])
        custo = utils.formatar_moeda(centro["custo_hora"])
        print(f"{codigo:<8}{centro['descricao'][:25]:<26}"
              f"{capacidade:>14}{custo:>14}")


def alterar_centro(dados):
    """Altera um campo de um centro de trabalho."""
    utils.exibir_titulo("ALTERAR CENTRO DE TRABALHO")
    codigo = ler_centro_existente(dados, "Código do centro: ")
    if codigo is None:
        return

    centro = dados["centros"][codigo]
    print(f"Descrição: {centro['descricao']}")
    print(f"Capacidade: "
          f"{utils.formatar_quantidade(centro['capacidade_horas'])} "
          f"h/semana")
    print(f"Custo-hora: {utils.formatar_moeda(centro['custo_hora'])}")
    print("\n 1. Descrição  2. Capacidade  3. Custo-hora  0. Cancelar")
    campo = utils.ler_inteiro("Escolha o campo: ", 0, 3)

    if campo == 0:
        print("Alteração cancelada.")
        return
    elif campo == 1:
        centro["descricao"] = utils.ler_texto("Nova descrição: ")
    elif campo == 2:
        centro["capacidade_horas"] = utils.ler_decimal(
            "Nova capacidade (horas/semana): ", 0.1)
    elif campo == 3:
        centro["custo_hora"] = utils.ler_decimal("Novo custo-hora (R$): ",
                                                 0)

    persistencia.salvar_dados(dados)
    print(f"Centro {codigo} alterado com sucesso.")


# ---------------------------------------------------------------------
# Roteiros (operação única por item fabricado)
# ---------------------------------------------------------------------

def obter_roteiro(dados, codigo):
    """Devolve o roteiro de um item ou None se ele não tiver roteiro."""
    return dados["roteiros"].get(codigo)


def definir_roteiro(dados):
    """Informa o centro e o tempo por unidade de um item fabricado.

    Cada item tem uma única operação (RF06). Se o item já tiver
    roteiro, ele é substituído.
    """
    utils.exibir_titulo("DEFINIR ROTEIRO")
    if not dados["centros"]:
        print("Cadastre pelo menos um centro de trabalho antes.")
        return

    codigo = itens.ler_codigo_existente(dados, "Código do item: ")
    if codigo is None:
        return
    if dados["itens"][codigo]["tipo"] == "MP":
        print("ERRO: matéria-prima é comprada e não possui roteiro.")
        return

    roteiro_atual = obter_roteiro(dados, codigo)
    if roteiro_atual is not None:
        tempo = utils.formatar_quantidade(roteiro_atual["tempo_unitario"])
        print(f"Roteiro atual: {roteiro_atual['centro']}, {tempo} h/un "
              f"(será substituído).")

    print("Centros disponíveis: " + ", ".join(sorted(dados["centros"])))
    centro = ler_centro_existente(dados, "Centro de trabalho: ")
    if centro is None:
        return
    tempo = utils.ler_decimal("Tempo por unidade (horas): ", 0.001)

    dados["roteiros"][codigo] = {"centro": centro, "tempo_unitario": tempo}
    persistencia.salvar_dados(dados)
    print(f"Roteiro de {codigo} definido: {centro}, "
          f"{utils.formatar_quantidade(tempo)} h/un.")


def listar_roteiros(dados):
    """Lista o roteiro de todos os itens fabricados (PA e SA)."""
    utils.exibir_titulo("ROTEIROS")
    print(f"{'Item':<8}{'Descrição':<28}{'Centro':<8}{'Tempo (h/un)':>13}")
    total = 0
    for tipo in ["PA", "SA"]:
        for codigo in sorted(dados["itens"]):
            item = dados["itens"][codigo]
            if item["tipo"] == tipo:
                total += 1
                roteiro = obter_roteiro(dados, codigo)
                if roteiro is None:
                    centro = "-"
                    tempo = "SEM ROTEIRO"
                else:
                    centro = roteiro["centro"]
                    tempo = utils.formatar_quantidade(
                        roteiro["tempo_unitario"])
                print(f"{codigo:<8}{item['descricao'][:27]:<28}"
                      f"{centro:<8}{tempo:>13}")
    if total == 0:
        print("Nenhum item fabricado (PA ou SA) cadastrado.")


# ---------------------------------------------------------------------
# Carga x capacidade - CRP (RF12, RN09)
# ---------------------------------------------------------------------

def formatar_horas(valor):
    """Formata horas com uma casa decimal: 15.0 vira '15,0'."""
    return f"{valor:.1f}".replace(".", ",")


def calcular_carga(dados, centro):
    """Calcula a carga (em horas) de um centro em cada semana (RN09).

    Carga = soma de (quantidade da OP x tempo unitário do roteiro) das
    OPs com liberação naquela semana. OPs atrasadas (liberação antes da
    semana 1) entram na semana 1.
    """
    carga = [0] * mps.HORIZONTE
    for ordem in dados["ordens"].values():
        if ordem["tipo"] != "OP" or ordem["status"] not in STATUS_CARGA:
            continue
        roteiro = obter_roteiro(dados, ordem["item"])
        if roteiro is None or roteiro["centro"] != centro:
            continue
        semana = max(ordem["semana_liberacao"], 1)
        if semana <= mps.HORIZONTE:
            horas = ordem["quantidade"] * roteiro["tempo_unitario"]
            carga[semana - 1] += horas
    for semana in range(mps.HORIZONTE):
        carga[semana] = round(carga[semana], 2)
    return carga


def exibir_crp(dados):
    """Exibe a carga x capacidade de cada centro por semana, sinalizando
    as semanas com sobrecarga (RF12)."""
    utils.exibir_titulo("CARGA x CAPACIDADE (CRP)")
    if not dados["centros"]:
        print("Nenhum centro de trabalho cadastrado.")
        return

    for codigo in sorted(dados["centros"]):
        centro = dados["centros"][codigo]
        capacidade = centro["capacidade_horas"]
        carga = calcular_carga(dados, codigo)

        print(f"\nCARGA x CAPACIDADE - {codigo} {centro['descricao']} "
              f"({formatar_horas(capacidade)} h/semana)")
        print(f"{'Sem':<5}{'Carga(h)':>9}{'Uso(%)':>8}")
        sobrecarga = []
        for semana in range(1, mps.HORIZONTE + 1):
            horas = carga[semana - 1]
            uso = horas / capacidade * 100
            barra = "#" * round(uso / 10)
            linha = (f"{semana:<5}{formatar_horas(horas):>9}"
                     f"{round(uso):>8} {barra}")
            if horas > capacidade:
                linha += " SOBRECARGA"
                sobrecarga.append(str(semana))
            print(linha)

        if sobrecarga:
            print(f"Sugestão: antecipar OPs ou programar hora extra nas "
                  f"semanas {', '.join(sobrecarga)}.")
        else:
            print("Nenhuma semana com sobrecarga.")
