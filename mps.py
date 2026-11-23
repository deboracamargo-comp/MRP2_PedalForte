"""Plano Mestre de Produção - MPS (RF07)."""

import itens
import persistencia
import utils

HORIZONTE = 8  # número de semanas do planejamento


def obter_demanda(dados, codigo):
    """Devolve a lista com a demanda das 8 semanas de um produto.

    Se o produto não tiver MPS, devolve uma lista de zeros.
    """
    return dados["mps"].get(codigo, [0] * HORIZONTE)


def ler_produto_acabado(dados, mensagem):
    """Lê o código de um produto acabado (PA) cadastrado.

    Devolve None se o item não existir ou não for PA.
    """
    codigo = itens.ler_codigo_existente(dados, mensagem)
    if codigo is None:
        return None
    if dados["itens"][codigo]["tipo"] != "PA":
        print("ERRO: o MPS é definido apenas para produtos acabados (PA).")
        return None
    return codigo


def cadastrar_mps(dados):
    """Cadastra (ou redefine) a demanda das 8 semanas de um PA (RF07)."""
    utils.exibir_titulo("CADASTRAR MPS")
    codigo = ler_produto_acabado(dados, "Código do produto acabado: ")
    if codigo is None:
        return

    if codigo in dados["mps"]:
        print("Este produto já possui MPS: os valores serão substituídos.")
    print(f"Informe a demanda de {codigo} em cada semana:")
    demanda = []
    for semana in range(1, HORIZONTE + 1):
        demanda.append(utils.ler_inteiro(f"  Semana {semana}: ", 0))

    dados["mps"][codigo] = demanda
    persistencia.salvar_dados(dados)
    print(f"MPS de {codigo} salvo com sucesso.")


def alterar_semana(dados):
    """Altera a demanda de uma única semana do MPS de um PA (RF07)."""
    utils.exibir_titulo("ALTERAR MPS")
    codigo = ler_produto_acabado(dados, "Código do produto acabado: ")
    if codigo is None:
        return
    if codigo not in dados["mps"]:
        print(f"O produto {codigo} ainda não possui MPS. Use 'Cadastrar'.")
        return

    demanda = dados["mps"][codigo]
    semana = utils.ler_inteiro(f"Semana (1 a {HORIZONTE}): ", 1, HORIZONTE)
    print(f"Demanda atual da semana {semana}: {demanda[semana - 1]}")
    demanda[semana - 1] = utils.ler_inteiro("Nova demanda: ", 0)
    persistencia.salvar_dados(dados)
    print("MPS alterado com sucesso.")


def exibir_mps(dados):
    """Exibe o MPS de todos os produtos acabados, semana a semana."""
    utils.exibir_titulo("PLANO MESTRE DE PRODUÇÃO (MPS)")
    if not dados["mps"]:
        print("Nenhum MPS cadastrado.")
        return

    cabecalho = f"{'Produto':<9}"
    for semana in range(1, HORIZONTE + 1):
        cabecalho += f"{'S' + str(semana):>6}"
    print(cabecalho + f"{'Total':>8}")

    for codigo in sorted(dados["mps"]):
        demanda = dados["mps"][codigo]
        linha = f"{codigo:<9}"
        for quantidade in demanda:
            linha += f"{quantidade:>6}"
        print(linha + f"{sum(demanda):>8}")
