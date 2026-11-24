"""Movimentações de estoque, saldo e kardex (RF04, RF05, RN02, RN10)."""

import itens
import persistencia
import utils

TIPOS_MOVIMENTO = {"E": "ENTRADA", "S": "SAIDA", "A": "AJUSTE"}


def obter_saldo(dados, codigo):
    """Devolve o saldo atual de um item (zero se nunca foi movimentado)."""
    return dados["estoque"].get(codigo, 0.0)


def calcular_variacao(tipo, quantidade):
    """Devolve quanto o saldo muda com a movimentação.

    Entrada soma, saída subtrai. No ajuste, a quantidade já vem com o
    sinal (+ aumenta, - diminui).
    """
    if tipo == "SAIDA":
        return -quantidade
    return quantidade


def verificar_saldo(dados, codigo, variacao):
    """Verifica se o saldo continua positivo após a variação (RN02).

    Mostra uma mensagem de erro e devolve False se o saldo ficaria
    negativo.
    """
    saldo = obter_saldo(dados, codigo)
    if round(saldo + variacao, 3) < 0:
        unidade = dados["itens"][codigo]["unidade"]
        print(f"ERRO: saldo insuficiente (saldo atual: "
              f"{utils.formatar_quantidade(saldo)} {unidade}). "
              f"Operação cancelada.")
        return False
    return True


def movimentar(dados, codigo, tipo, quantidade, documento, data):
    """Registra uma movimentação e atualiza o saldo do item (RF04).

    É a ÚNICA função do sistema que altera saldos. Toda movimentação é
    gravada no kardex (RN10). Devolve True se deu certo e False se foi
    recusada por falta de saldo (RN02).
    """
    variacao = calcular_variacao(tipo, quantidade)
    if not verificar_saldo(dados, codigo, variacao):
        return False

    novo_saldo = round(obter_saldo(dados, codigo) + variacao, 3)
    dados["estoque"][codigo] = novo_saldo
    persistencia.registrar_movimento({
        "data": data,
        "codigo": codigo,
        "tipo": tipo,
        "quantidade": variacao,
        "saldo": novo_saldo,
        "documento": documento,
    })
    persistencia.salvar_dados(dados)
    return True


def exibir_alerta(dados, codigo):
    """Mostra um alerta se o saldo estiver abaixo do estoque de
    segurança (RF05)."""
    saldo = obter_saldo(dados, codigo)
    item = dados["itens"][codigo]
    if saldo < item["estoque_seguranca"]:
        print(f"ALERTA: saldo ({utils.formatar_quantidade(saldo)} "
              f"{item['unidade']}) abaixo do estoque de segurança "
              f"({utils.formatar_quantidade(item['estoque_seguranca'])} "
              f"{item['unidade']}).")


def registrar_movimentacao(dados):
    """Pede os dados de uma movimentação ao usuário e a registra (RF04)."""
    utils.exibir_titulo("MOVIMENTAÇÃO DE ESTOQUE")
    codigo = itens.ler_codigo_existente(dados, "Código do item: ")
    if codigo is None:
        return

    letra = utils.ler_opcao("Tipo [E]ntrada [S]aída [A]juste: ",
                            ["E", "S", "A"])
    tipo = TIPOS_MOVIMENTO[letra]

    if tipo == "AJUSTE":
        quantidade = utils.ler_decimal(
            "Quantidade do ajuste (+ aumenta, - diminui): ")
        if quantidade == 0:
            print("ERRO: o ajuste não pode ser zero.")
            return
    else:
        quantidade = utils.ler_decimal("Quantidade: ", 0.001)

    variacao = calcular_variacao(tipo, quantidade)
    if not verificar_saldo(dados, codigo, variacao):
        return

    documento = utils.ler_texto("Documento/motivo: ")
    data = utils.ler_data("Data")

    if movimentar(dados, codigo, tipo, quantidade, documento, data):
        unidade = dados["itens"][codigo]["unidade"]
        saldo = utils.formatar_quantidade(obter_saldo(dados, codigo))
        print(f"Movimentação registrada. Saldo atual: {saldo} {unidade}.")
        exibir_alerta(dados, codigo)


def consultar_kardex(dados):
    """Exibe o saldo e o histórico (kardex) de um item (RF05)."""
    codigo = itens.ler_codigo_existente(dados, "Código do item: ")
    if codigo is None:
        return
    item = dados["itens"][codigo]

    print(f"\nKARDEX - {codigo} {item['descricao']} ({item['unidade']})")
    utils.exibir_linha()
    movimentos = persistencia.ler_movimentos(codigo)
    if not movimentos:
        print("Nenhuma movimentação registrada para este item.")
    else:
        print(f"{'Data':<12}{'Tipo':<9}{'Qtde':>8}{'Saldo':>9}  Documento")
        for mov in movimentos:
            quantidade = utils.formatar_quantidade(mov["quantidade"])
            if mov["quantidade"] > 0:
                quantidade = "+" + quantidade
            saldo = utils.formatar_quantidade(mov["saldo"])
            print(f"{utils.formatar_data(mov['data']):<12}"
                  f"{mov['tipo']:<9}{quantidade:>8}{saldo:>9}  "
                  f"{mov['documento']}")
    utils.exibir_linha()

    saldo = utils.formatar_quantidade(obter_saldo(dados, codigo))
    seguranca = utils.formatar_quantidade(item["estoque_seguranca"])
    print(f"Saldo atual: {saldo} {item['unidade']} | "
          f"Estoque de segurança: {seguranca} {item['unidade']}")
    exibir_alerta(dados, codigo)


def listar_posicao(dados):
    """Lista o saldo de todos os itens, destacando os que estão abaixo
    do estoque de segurança (RF05)."""
    utils.exibir_titulo("POSIÇÃO DE ESTOQUE")
    if not dados["itens"]:
        print("Nenhum item cadastrado.")
        return

    print(f"{'Código':<8}{'Descrição':<28}{'Saldo':>9}{'Est.Seg.':>10}"
          f"  {'Un':<5}Situação")
    abaixo = 0
    for tipo in utils.TIPOS_ITEM:
        for codigo in sorted(dados["itens"]):
            item = dados["itens"][codigo]
            if item["tipo"] == tipo:
                saldo = obter_saldo(dados, codigo)
                if saldo < item["estoque_seguranca"]:
                    situacao = "ABAIXO DO EST. SEG."
                    abaixo += 1
                else:
                    situacao = "OK"
                texto_saldo = utils.formatar_quantidade(saldo)
                texto_es = utils.formatar_quantidade(
                    item["estoque_seguranca"])
                print(f"{codigo:<8}{item['descricao'][:27]:<28}"
                      f"{texto_saldo:>9}{texto_es:>10}"
                      f"  {item['unidade']:<5}{situacao}")
    print(f"\n{abaixo} item(ns) abaixo do estoque de segurança.")
