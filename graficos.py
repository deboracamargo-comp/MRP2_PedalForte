"""Gráficos de gestão e acompanhamento com matplotlib (RF16).

Cada gráfico é exibido na tela e salvo em PNG na pasta exports/.
"""

import matplotlib.pyplot as plt

import capacidade
import estoque
import itens
import mps
import mrp
import persistencia
import utils

# Cores (paleta validada para daltonismo e contraste)
COR_1 = "#2a78d6"        # azul: primeira série
COR_2 = "#eb6834"        # laranja: segunda série
COR_ALERTA = "#d03b3b"   # vermelho: sobrecarga (sempre com texto)
COR_REFERENCIA = "#52514e"  # cinza: linhas de referência
COR_FUNDO = "#fcfcfb"

SEMANAS = list(range(1, mps.HORIZONTE + 1))


def preparar_grafico(titulo, rotulo_y):
    """Cria a figura com o estilo padrão do sistema."""
    figura, eixo = plt.subplots(figsize=(10, 5))
    figura.patch.set_facecolor(COR_FUNDO)
    eixo.set_facecolor(COR_FUNDO)
    eixo.set_title(titulo, loc="left", fontsize=13)
    eixo.set_ylabel(rotulo_y)
    eixo.spines["top"].set_visible(False)
    eixo.spines["right"].set_visible(False)
    eixo.grid(axis="y", color="#e5e4e0", linewidth=0.8)
    eixo.set_axisbelow(True)
    return figura, eixo


def finalizar(figura, nome_arquivo):
    """Salva o gráfico em PNG na pasta exports/ e o exibe na tela."""
    figura.tight_layout()
    caminho = persistencia.caminho_exportacao(nome_arquivo)
    figura.savefig(caminho, dpi=120)
    print(f"Gráfico salvo em {caminho}")
    plt.show()
    plt.close(figura)


def grafico_posicao_estoque(dados):
    """Barras: saldo atual x estoque de segurança de cada item."""
    if not dados["itens"]:
        print("Nenhum item cadastrado.")
        return

    codigos = []
    for tipo in utils.TIPOS_ITEM:
        for codigo in sorted(dados["itens"]):
            if dados["itens"][codigo]["tipo"] == tipo:
                codigos.append(codigo)
    saldos = []
    segurancas = []
    for codigo in codigos:
        saldos.append(estoque.obter_saldo(dados, codigo))
        segurancas.append(dados["itens"][codigo]["estoque_seguranca"])

    posicoes = list(range(len(codigos)))
    largura = 0.38
    esquerda = []
    direita = []
    for posicao in posicoes:
        esquerda.append(posicao - largura / 2)
        direita.append(posicao + largura / 2)

    figura, eixo = preparar_grafico("Posição de estoque: saldo atual x "
                                    "estoque de segurança", "Quantidade")
    eixo.bar(esquerda, saldos, largura, color=COR_1, label="Saldo atual",
             edgecolor=COR_FUNDO, linewidth=1)
    eixo.bar(direita, segurancas, largura, color=COR_2,
             label="Estoque de segurança", edgecolor=COR_FUNDO, linewidth=1)
    eixo.set_xticks(posicoes)
    eixo.set_xticklabels(codigos, rotation=45, ha="right")
    eixo.legend(frameon=False)
    finalizar(figura, "grafico_posicao_estoque.png")


def grafico_estoque_projetado(dados):
    """Linha: estoque projetado de um item nas 8 semanas do MRP, com a
    linha do estoque de segurança."""
    codigo = itens.ler_codigo_existente(dados, "Código do item: ")
    if codigo is None:
        return
    registro = mrp.calcular_mrp(dados)[codigo]
    seguranca = dados["itens"][codigo]["estoque_seguranca"]

    figura, eixo = preparar_grafico(
        f"Estoque projetado - {codigo} "
        f"{dados['itens'][codigo]['descricao']}", "Quantidade")
    eixo.plot(SEMANAS, registro["estoque_projetado"], color=COR_1,
              linewidth=2, marker="o", markersize=7, label="Estoque projetado")
    eixo.axhline(seguranca, color=COR_REFERENCIA, linewidth=1.5,
                 linestyle="--", label="Estoque de segurança")
    eixo.set_ylim(bottom=0)
    eixo.set_xticks(SEMANAS)
    eixo.set_xlabel("Semana")
    eixo.legend(frameon=False)
    finalizar(figura, f"grafico_estoque_projetado_{codigo}.png")


def grafico_ordens_por_semana(dados):
    """Barras empilhadas: quantidade de ordens (OP e OC) por semana de
    entrega, sem as ordens já encerradas."""
    quantidade_op = [0] * mps.HORIZONTE
    quantidade_oc = [0] * mps.HORIZONTE
    for ordem in dados["ordens"].values():
        semana = ordem["semana_entrega"]
        if ordem["status"] != "ENCERRADA" and 1 <= semana <= mps.HORIZONTE:
            if ordem["tipo"] == "OP":
                quantidade_op[semana - 1] += 1
            else:
                quantidade_oc[semana - 1] += 1
    if sum(quantidade_op) + sum(quantidade_oc) == 0:
        print("Nenhuma ordem em aberto. Execute o MRP antes.")
        return

    figura, eixo = preparar_grafico("Ordens por semana de entrega",
                                    "Número de ordens")
    eixo.bar(SEMANAS, quantidade_op, color=COR_1, label="OP (produção)",
             edgecolor=COR_FUNDO, linewidth=2)
    eixo.bar(SEMANAS, quantidade_oc, bottom=quantidade_op, color=COR_2,
             label="OC (compra)", edgecolor=COR_FUNDO, linewidth=2)
    eixo.set_xticks(SEMANAS)
    eixo.set_xlabel("Semana de entrega")
    eixo.legend(frameon=False)
    finalizar(figura, "grafico_ordens_por_semana.png")


def grafico_carga_capacidade(dados):
    """Barras: carga x capacidade de um centro por semana, destacando as
    semanas com sobrecarga."""
    if not dados["centros"]:
        print("Nenhum centro de trabalho cadastrado.")
        return
    print("Centros disponíveis: " + ", ".join(sorted(dados["centros"])))
    centro = capacidade.ler_centro_existente(dados, "Centro de trabalho: ")
    if centro is None:
        return

    limite = dados["centros"][centro]["capacidade_horas"]
    carga = capacidade.calcular_carga(dados, centro)
    cores = []
    for horas in carga:
        if horas > limite:
            cores.append(COR_ALERTA)
        else:
            cores.append(COR_1)

    figura, eixo = preparar_grafico(
        f"Carga x capacidade - {centro} "
        f"{dados['centros'][centro]['descricao']}", "Horas")
    eixo.bar(SEMANAS, carga, color=cores, edgecolor=COR_FUNDO, linewidth=2,
             label="Carga")
    eixo.axhline(limite, color=COR_REFERENCIA, linewidth=1.5,
                 linestyle="--", label="Capacidade")
    for semana in SEMANAS:
        if carga[semana - 1] > limite:
            eixo.text(semana, carga[semana - 1], "SOBRECARGA",
                      ha="center", va="bottom", fontsize=9)
    eixo.set_xticks(SEMANAS)
    eixo.set_xlabel("Semana")
    eixo.legend(frameon=False)
    finalizar(figura, f"grafico_carga_{centro}.png")
