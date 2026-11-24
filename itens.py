"""Cadastro, listagem e alteração de itens (RF02)."""

import persistencia
import utils

NOMES_TIPO = {
    "PA": "Produto acabado",
    "SA": "Semiacabado",
    "MP": "Matéria-prima",
}


def ler_codigo_existente(dados, mensagem):
    """Lê um código e o devolve se o item estiver cadastrado.

    Devolve None se o item não existir.
    """
    codigo = utils.ler_codigo(mensagem)
    if codigo not in dados["itens"]:
        print(f"ERRO: o item {codigo} não está cadastrado.")
        return None
    return codigo


def exibir_detalhes(codigo, item):
    """Exibe todos os campos de um item, um por linha."""
    print(f"Código ............ {codigo}")
    print(f"Descrição ......... {item['descricao']}")
    print(f"Tipo .............. {item['tipo']} - "
          f"{NOMES_TIPO[item['tipo']]}")
    print(f"Unidade ........... {item['unidade']}")
    print(f"Custo unitário .... "
          f"{utils.formatar_moeda(item['custo_unitario'])}")
    print(f"Lead time ......... {item['lead_time']} semana(s)")
    print(f"Estoque segurança . "
          f"{utils.formatar_quantidade(item['estoque_seguranca'])}")
    print(f"Lote mínimo ....... "
          f"{utils.formatar_quantidade(item['lote_minimo'])}")


def cadastrar_item(dados):
    """Cadastra um item novo e salva os dados (RF02, RN01)."""
    utils.exibir_titulo("CADASTRAR ITEM")
    codigo = utils.ler_codigo("Código (ex.: PA-001): ")
    if codigo in dados["itens"]:
        print(f"ERRO: o código {codigo} já está cadastrado.")
        return

    tipo = codigo[:2]
    print(f"Tipo: {tipo} - {NOMES_TIPO[tipo]}")

    item = {
        "descricao": utils.ler_texto("Descrição: "),
        "tipo": tipo,
        "unidade": utils.ler_texto("Unidade de medida (un, m, L...): "),
        "custo_unitario": utils.ler_decimal("Custo unitário (R$): ", 0),
        "lead_time": utils.ler_inteiro("Lead time (semanas): ", 0),
        "estoque_seguranca": utils.ler_decimal("Estoque de segurança: ",
                                               0),
        "lote_minimo": utils.ler_decimal("Lote mínimo: ", 0),
    }

    dados["itens"][codigo] = item
    persistencia.salvar_dados(dados)
    print(f"Item {codigo} cadastrado com sucesso.")


def listar_itens(dados):
    """Lista todos os itens, agrupados por tipo (PA, SA e MP)."""
    utils.exibir_titulo("ITENS CADASTRADOS")
    if not dados["itens"]:
        print("Nenhum item cadastrado.")
        return

    print(f"{'Código':<8}{'Descrição':<28}{'Un':<5}{'Custo':>13}"
          f"{'LT':>4}{'ES':>7}{'Lote':>7}")
    for tipo in utils.TIPOS_ITEM:
        for codigo in sorted(dados["itens"]):
            item = dados["itens"][codigo]
            if item["tipo"] == tipo:
                custo = utils.formatar_moeda(item["custo_unitario"])
                es = utils.formatar_quantidade(item["estoque_seguranca"])
                lote = utils.formatar_quantidade(item["lote_minimo"])
                print(f"{codigo:<8}{item['descricao'][:27]:<28}"
                      f"{item['unidade']:<5}{custo:>13}"
                      f"{item['lead_time']:>4}{es:>7}{lote:>7}")
    print(f"\nTotal: {len(dados['itens'])} item(ns).")


def alterar_item(dados):
    """Altera um campo de um item cadastrado (RF02).

    O código e o tipo não podem ser alterados, pois identificam o item.
    """
    utils.exibir_titulo("ALTERAR ITEM")
    codigo = ler_codigo_existente(dados, "Código do item: ")
    if codigo is None:
        return

    item = dados["itens"][codigo]
    exibir_detalhes(codigo, item)
    print("\nCampos que podem ser alterados:")
    print(" 1. Descrição")
    print(" 2. Unidade de medida")
    print(" 3. Custo unitário")
    print(" 4. Lead time")
    print(" 5. Estoque de segurança")
    print(" 6. Lote mínimo")
    print(" 0. Cancelar")
    campo = utils.ler_inteiro("Escolha o campo: ", 0, 6)

    if campo == 0:
        print("Alteração cancelada.")
        return
    elif campo == 1:
        item["descricao"] = utils.ler_texto("Nova descrição: ")
    elif campo == 2:
        item["unidade"] = utils.ler_texto("Nova unidade: ")
    elif campo == 3:
        item["custo_unitario"] = utils.ler_decimal("Novo custo (R$): ", 0)
    elif campo == 4:
        item["lead_time"] = utils.ler_inteiro("Novo lead time: ", 0)
    elif campo == 5:
        item["estoque_seguranca"] = utils.ler_decimal(
            "Novo estoque de segurança: ", 0)
    elif campo == 6:
        item["lote_minimo"] = utils.ler_decimal("Novo lote mínimo: ", 0)

    persistencia.salvar_dados(dados)
    print(f"Item {codigo} alterado com sucesso.")
