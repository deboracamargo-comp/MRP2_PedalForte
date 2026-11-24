"""Exportação de relatórios em CSV (RF14)."""

import estoque
import ordens
import persistencia
import utils


def exportar_estoque(dados):
    """Exporta a posição de estoque de todos os itens em CSV (RF14)."""
    utils.exibir_titulo("EXPORTAR POSIÇÃO DE ESTOQUE")
    if not dados["itens"]:
        print("Nenhum item cadastrado.")
        return

    campos = ["codigo", "descricao", "tipo", "unidade", "saldo",
              "estoque_seguranca", "situacao"]
    linhas = []
    for tipo in utils.TIPOS_ITEM:
        for codigo in sorted(dados["itens"]):
            item = dados["itens"][codigo]
            if item["tipo"] == tipo:
                saldo = estoque.obter_saldo(dados, codigo)
                if saldo < item["estoque_seguranca"]:
                    situacao = "ABAIXO DO ESTOQUE DE SEGURANCA"
                else:
                    situacao = "OK"
                linhas.append({
                    "codigo": codigo,
                    "descricao": item["descricao"],
                    "tipo": item["tipo"],
                    "unidade": item["unidade"],
                    "saldo": utils.formatar_quantidade(saldo),
                    "estoque_seguranca": utils.formatar_quantidade(
                        item["estoque_seguranca"]),
                    "situacao": situacao,
                })

    caminho = persistencia.exportar_csv("posicao_estoque.csv", campos,
                                        linhas)
    print(f"{len(linhas)} item(ns) exportado(s) para {caminho}")


def exportar_ordens(dados):
    """Exporta a lista de ordens de produção e de compra em CSV (RF14)."""
    utils.exibir_titulo("EXPORTAR LISTA DE ORDENS")
    if not dados["ordens"]:
        print("Nenhuma ordem cadastrada. Execute o MRP antes.")
        return

    campos = ["ordem", "tipo", "item", "descricao", "quantidade",
              "semana_liberacao", "semana_entrega", "status"]
    linhas = []
    for tipo in ["OP", "OC"]:
        for numero in sorted(dados["ordens"]):
            if numero.startswith(tipo):
                ordem = dados["ordens"][numero]
                linhas.append({
                    "ordem": numero,
                    "tipo": ordem["tipo"],
                    "item": ordem["item"],
                    "descricao": dados["itens"][ordem["item"]]["descricao"],
                    "quantidade": utils.formatar_quantidade(
                        ordem["quantidade"]),
                    "semana_liberacao": ordem["semana_liberacao"],
                    "semana_entrega": ordem["semana_entrega"],
                    "status": ordens.texto_status(ordem),
                })

    caminho = persistencia.exportar_csv("ordens.csv", campos, linhas)
    print(f"{len(linhas)} ordem(ns) exportada(s) para {caminho}")
