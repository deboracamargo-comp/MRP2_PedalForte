"""Interface gráfica do sistema MRP II - Pedal Forte Bicicletas.

Bônus da RNF08, feita com Tkinter (biblioteca padrão do Python) e
matplotlib (gráficos dentro das telas). Toda a lógica de negócio vem dos
mesmos módulos usados pelo modo texto: esta interface só mostra os dados
e chama as funções de cálculo (MRP, CRP, custos, estoque).

Para executar: python3 gui.py
"""

import contextlib
import io
import os
import subprocess
import sys
import tkinter as tk
from datetime import datetime
from tkinter import font as tkfont
from tkinter import messagebox, ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator

import capacidade
import custos
import estoque
import estrutura
import mps
import mrp
import ordens
import persistencia
import relatorios
import utils

# ---------------------------------------------------------------------
# Aparência
# ---------------------------------------------------------------------

FUNDO = "#f3f4f6"
CARTAO = "#ffffff"
BORDA = "#e2e4e8"
LATERAL = "#1b2533"
LATERAL_HOVER = "#273246"
TEXTO = "#1f2328"
TEXTO_2 = "#5b6470"
TEXTO_LATERAL = "#c9d1dc"
AZUL = "#2a78d6"
AZUL_ESCURO = "#1f62b3"
LARANJA = "#eb6834"
VERMELHO = "#d03b3b"
VERDE = "#2e9e5b"
CINZA = "#52514e"
FUNDO_ALERTA = "#fdecec"
FUNDO_AVISO = "#fff3e6"
FUNDO_FIRME = "#e8f1fc"
FUNDO_OK = "#e9f6ee"

PAGINAS = [
    ("painel", "Painel"),
    ("itens", "Itens"),
    ("estrutura", "Estrutura (BOM)"),
    ("estoque", "Estoque"),
    ("mps", "Plano mestre (MPS)"),
    ("mrp", "MRP"),
    ("ordens", "Ordens"),
    ("capacidade", "Capacidade (CRP)"),
    ("custos", "Custo padrão"),
    ("relatorios", "Relatórios"),
]

SUBTITULOS = {
    "painel": "Visão geral da fábrica e alertas",
    "itens": "Cadastro de produtos, semiacabados e matérias-primas (RF02)",
    "estrutura": "Estrutura de produto em até 3 níveis (RF03, RN03)",
    "estoque": "Movimentações, saldo e kardex (RF04, RF05)",
    "mps": "Demanda dos produtos acabados nas 8 semanas (RF07)",
    "mrp": "Cálculo das necessidades e registro por item (RF08, RF09)",
    "ordens": "Ciclo de status e apontamento de produção (RF10, RF11)",
    "capacidade": "Carga x capacidade, centros e roteiros (RF06, RF12)",
    "custos": "Materiais + mão de obra, pela estrutura (RF13)",
    "relatorios": "Exportação CSV e gráficos em PNG (RF14, RF16)",
}

NOMES_TIPO = {"PA": "Produto acabado", "SA": "Semiacabado",
              "MP": "Matéria-prima"}
SEMANAS = list(range(1, mps.HORIZONTE + 1))


# ---------------------------------------------------------------------
# Funções auxiliares (sem interface)
# ---------------------------------------------------------------------

def converter_numero(texto, campo, minimo=None, inteiro=False):
    """Converte o texto de um campo em número, aceitando vírgula.

    Gera ValueError com uma mensagem amigável se o valor for inválido.
    """
    texto = texto.strip().replace(",", ".")
    try:
        if inteiro:
            valor = int(texto)
        else:
            valor = float(texto)
    except ValueError:
        raise ValueError(f"{campo}: digite um número válido.") from None
    if minimo is not None and valor < minimo:
        raise ValueError(f"{campo}: o valor mínimo é "
                         f"{utils.formatar_quantidade(minimo)}.")
    return valor


def capturar_saida(funcao, *argumentos):
    """Executa uma função do modo texto e devolve (resultado, texto que
    ela escreveu com print). Assim reaproveitamos as mensagens."""
    saida = io.StringIO()
    with contextlib.redirect_stdout(saida):
        resultado = funcao(*argumentos)
    return resultado, saida.getvalue().strip()


def estilizar_eixo(eixo, titulo, rotulo_y):
    """Aplica o estilo padrão dos gráficos do sistema."""
    eixo.set_title(titulo, loc="left", fontsize=11, color=TEXTO)
    eixo.set_ylabel(rotulo_y, color=TEXTO_2)
    eixo.spines["top"].set_visible(False)
    eixo.spines["right"].set_visible(False)
    eixo.spines["left"].set_color(BORDA)
    eixo.spines["bottom"].set_color(BORDA)
    eixo.tick_params(colors=TEXTO_2, labelsize=9)
    eixo.grid(axis="y", color="#eceef1", linewidth=0.8)
    eixo.set_axisbelow(True)


def nova_figura(largura=6.0, altura=3.2):
    """Cria uma figura do matplotlib (sem pyplot) para usar no Tkinter."""
    figura = Figure(figsize=(largura, altura), dpi=100, facecolor=CARTAO)
    eixo = figura.add_subplot(111)
    eixo.set_facecolor(CARTAO)
    return figura, eixo


# ---------------------------------------------------------------------
# Aplicação
# ---------------------------------------------------------------------

class AplicativoMRP:
    """Janela principal: menu lateral à esquerda e a página à direita.

    Cada página é montada do zero quando é aberta (métodos 'pagina_...'),
    então sempre mostra os dados atualizados.
    """

    def __init__(self, janela):
        self.janela = janela
        self.dados = persistencia.carregar_dados()
        self.pagina_atual = "painel"
        self.botoes_menu = {}
        self.excecoes = []
        self.resumo_mrp = ""

        janela.title("MRP II - Pedal Forte Bicicletas")
        janela.geometry("1320x800")
        janela.minsize(1180, 720)
        janela.configure(bg=FUNDO)

        self.criar_fontes()
        self.criar_estilos()
        self.criar_menu_lateral()

        area = tk.Frame(janela, bg=FUNDO)
        area.pack(side="left", fill="both", expand=True)
        self.criar_cabecalho(area)
        self.status = tk.StringVar(value="Dados carregados de data/.")
        tk.Label(area, textvariable=self.status, bg=FUNDO, fg=TEXTO_2,
                 font=self.fonte_pequena, anchor="w").pack(
            side="bottom", fill="x", padx=24, pady=(0, 8))
        self.conteudo = tk.Frame(area, bg=FUNDO)
        self.conteudo.pack(fill="both", expand=True, padx=24, pady=(0, 8))

        self.mostrar("painel")

    # ----- aparência --------------------------------------------------

    def criar_fontes(self):
        """Escolhe a fonte disponível no sistema (Windows ou Linux)."""
        familias = tkfont.families()
        if "Segoe UI" in familias:
            familia = "Segoe UI"
        elif "DejaVu Sans" in familias:
            familia = "DejaVu Sans"
        else:
            familia = "Helvetica"
        self.familia = familia
        self.fonte = (familia, 10)
        self.fonte_pequena = (familia, 9)
        self.fonte_negrito = (familia, 10, "bold")
        self.fonte_titulo = (familia, 20, "bold")
        self.fonte_cartao = (familia, 12, "bold")
        self.fonte_numero = (familia, 26, "bold")

    def criar_estilos(self):
        """Configura o visual dos componentes ttk (tabelas, caixas)."""
        estilo = ttk.Style(self.janela)
        estilo.theme_use("clam")
        estilo.configure("Treeview", font=self.fonte, rowheight=27,
                         background=CARTAO, fieldbackground=CARTAO,
                         foreground=TEXTO, borderwidth=0)
        estilo.configure("Treeview.Heading", font=self.fonte_negrito,
                         background="#eef0f3", foreground=TEXTO,
                         relief="flat", padding=(6, 5))
        estilo.map("Treeview", background=[("selected", AZUL)],
                   foreground=[("selected", "#ffffff")])
        estilo.map("Treeview.Heading", background=[("active", "#e3e6ea")])
        estilo.configure("TCombobox", padding=5)
        estilo.configure("TEntry", padding=5)
        estilo.configure("TNotebook", background=FUNDO, borderwidth=0)
        estilo.configure("TNotebook.Tab", font=self.fonte_negrito,
                         padding=(16, 7), background="#e6e8ec",
                         foreground=TEXTO_2)
        estilo.map("TNotebook.Tab", background=[("selected", CARTAO)],
                   foreground=[("selected", AZUL)])
        estilo.configure("TRadiobutton", background=CARTAO, font=self.fonte)
        estilo.configure("Vertical.TScrollbar", background="#e6e8ec",
                         troughcolor=CARTAO, borderwidth=0, arrowsize=12)

    # ----- estrutura da janela ----------------------------------------

    def criar_menu_lateral(self):
        """Monta a barra lateral escura com o logotipo e as páginas."""
        lateral = tk.Frame(self.janela, bg=LATERAL, width=230)
        lateral.pack(side="left", fill="y")
        lateral.pack_propagate(False)

        logo = tk.Canvas(lateral, width=190, height=70, bg=LATERAL,
                         highlightthickness=0)
        logo.pack(pady=(22, 4), padx=20, anchor="w")
        self.desenhar_bicicleta(logo)
        tk.Label(lateral, text="PEDAL FORTE", bg=LATERAL, fg="#ffffff",
                 font=(self.familia, 15, "bold")).pack(anchor="w", padx=22)
        tk.Label(lateral, text="Sistema MRP II", bg=LATERAL, fg=LARANJA,
                 font=self.fonte_negrito).pack(anchor="w", padx=22,
                                               pady=(0, 18))

        for chave, nome in PAGINAS:
            botao = tk.Label(lateral, text="   " + nome, bg=LATERAL,
                             fg=TEXTO_LATERAL, font=(self.familia, 11),
                             anchor="w", padx=14, pady=9, cursor="hand2")
            botao.pack(fill="x")
            botao.bind("<Button-1>",
                       lambda evento, pagina=chave: self.mostrar(pagina))
            botao.bind("<Enter>",
                       lambda evento, pagina=chave: self.passar_mouse(
                           pagina, True))
            botao.bind("<Leave>",
                       lambda evento, pagina=chave: self.passar_mouse(
                           pagina, False))
            self.botoes_menu[chave] = botao

        tk.Label(lateral, text="Divinópolis - MG\nCEFET-MG  ·  2026/2",
                 bg=LATERAL, fg="#7f8a99", font=self.fonte_pequena,
                 justify="left").pack(side="bottom", anchor="w",
                                      padx=22, pady=18)

    def desenhar_bicicleta(self, tela):
        """Desenha um pequeno logotipo de bicicleta no Canvas."""
        tela.create_oval(4, 26, 48, 70, outline=LARANJA, width=4)
        tela.create_oval(78, 26, 122, 70, outline=LARANJA, width=4)
        tela.create_line(26, 48, 52, 22, 92, 22, 100, 48, fill="#ffffff",
                         width=4, joinstyle="round")
        tela.create_line(26, 48, 62, 48, 52, 22, fill="#ffffff", width=4)
        tela.create_line(62, 48, 92, 22, fill="#ffffff", width=4)
        tela.create_line(46, 14, 58, 14, fill="#ffffff", width=4,
                         capstyle="round")
        tela.create_line(88, 10, 92, 22, fill="#ffffff", width=4)
        tela.create_line(84, 10, 96, 10, fill="#ffffff", width=4,
                         capstyle="round")
        tela.create_oval(58, 44, 66, 52, fill=LARANJA, outline=LARANJA)

    def criar_cabecalho(self, area):
        """Título e subtítulo da página atual, com a data à direita."""
        topo = tk.Frame(area, bg=FUNDO)
        topo.pack(fill="x", padx=24, pady=(20, 12))
        textos = tk.Frame(topo, bg=FUNDO)
        textos.pack(side="left")
        self.titulo = tk.Label(textos, bg=FUNDO, fg=TEXTO,
                               font=self.fonte_titulo)
        self.titulo.pack(anchor="w")
        self.subtitulo = tk.Label(textos, bg=FUNDO, fg=TEXTO_2,
                                  font=self.fonte)
        self.subtitulo.pack(anchor="w")
        hoje = utils.formatar_data(utils.data_hoje())
        tk.Label(topo, text=f"Hoje: {hoje}", bg=FUNDO, fg=TEXTO_2,
                 font=self.fonte_negrito).pack(side="right", anchor="n")

    def passar_mouse(self, pagina, entrou):
        """Destaca o item do menu quando o mouse passa por cima."""
        if pagina == self.pagina_atual:
            return
        botao = self.botoes_menu[pagina]
        if entrou:
            botao.configure(bg=LATERAL_HOVER, fg="#ffffff")
        else:
            botao.configure(bg=LATERAL, fg=TEXTO_LATERAL)

    def mostrar(self, pagina):
        """Abre uma página: apaga o conteúdo atual e monta a nova."""
        self.pagina_atual = pagina
        for chave, botao in self.botoes_menu.items():
            if chave == pagina:
                botao.configure(bg=AZUL, fg="#ffffff",
                                font=(self.familia, 11, "bold"))
            else:
                botao.configure(bg=LATERAL, fg=TEXTO_LATERAL,
                                font=(self.familia, 11))
        for nome_pagina, nome in PAGINAS:
            if nome_pagina == pagina:
                self.titulo.configure(text=nome)
        self.subtitulo.configure(text=SUBTITULOS[pagina])

        for widget in self.conteudo.winfo_children():
            widget.destroy()
        metodo = getattr(self, "pagina_" + pagina)
        metodo()

    def atualizar(self, mensagem=None):
        """Salva os dados, recarrega a página atual e mostra a mensagem
        na barra de status."""
        persistencia.salvar_dados(self.dados)
        self.mostrar(self.pagina_atual)
        if mensagem:
            self.status.set(mensagem)

    # ----- componentes reutilizáveis ----------------------------------

    def cartao(self, pai, titulo=None, grade=None, **opcoes_pack):
        """Cria um cartão branco com borda e, se houver, um título.

        Se 'grade' for informada, o cartão é posicionado com grid;
        senão, com pack (usando as opções recebidas).
        """
        moldura = tk.Frame(pai, bg=CARTAO, highlightthickness=1,
                           highlightbackground=BORDA,
                           highlightcolor=BORDA)
        if grade is None:
            moldura.pack(**opcoes_pack)
        else:
            moldura.grid(**grade)
        if titulo:
            tk.Label(moldura, text=titulo, bg=CARTAO, fg=TEXTO,
                     font=self.fonte_cartao, anchor="w").pack(
                fill="x", padx=16, pady=(12, 6))
        interno = tk.Frame(moldura, bg=CARTAO)
        interno.pack(fill="both", expand=True, padx=16, pady=(0, 14))
        return interno

    def botao(self, pai, texto, comando, tipo="primario"):
        """Cria um botão no estilo do sistema."""
        cores = {
            "primario": (AZUL, "#ffffff", AZUL_ESCURO),
            "secundario": ("#e8ebef", TEXTO, "#d9dde3"),
            "perigo": (VERMELHO, "#ffffff", "#a92f2f"),
            "destaque": (LARANJA, "#ffffff", "#c9552a"),
        }
        fundo, frente, ativo = cores[tipo]
        return tk.Button(pai, text=texto, command=comando, bg=fundo,
                         fg=frente, activebackground=ativo,
                         activeforeground=frente, relief="flat", bd=0,
                         font=self.fonte_negrito, padx=14, pady=7,
                         cursor="hand2")

    def tabela(self, pai, colunas, altura=10, arvore=False):
        """Cria uma tabela (Treeview) com barra de rolagem.

        'colunas' é uma lista de tuplas (id, título, largura, alinhamento).
        """
        moldura = tk.Frame(pai, bg=CARTAO)
        moldura.pack(fill="both", expand=True)
        ids = []
        for coluna in colunas:
            ids.append(coluna[0])
        if arvore:
            exibir = "tree headings"
        else:
            exibir = "headings"
        tabela = ttk.Treeview(moldura, columns=ids, show=exibir,
                              height=altura)
        for identificador, titulo, largura, alinhamento in colunas:
            tabela.heading(identificador, text=titulo, anchor=alinhamento)
            if identificador == "descricao":
                # A descrição começa estreita e cresce para ocupar o
                # espaço que sobrar (o Tk só aumenta colunas, não diminui).
                tabela.column(identificador, width=110, minwidth=80,
                              anchor=alinhamento, stretch=True)
            else:
                tabela.column(identificador, width=largura,
                              anchor=alinhamento, stretch=False)
        rolagem = ttk.Scrollbar(moldura, orient="vertical",
                                command=tabela.yview)
        tabela.configure(yscrollcommand=rolagem.set)
        rolagem.pack(side="right", fill="y")
        tabela.pack(side="left", fill="both", expand=True)
        tabela.tag_configure("par", background="#f8f9fb")
        tabela.tag_configure("alerta", background=FUNDO_ALERTA,
                             foreground="#8a1c1c")
        tabela.tag_configure("aviso", background=FUNDO_AVISO)
        tabela.tag_configure("firme", background=FUNDO_FIRME)
        tabela.tag_configure("ok", background=FUNDO_OK,
                             foreground="#4c6b57")
        return tabela

    def campo(self, pai, linha, rotulo, largura=18):
        """Cria um rótulo e uma caixa de texto em uma linha do grid."""
        tk.Label(pai, text=rotulo, bg=CARTAO, fg=TEXTO_2,
                 font=self.fonte).grid(row=linha, column=0, sticky="w",
                                       pady=4, padx=(0, 10))
        caixa = ttk.Entry(pai, width=largura, font=self.fonte)
        caixa.grid(row=linha, column=1, sticky="we", pady=4)
        return caixa

    def lista(self, pai, linha, rotulo, valores, largura=24):
        """Cria um rótulo e uma lista de escolha (Combobox)."""
        tk.Label(pai, text=rotulo, bg=CARTAO, fg=TEXTO_2,
                 font=self.fonte).grid(row=linha, column=0, sticky="w",
                                       pady=4, padx=(0, 10))
        caixa = ttk.Combobox(pai, values=valores, width=largura - 2,
                             state="readonly", font=self.fonte)
        caixa.grid(row=linha, column=1, sticky="we", pady=4)
        return caixa

    def mostrar_grafico(self, pai, figura, nome_png):
        """Coloca uma figura do matplotlib dentro da página, com um botão
        para salvá-la em PNG na pasta exports/ (RF16)."""
        figura.tight_layout()
        tela = FigureCanvasTkAgg(figura, master=pai)
        tela.draw()
        tela.get_tk_widget().pack(fill="both", expand=True)
        rodape = tk.Frame(pai, bg=CARTAO)
        rodape.pack(fill="x", pady=(6, 0))
        self.botao(rodape, "Salvar PNG",
                   lambda: self.salvar_png(figura, nome_png),
                   "secundario").pack(side="right")

    def salvar_png(self, figura, nome_png):
        """Grava uma figura em PNG na pasta exports/."""
        caminho = persistencia.caminho_exportacao(nome_png)
        figura.savefig(caminho, dpi=120, facecolor=CARTAO)
        self.status.set(f"Gráfico salvo em {caminho}")

    def descricao(self, codigo):
        """Devolve 'CÓDIGO - descrição' para as listas de escolha."""
        return f"{codigo} - {self.dados['itens'][codigo]['descricao']}"

    def codigos(self, tipos):
        """Lista os códigos dos itens dos tipos pedidos, em ordem."""
        resultado = []
        for tipo in tipos:
            for codigo in sorted(self.dados["itens"]):
                if self.dados["itens"][codigo]["tipo"] == tipo:
                    resultado.append(codigo)
        return resultado

    def opcoes_itens(self, tipos):
        """Lista 'CÓDIGO - descrição' dos itens dos tipos pedidos."""
        opcoes = []
        for codigo in self.codigos(tipos):
            opcoes.append(self.descricao(codigo))
        return opcoes

    # ----- figuras (usadas nas páginas e na exportação em PNG) --------

    def figura_carga(self, centro, largura=6.0, altura=3.2):
        """Barras de carga x capacidade de um centro (RF12, RF16)."""
        limite = self.dados["centros"][centro]["capacidade_horas"]
        carga = capacidade.calcular_carga(self.dados, centro)
        cores = []
        for horas in carga:
            if horas > limite:
                cores.append(VERMELHO)
            else:
                cores.append(AZUL)
        figura, eixo = nova_figura(largura, altura)
        estilizar_eixo(eixo, f"Carga x capacidade - {centro} "
                       f"{self.dados['centros'][centro]['descricao']}",
                       "Horas")
        eixo.bar(SEMANAS, carga, color=cores, width=0.6, label="Carga")
        eixo.axhline(limite, color=CINZA, linestyle="--", linewidth=1.5,
                     label=f"Capacidade ({utils.formatar_quantidade(limite)}"
                           f" h)")
        for semana in SEMANAS:
            if carga[semana - 1] > limite:
                eixo.text(semana, carga[semana - 1], "SOBRECARGA",
                          ha="center", va="bottom", fontsize=8,
                          color=TEXTO)
        eixo.set_xticks(SEMANAS)
        eixo.set_xlabel("Semana", color=TEXTO_2)
        eixo.set_ylim(0, max(max(carga), limite) * 1.3)
        eixo.legend(frameon=False, fontsize=8, ncol=2, loc="upper left")
        return figura

    def figura_ordens(self, largura=6.0, altura=3.2):
        """Barras empilhadas de ordens em aberto por semana de entrega."""
        quantidade_op = [0] * mps.HORIZONTE
        quantidade_oc = [0] * mps.HORIZONTE
        for ordem in self.dados["ordens"].values():
            semana = ordem["semana_entrega"]
            if ordem["status"] != "ENCERRADA" and 1 <= semana <= 8:
                if ordem["tipo"] == "OP":
                    quantidade_op[semana - 1] += 1
                else:
                    quantidade_oc[semana - 1] += 1
        figura, eixo = nova_figura(largura, altura)
        estilizar_eixo(eixo, "Ordens em aberto por semana de entrega",
                       "Número de ordens")
        eixo.bar(SEMANAS, quantidade_op, color=AZUL, width=0.6,
                 label="OP (produção)", edgecolor=CARTAO, linewidth=1.5)
        eixo.bar(SEMANAS, quantidade_oc, bottom=quantidade_op,
                 color=LARANJA, width=0.6, label="OC (compra)",
                 edgecolor=CARTAO, linewidth=1.5)
        eixo.set_xticks(SEMANAS)
        eixo.set_xlabel("Semana de entrega", color=TEXTO_2)
        eixo.yaxis.set_major_locator(MaxNLocator(integer=True))
        eixo.legend(frameon=False, fontsize=8)
        return figura

    def figura_posicao(self, largura=9.0, altura=3.4):
        """Barras de saldo x estoque de segurança de todos os itens."""
        codigos = self.codigos(utils.TIPOS_ITEM)
        saldos = []
        segurancas = []
        for codigo in codigos:
            saldos.append(estoque.obter_saldo(self.dados, codigo))
            segurancas.append(self.dados["itens"][codigo]
                              ["estoque_seguranca"])
        posicoes = list(range(len(codigos)))
        esquerda = []
        direita = []
        for posicao in posicoes:
            esquerda.append(posicao - 0.2)
            direita.append(posicao + 0.2)
        figura, eixo = nova_figura(largura, altura)
        estilizar_eixo(eixo, "Saldo atual x estoque de segurança "
                       "(escala logarítmica)", "Quantidade")
        eixo.bar(esquerda, saldos, 0.38, color=AZUL, label="Saldo atual")
        eixo.bar(direita, segurancas, 0.38, color=LARANJA,
                 label="Estoque de segurança")
        eixo.set_yscale("symlog")
        eixo.set_xticks(posicoes)
        eixo.set_xticklabels(codigos, rotation=45, ha="right", fontsize=8)
        eixo.legend(frameon=False, fontsize=8)
        return figura

    def figura_projetado(self, codigo, registro, largura=6.0, altura=3.0):
        """Linha do estoque projetado de um item, com o estoque de
        segurança e os recebimentos planejados (RF08, RF16)."""
        item = self.dados["itens"][codigo]
        figura, eixo = nova_figura(largura, altura)
        estilizar_eixo(eixo, f"Estoque projetado - {codigo}",
                       f"Quantidade ({item['unidade']})")
        eixo.bar(SEMANAS, registro["recebimentos_planejados"],
                 color=LARANJA, width=0.5, alpha=0.85,
                 label="Receb. planejado")
        eixo.plot(SEMANAS, registro["estoque_projetado"], color=AZUL,
                  linewidth=2, marker="o", markersize=6,
                  label="Estoque projetado")
        eixo.axhline(item["estoque_seguranca"], color=CINZA,
                     linestyle="--", linewidth=1.5,
                     label="Est. segurança")
        maior = max(max(registro["estoque_projetado"]),
                    max(registro["recebimentos_planejados"]),
                    item["estoque_seguranca"], 1)
        eixo.set_ylim(0, maior * 1.3)
        eixo.set_xticks(SEMANAS)
        eixo.set_xlabel("Semana", color=TEXTO_2)
        eixo.legend(frameon=False, fontsize=8, ncol=3, loc="upper left")
        return figura

    def figura_mps(self, largura=9.0, altura=2.8):
        """Barras agrupadas da demanda do MPS por semana."""
        produtos = sorted(self.dados["mps"])
        figura, eixo = nova_figura(largura, altura)
        estilizar_eixo(eixo, "Demanda do MPS por semana", "Unidades")
        cores = [AZUL, LARANJA, "#7a5cc7", VERDE]
        largura_barra = 0.8 / max(len(produtos), 1)
        for indice in range(len(produtos)):
            codigo = produtos[indice]
            posicoes = []
            for semana in SEMANAS:
                posicoes.append(semana - 0.4 + largura_barra * (indice + 0.5))
            eixo.bar(posicoes, self.dados["mps"][codigo], largura_barra,
                     color=cores[indice % len(cores)], label=codigo)
        eixo.set_xticks(SEMANAS)
        eixo.set_xlabel("Semana", color=TEXTO_2)
        if produtos:
            eixo.legend(frameon=False, fontsize=8)
        return figura

    # =================================================================
    # PÁGINAS
    # =================================================================

    # ----- Painel -----------------------------------------------------

    def pagina_painel(self):
        """Indicadores, gráfico do centro mais carregado e alertas."""
        abaixo = []
        for codigo in self.codigos(utils.TIPOS_ITEM):
            item = self.dados["itens"][codigo]
            if estoque.obter_saldo(self.dados, codigo) < \
                    item["estoque_seguranca"]:
                abaixo.append(codigo)
        abertas = 0
        atrasadas = []
        for numero, ordem in sorted(self.dados["ordens"].items()):
            if ordem["status"] != "ENCERRADA":
                abertas += 1
            if ordens.texto_status(ordem) == "ATRASADA":
                atrasadas.append(numero)
        sobrecargas = []
        centro_critico = None
        maior_uso = -1
        for centro in sorted(self.dados["centros"]):
            limite = self.dados["centros"][centro]["capacidade_horas"]
            carga = capacidade.calcular_carga(self.dados, centro)
            for semana in SEMANAS:
                if carga[semana - 1] > limite:
                    sobrecargas.append((centro, semana))
            if max(carga) / limite > maior_uso:
                maior_uso = max(carga) / limite
                centro_critico = centro

        linha = tk.Frame(self.conteudo, bg=FUNDO)
        linha.pack(fill="x", pady=(0, 14))
        indicadores = [
            ("Itens cadastrados", len(self.dados["itens"]), AZUL),
            ("Abaixo do estoque de segurança", len(abaixo), VERMELHO),
            ("Ordens em aberto", abertas, LARANJA),
            ("Ordens atrasadas", len(atrasadas), VERMELHO),
            ("Semanas com sobrecarga", len(sobrecargas), VERMELHO),
        ]
        for coluna in range(len(indicadores)):
            rotulo, valor, cor = indicadores[coluna]
            self.indicador(linha, rotulo, valor, cor, coluna)

        corpo = tk.Frame(self.conteudo, bg=FUNDO)
        corpo.pack(fill="both", expand=True)
        corpo.columnconfigure(0, weight=3, uniform="painel")
        corpo.columnconfigure(1, weight=2, uniform="painel")
        corpo.rowconfigure(0, weight=1)

        esquerda = tk.Frame(corpo, bg=FUNDO)
        esquerda.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
        if centro_critico is not None:
            caixa = self.cartao(esquerda, "Centro mais carregado",
                                fill="both", expand=True)
            self.mostrar_grafico(caixa, self.figura_carga(centro_critico,
                                                          6.4, 2.8),
                                 f"grafico_carga_{centro_critico}.png")
        else:
            caixa = self.cartao(esquerda, "Centro mais carregado",
                                fill="both", expand=True)
            tk.Label(caixa, text="Cadastre centros de trabalho.",
                     bg=CARTAO, fg=TEXTO_2).pack()

        direita = tk.Frame(corpo, bg=FUNDO)
        direita.grid(row=0, column=1, sticky="nsew")
        caixa = self.cartao(direita, "Alertas", fill="both", expand=True)
        texto = tk.Text(caixa, bg=CARTAO, relief="flat", wrap="word",
                        font=self.fonte, height=12, cursor="arrow")
        texto.pack(fill="both", expand=True)
        texto.tag_configure("titulo", font=self.fonte_negrito,
                            foreground=TEXTO, spacing1=8, spacing3=2)
        texto.tag_configure("critico", foreground=VERMELHO)
        texto.tag_configure("normal", foreground=TEXTO_2)

        texto.insert("end", "Estoque abaixo da segurança\n", "titulo")
        if not abaixo:
            texto.insert("end", "Nenhum item.\n", "normal")
        for codigo in abaixo:
            item = self.dados["itens"][codigo]
            saldo = utils.formatar_quantidade(
                estoque.obter_saldo(self.dados, codigo))
            minimo = utils.formatar_quantidade(item["estoque_seguranca"])
            texto.insert("end", f"• {codigo} {item['descricao']}: "
                         f"{saldo} de {minimo} {item['unidade']}\n",
                         "critico")
        texto.insert("end", "Ordens atrasadas (liberar já)\n", "titulo")
        if not atrasadas:
            texto.insert("end", "Nenhuma ordem atrasada.\n", "normal")
        for numero in atrasadas:
            ordem = self.dados["ordens"][numero]
            texto.insert("end", f"• {numero} {ordem['item']}: liberação "
                         f"na semana {ordem['semana_liberacao']}\n",
                         "critico")
        texto.insert("end", "Sobrecarga de capacidade\n", "titulo")
        if not sobrecargas:
            texto.insert("end", "Nenhuma sobrecarga.\n", "normal")
        for centro, semana in sobrecargas:
            texto.insert("end", f"• {centro} na semana {semana}\n",
                         "critico")
        texto.configure(state="disabled")

        acoes = tk.Frame(caixa, bg=CARTAO)
        acoes.pack(fill="x", pady=(8, 0))
        self.botao(acoes, "Executar MRP", self.executar_mrp_painel,
                   "destaque").pack(side="left")
        self.botao(acoes, "Ver ordens", lambda: self.mostrar("ordens"),
                   "secundario").pack(side="left", padx=8)

    def indicador(self, pai, rotulo, valor, cor, coluna):
        """Cartão com um número grande (indicador do painel)."""
        pai.columnconfigure(coluna, weight=1)
        moldura = tk.Frame(pai, bg=CARTAO, highlightthickness=1,
                           highlightbackground=BORDA,
                           highlightcolor=BORDA)
        moldura.grid(row=0, column=coluna, sticky="nsew",
                     padx=(0 if coluna == 0 else 12, 0))
        tk.Frame(moldura, bg=cor, width=5).pack(side="left", fill="y")
        interno = tk.Frame(moldura, bg=CARTAO)
        interno.pack(side="left", fill="both", expand=True, padx=14,
                     pady=10)
        if valor == 0 and cor == VERMELHO:
            cor_numero = VERDE
        else:
            cor_numero = TEXTO
        tk.Label(interno, text=str(valor), bg=CARTAO, fg=cor_numero,
                 font=self.fonte_numero).pack(anchor="w")
        tk.Label(interno, text=rotulo, bg=CARTAO, fg=TEXTO_2,
                 font=self.fonte_pequena, wraplength=170,
                 justify="left").pack(anchor="w")

    def executar_mrp_painel(self):
        """Executa o MRP a partir do painel e abre a página do MRP."""
        self.executar_mrp(mostrar_pagina=False)
        self.mostrar("mrp")

    # ----- Itens ------------------------------------------------------

    def pagina_itens(self):
        """Tabela de itens com busca e formulário de cadastro/alteração."""
        direita = tk.Frame(self.conteudo, bg=FUNDO)
        direita.pack(side="right", fill="y", padx=(14, 0))
        esquerda = tk.Frame(self.conteudo, bg=FUNDO)
        esquerda.pack(side="left", fill="both", expand=True)

        caixa = self.cartao(esquerda, "Itens cadastrados", fill="both",
                            expand=True)
        busca_linha = tk.Frame(caixa, bg=CARTAO)
        busca_linha.pack(fill="x", pady=(0, 8))
        tk.Label(busca_linha, text="Buscar:", bg=CARTAO, fg=TEXTO_2,
                 font=self.fonte).pack(side="left")
        self.busca_item = ttk.Entry(busca_linha, width=30, font=self.fonte)
        self.busca_item.pack(side="left", padx=8)
        self.busca_item.bind("<KeyRelease>",
                             lambda evento: self.preencher_itens())
        tk.Label(busca_linha, text="• abaixo do est. de segurança",
                 bg=CARTAO, fg=VERMELHO,
                 font=self.fonte_pequena).pack(side="right")

        self.tabela_itens = self.tabela(caixa, [
            ("codigo", "Código", 68, "w"),
            ("descricao", "Descrição", 175, "w"),
            ("tipo", "Tipo", 44, "center"),
            ("un", "Un", 36, "center"),
            ("custo", "Custo un.", 90, "e"),
            ("lt", "LT", 32, "e"),
            ("es", "Est.seg.", 64, "e"),
            ("lote", "Lote", 52, "e"),
            ("saldo", "Saldo", 60, "e"),
        ], altura=18)
        self.tabela_itens.bind("<<TreeviewSelect>>",
                               lambda evento: self.carregar_item())
        self.preencher_itens()

        formulario = self.cartao(direita, "Novo item / alterar item",
                                 fill="x")
        formulario.columnconfigure(1, weight=1)
        self.item_codigo = self.campo(formulario, 0, "Código")
        self.item_tipo = tk.Label(formulario, text="Tipo: -", bg=CARTAO,
                                  fg=AZUL, font=self.fonte_negrito)
        self.item_tipo.grid(row=1, column=1, sticky="w")
        self.item_codigo.bind("<KeyRelease>",
                              lambda evento: self.mostrar_tipo())
        self.item_descricao = self.campo(formulario, 2, "Descrição")
        self.item_unidade = self.campo(formulario, 3, "Unidade")
        self.item_custo = self.campo(formulario, 4, "Custo un. (R$)")
        self.item_lead = self.campo(formulario, 5, "Lead time (sem)")
        self.item_es = self.campo(formulario, 6, "Est. segurança")
        self.item_lote = self.campo(formulario, 7, "Lote mínimo")
        botoes = tk.Frame(formulario, bg=CARTAO)
        botoes.grid(row=8, column=0, columnspan=2, sticky="we",
                    pady=(12, 0))
        self.botao(botoes, "Salvar", self.salvar_item).pack(side="left")
        self.botao(botoes, "Novo", self.limpar_item,
                   "secundario").pack(side="left", padx=8)
        tk.Label(direita, text="Selecione um item na tabela para alterar."
                 "\nO código e o tipo não podem ser alterados.\nO tipo "
                 "vem das 2 primeiras letras do código (RN01).",
                 bg=FUNDO, fg=TEXTO_2, font=self.fonte_pequena,
                 justify="left").pack(anchor="w", pady=10)
        self.limpar_item()

    def preencher_itens(self):
        """Preenche a tabela de itens, aplicando o texto da busca."""
        tabela = self.tabela_itens
        tabela.delete(*tabela.get_children())
        busca = self.busca_item.get().strip().lower()
        contador = 0
        for codigo in self.codigos(utils.TIPOS_ITEM):
            item = self.dados["itens"][codigo]
            texto = (codigo + " " + item["descricao"]).lower()
            if busca and busca not in texto:
                continue
            saldo = estoque.obter_saldo(self.dados, codigo)
            if saldo < item["estoque_seguranca"]:
                etiqueta = "alerta"
            elif contador % 2 == 1:
                etiqueta = "par"
            else:
                etiqueta = ""
            contador += 1
            if item["tipo"] == "MP":
                custo = item["custo_unitario"]
            else:
                custo = custos.custo_padrao(self.dados, codigo)
            tabela.insert("", "end", iid=codigo, tags=(etiqueta,), values=(
                codigo, item["descricao"], item["tipo"], item["unidade"],
                utils.formatar_moeda(custo), item["lead_time"],
                utils.formatar_quantidade(item["estoque_seguranca"]),
                utils.formatar_quantidade(item["lote_minimo"]),
                utils.formatar_quantidade(saldo)))

    def mostrar_tipo(self):
        """Mostra o tipo do item conforme o código digitado."""
        prefixo = self.item_codigo.get().strip().upper()[:2]
        if prefixo in NOMES_TIPO:
            self.item_tipo.configure(text=f"Tipo: {prefixo} - "
                                     f"{NOMES_TIPO[prefixo]}")
        else:
            self.item_tipo.configure(text="Tipo: use PA, SA ou MP")

    def limpar_item(self):
        """Deixa o formulário pronto para um item novo."""
        self.item_editando = None
        self.item_codigo.configure(state="normal")
        caixas = [self.item_codigo, self.item_descricao, self.item_unidade,
                  self.item_custo, self.item_lead, self.item_es,
                  self.item_lote]
        for caixa in caixas:
            caixa.delete(0, "end")
        for caixa, padrao in [(self.item_custo, "0"), (self.item_lead, "1"),
                              (self.item_es, "0"), (self.item_lote, "0")]:
            caixa.insert(0, padrao)
        self.item_tipo.configure(text="Tipo: -")
        self.item_codigo.focus_set()

    def carregar_item(self):
        """Coloca no formulário os dados do item selecionado."""
        selecao = self.tabela_itens.selection()
        if not selecao:
            return
        codigo = selecao[0]
        item = self.dados["itens"][codigo]
        self.limpar_item()
        self.item_editando = codigo
        self.item_codigo.insert(0, codigo)
        self.item_codigo.configure(state="disabled")
        self.mostrar_tipo()
        valores = [
            (self.item_descricao, item["descricao"]),
            (self.item_unidade, item["unidade"]),
            (self.item_custo, utils.formatar_quantidade(
                item["custo_unitario"])),
            (self.item_lead, str(item["lead_time"])),
            (self.item_es, utils.formatar_quantidade(
                item["estoque_seguranca"])),
            (self.item_lote, utils.formatar_quantidade(item["lote_minimo"])),
        ]
        for caixa, valor in valores:
            caixa.delete(0, "end")
            caixa.insert(0, valor)

    def salvar_item(self):
        """Valida o formulário e cadastra ou altera o item (RF02, RN01)."""
        try:
            if self.item_editando is None:
                codigo = self.item_codigo.get().strip().upper()
                if not utils.validar_codigo(codigo):
                    raise ValueError("Código inválido. Use o formato "
                                     "Tipo-Número, ex.: PA-001, MP-201.")
                if codigo in self.dados["itens"]:
                    raise ValueError(f"O código {codigo} já está "
                                     f"cadastrado (RN01).")
            else:
                codigo = self.item_editando
            descricao = self.item_descricao.get().strip()
            unidade = self.item_unidade.get().strip()
            if not descricao or not unidade:
                raise ValueError("Preencha a descrição e a unidade.")
            novo = {
                "descricao": descricao,
                "tipo": codigo[:2],
                "unidade": unidade,
                "custo_unitario": converter_numero(
                    self.item_custo.get(), "Custo unitário", 0),
                "lead_time": converter_numero(
                    self.item_lead.get(), "Lead time", 0, inteiro=True),
                "estoque_seguranca": converter_numero(
                    self.item_es.get(), "Estoque de segurança", 0),
                "lote_minimo": converter_numero(
                    self.item_lote.get(), "Lote mínimo", 0),
            }
        except ValueError as erro:
            messagebox.showerror("Dados inválidos", str(erro))
            return
        if self.item_editando is None:
            mensagem = f"Item {codigo} cadastrado com sucesso."
        else:
            mensagem = f"Item {codigo} alterado com sucesso."
        self.dados["itens"][codigo] = novo
        self.atualizar(mensagem)

    # ----- Estrutura (BOM) --------------------------------------------

    def pagina_estrutura(self):
        """Árvore da BOM (explosão recursiva) e formulário de edição."""
        direita = tk.Frame(self.conteudo, bg=FUNDO)
        direita.pack(side="right", fill="y", padx=(14, 0))
        esquerda = tk.Frame(self.conteudo, bg=FUNDO)
        esquerda.pack(side="left", fill="both", expand=True)

        caixa = self.cartao(esquerda, "Explosão da estrutura", fill="both",
                            expand=True)
        topo = tk.Frame(caixa, bg=CARTAO)
        topo.pack(fill="x", pady=(0, 8))
        tk.Label(topo, text="Produto:", bg=CARTAO, fg=TEXTO_2,
                 font=self.fonte).pack(side="left")
        opcoes = self.opcoes_itens(["PA", "SA"])
        self.bom_produto = ttk.Combobox(topo, values=opcoes, width=40,
                                        state="readonly", font=self.fonte)
        self.bom_produto.pack(side="left", padx=8)
        self.bom_produto.bind("<<ComboboxSelected>>",
                              lambda evento: self.preencher_bom())
        self.arvore_bom = self.tabela(caixa, [
            ("qtde", "Qtde/un", 90, "e"),
            ("un", "Un", 50, "center"),
            ("tipo", "Tipo", 60, "center"),
            ("nivel", "Nível", 60, "center"),
        ], altura=16, arvore=True)
        self.arvore_bom.heading("#0", text="Item", anchor="w")
        self.arvore_bom.column("#0", width=360, anchor="w")
        self.niveis_bom = tk.Label(caixa, bg=CARTAO, fg=TEXTO_2,
                                   font=self.fonte, anchor="w",
                                   justify="left", wraplength=640)
        self.niveis_bom.pack(fill="x", pady=(8, 0))
        if opcoes:
            self.bom_produto.current(0)
            self.preencher_bom()

        formulario = self.cartao(direita, "Adicionar / alterar componente",
                                 fill="x")
        formulario.columnconfigure(1, weight=1)
        self.bom_pai = self.lista(formulario, 0, "Item pai", opcoes)
        self.bom_pai.bind("<<ComboboxSelected>>",
                          lambda evento: self.filtrar_componentes())
        self.bom_componente = self.lista(formulario, 1, "Componente", [])
        self.bom_quantidade = self.campo(formulario, 2, "Quantidade")
        botoes = tk.Frame(formulario, bg=CARTAO)
        botoes.grid(row=3, column=0, columnspan=2, sticky="we",
                    pady=(12, 0))
        self.botao(botoes, "Salvar", self.salvar_componente).pack(
            side="left")
        self.botao(botoes, "Remover", self.remover_componente,
                   "perigo").pack(side="left", padx=8)
        tk.Label(direita, text="RN03: um PA pode ter SA e MP; um SA só "
                 "MP;\numa MP não tem estrutura. A regra também\nimpede "
                 "ciclos na BOM.\n\nSe o componente já estiver no pai, a "
                 "quantidade\né atualizada.", bg=FUNDO, fg=TEXTO_2,
                 font=self.fonte_pequena, justify="left").pack(
            anchor="w", pady=10)
        if opcoes:
            self.bom_pai.current(0)
            self.filtrar_componentes()

    def preencher_bom(self):
        """Monta a árvore do produto escolhido (explosão da BOM)."""
        arvore = self.arvore_bom
        arvore.delete(*arvore.get_children())
        codigo = self.bom_produto.get()[:6]
        if not codigo:
            return
        item = self.dados["itens"][codigo]
        raiz = arvore.insert("", "end", text=self.descricao(codigo),
                             values=("", item["unidade"], item["tipo"], 0),
                             open=True)
        niveis = {0: [codigo]}
        self.inserir_componentes(raiz, codigo, 1, niveis)
        partes = []
        for nivel in sorted(niveis):
            partes.append(f"{nivel} = {', '.join(niveis[nivel])}")
        self.niveis_bom.configure(text="Níveis:  " + "  |  ".join(partes))

    def inserir_componentes(self, no_pai, codigo, nivel, niveis):
        """Insere os componentes de um item na árvore e, de forma
        RECURSIVA, os componentes de cada componente."""
        for linha in estrutura.obter_componentes(self.dados, codigo):
            componente = linha["componente"]
            item = self.dados["itens"][componente]
            no = self.arvore_bom.insert(
                no_pai, "end", text=self.descricao(componente), open=True,
                values=(utils.formatar_quantidade(linha["quantidade"]),
                        item["unidade"], item["tipo"], nivel))
            if nivel not in niveis:
                niveis[nivel] = []
            niveis[nivel].append(componente)
            self.inserir_componentes(no, componente, nivel + 1, niveis)

    def filtrar_componentes(self):
        """Mostra só os componentes permitidos para o pai (RN03)."""
        pai = self.bom_pai.get()[:6]
        if not pai:
            return
        tipos = estrutura.COMPONENTES_PERMITIDOS[pai[:2]]
        self.bom_componente.configure(values=self.opcoes_itens(tipos))
        self.bom_componente.set("")

    def salvar_componente(self):
        """Adiciona um componente ou atualiza sua quantidade (RF03)."""
        pai = self.bom_pai.get()[:6]
        componente = self.bom_componente.get()[:6]
        if not pai or not componente:
            messagebox.showerror("Dados incompletos",
                                 "Escolha o item pai e o componente.")
            return
        try:
            quantidade = converter_numero(self.bom_quantidade.get(),
                                          "Quantidade", 0.001)
        except ValueError as erro:
            messagebox.showerror("Dados inválidos", str(erro))
            return
        lista = self.dados["estrutura"].setdefault(pai, [])
        for linha in lista:
            if linha["componente"] == componente:
                linha["quantidade"] = quantidade
                break
        else:
            lista.append({"componente": componente,
                          "quantidade": quantidade})
        self.atualizar(f"{componente} gravado na estrutura de {pai}.")

    def remover_componente(self):
        """Remove o componente escolhido da estrutura do pai."""
        pai = self.bom_pai.get()[:6]
        componente = self.bom_componente.get()[:6]
        lista = self.dados["estrutura"].get(pai, [])
        for linha in lista:
            if linha["componente"] == componente:
                if not messagebox.askyesno(
                        "Remover componente",
                        f"Remover {componente} da estrutura de {pai}?"):
                    return
                lista.remove(linha)
                if not lista:
                    del self.dados["estrutura"][pai]
                self.atualizar(f"{componente} removido da estrutura "
                               f"de {pai}.")
                return
        messagebox.showerror("Componente não encontrado",
                             f"{componente or 'O componente'} não faz "
                             f"parte da estrutura de {pai}.")

    # ----- Estoque ----------------------------------------------------

    def pagina_estoque(self):
        """Posição de estoque, formulário de movimentação e kardex."""
        direita = tk.Frame(self.conteudo, bg=FUNDO)
        direita.pack(side="right", fill="y", padx=(14, 0))
        esquerda = tk.Frame(self.conteudo, bg=FUNDO)
        esquerda.pack(side="left", fill="both", expand=True)

        caixa = self.cartao(esquerda, "Posição de estoque", fill="both",
                            expand=True)
        self.tabela_estoque = self.tabela(caixa, [
            ("codigo", "Código", 72, "w"),
            ("descricao", "Descrição", 170, "w"),
            ("saldo", "Saldo", 70, "e"),
            ("es", "Est. seg.", 75, "e"),
            ("un", "Un", 40, "center"),
            ("situacao", "Situação", 162, "w"),
        ], altura=9)
        contador = 0
        for codigo in self.codigos(utils.TIPOS_ITEM):
            item = self.dados["itens"][codigo]
            saldo = estoque.obter_saldo(self.dados, codigo)
            if saldo < item["estoque_seguranca"]:
                etiqueta = "alerta"
                situacao = "ABAIXO DO EST. SEG."
            else:
                etiqueta = "par" if contador % 2 else ""
                situacao = "OK"
            contador += 1
            self.tabela_estoque.insert(
                "", "end", iid=codigo, tags=(etiqueta,), values=(
                    codigo, item["descricao"],
                    utils.formatar_quantidade(saldo),
                    utils.formatar_quantidade(item["estoque_seguranca"]),
                    item["unidade"], situacao))
        self.tabela_estoque.bind("<<TreeviewSelect>>",
                                 lambda evento: self.mostrar_kardex())
        self.primeiro_estoque = None
        for codigo in self.codigos(utils.TIPOS_ITEM):
            item = self.dados["itens"][codigo]
            if estoque.obter_saldo(self.dados, codigo) < \
                    item["estoque_seguranca"]:
                self.primeiro_estoque = codigo
                break

        caixa_kardex = self.cartao(esquerda, None, fill="both",
                                   expand=True, pady=(14, 0))
        self.titulo_kardex = tk.Label(
            caixa_kardex, text="Kardex: selecione um item acima",
            bg=CARTAO, fg=TEXTO, font=self.fonte_cartao, anchor="w")
        self.titulo_kardex.pack(fill="x", pady=(12, 6))
        self.tabela_kardex = self.tabela(caixa_kardex, [
            ("data", "Data", 90, "center"),
            ("tipo", "Tipo", 80, "w"),
            ("qtde", "Qtde", 80, "e"),
            ("saldo", "Saldo", 80, "e"),
            ("descricao", "Documento", 260, "w"),
        ], altura=6)

        formulario = self.cartao(direita, "Registrar movimentação",
                                 fill="x")
        formulario.columnconfigure(1, weight=1)
        self.mov_item = self.lista(formulario, 0, "Item",
                                   self.opcoes_itens(utils.TIPOS_ITEM))
        tk.Label(formulario, text="Tipo", bg=CARTAO, fg=TEXTO_2,
                 font=self.fonte).grid(row=1, column=0, sticky="w", pady=4)
        self.mov_tipo = tk.StringVar(value="ENTRADA")
        tipos = tk.Frame(formulario, bg=CARTAO)
        tipos.grid(row=1, column=1, sticky="w")
        for valor, texto in [("ENTRADA", "Entrada"), ("SAIDA", "Saída"),
                             ("AJUSTE", "Ajuste")]:
            ttk.Radiobutton(tipos, text=texto, value=valor,
                            variable=self.mov_tipo).pack(side="left",
                                                         padx=(0, 8))
        self.mov_quantidade = self.campo(formulario, 2, "Quantidade")
        self.mov_documento = self.campo(formulario, 3, "Documento/motivo")
        self.mov_data = self.campo(formulario, 4, "Data (dd/mm/aaaa)")
        self.mov_data.insert(0, utils.formatar_data(utils.data_hoje()))
        self.botao(formulario, "Registrar", self.registrar_movimento).grid(
            row=5, column=0, columnspan=2, sticky="w", pady=(12, 0))
        tk.Label(direita, text="No ajuste, use número negativo para "
                 "diminuir\no saldo (ex.: -2 no inventário).\n\nRN02: o "
                 "saldo nunca pode ficar negativo.\nRN10: o kardex não "
                 "pode ser apagado.", bg=FUNDO, fg=TEXTO_2,
                 font=self.fonte_pequena, justify="left").pack(
            anchor="w", pady=10)
        if self.primeiro_estoque is not None:
            self.tabela_estoque.selection_set(self.primeiro_estoque)
            self.tabela_estoque.see(self.primeiro_estoque)
            self.mostrar_kardex()

    def mostrar_kardex(self):
        """Mostra o kardex do item selecionado na posição de estoque."""
        selecao = self.tabela_estoque.selection()
        if not selecao:
            return
        codigo = selecao[0]
        item = self.dados["itens"][codigo]
        self.titulo_kardex.configure(
            text=f"Kardex: {codigo} {item['descricao']} "
                 f"({item['unidade']})")
        self.mov_item.set(self.descricao(codigo))
        tabela = self.tabela_kardex
        tabela.delete(*tabela.get_children())
        for movimento in persistencia.ler_movimentos(codigo):
            quantidade = utils.formatar_quantidade(movimento["quantidade"])
            if movimento["quantidade"] > 0:
                quantidade = "+" + quantidade
            tabela.insert("", "end", values=(
                utils.formatar_data(movimento["data"]), movimento["tipo"],
                quantidade, utils.formatar_quantidade(movimento["saldo"]),
                movimento["documento"]))

    def registrar_movimento(self):
        """Valida o formulário e registra a movimentação (RF04)."""
        codigo = self.mov_item.get()[:6]
        tipo = self.mov_tipo.get()
        documento = self.mov_documento.get().strip()
        try:
            if not codigo:
                raise ValueError("Escolha o item.")
            if tipo == "AJUSTE":
                quantidade = converter_numero(self.mov_quantidade.get(),
                                              "Quantidade")
                if quantidade == 0:
                    raise ValueError("O ajuste não pode ser zero.")
            else:
                quantidade = converter_numero(self.mov_quantidade.get(),
                                              "Quantidade", 0.001)
            if not documento:
                raise ValueError("Informe o documento ou o motivo.")
            try:
                data = datetime.strptime(self.mov_data.get().strip(),
                                         "%d/%m/%Y").strftime("%Y-%m-%d")
            except ValueError:
                raise ValueError("Data inválida. Use dd/mm/aaaa.") from None
        except ValueError as erro:
            messagebox.showerror("Dados inválidos", str(erro))
            return
        deu_certo, mensagem = capturar_saida(
            estoque.movimentar, self.dados, codigo, tipo, quantidade,
            documento, data)
        if not deu_certo:
            messagebox.showerror("Movimentação recusada (RN02)", mensagem)
            return
        _, alerta = capturar_saida(estoque.exibir_alerta, self.dados, codigo)
        saldo = utils.formatar_quantidade(
            estoque.obter_saldo(self.dados, codigo))
        self.atualizar(f"Movimentação registrada em {codigo}. Saldo atual: "
                       f"{saldo}.")
        self.tabela_estoque.selection_set(codigo)
        self.tabela_estoque.see(codigo)
        self.mostrar_kardex()
        if alerta:
            messagebox.showwarning("Estoque de segurança", alerta)

    # ----- MPS --------------------------------------------------------

    def pagina_mps(self):
        """Grade editável com a demanda dos PA nas 8 semanas (RF07)."""
        caixa = self.cartao(self.conteudo, "Demanda por semana (unidades)",
                            fill="x")
        grade = tk.Frame(caixa, bg=CARTAO)
        grade.pack(anchor="w")
        tk.Label(grade, text="Produto", bg=CARTAO, fg=TEXTO,
                 font=self.fonte_negrito).grid(row=0, column=0, sticky="w",
                                               padx=(0, 16), pady=(0, 6))
        for semana in SEMANAS:
            tk.Label(grade, text=f"S{semana}", bg=CARTAO, fg=TEXTO,
                     font=self.fonte_negrito).grid(row=0, column=semana,
                                                   pady=(0, 6))
        tk.Label(grade, text="Total", bg=CARTAO, fg=TEXTO,
                 font=self.fonte_negrito).grid(row=0, column=9, padx=12)

        self.caixas_mps = {}
        linha = 1
        for codigo in self.codigos(["PA"]):
            demanda = mps.obter_demanda(self.dados, codigo)
            tk.Label(grade, text=self.descricao(codigo), bg=CARTAO,
                     fg=TEXTO, font=self.fonte).grid(
                row=linha, column=0, sticky="w", padx=(0, 16), pady=3)
            caixas = []
            for semana in SEMANAS:
                caixa_semana = ttk.Entry(grade, width=7, justify="center",
                                         font=self.fonte)
                caixa_semana.insert(0, str(demanda[semana - 1]))
                caixa_semana.grid(row=linha, column=semana, padx=3)
                caixas.append(caixa_semana)
            tk.Label(grade, text=str(sum(demanda)), bg=CARTAO, fg=AZUL,
                     font=self.fonte_negrito).grid(row=linha, column=9)
            self.caixas_mps[codigo] = caixas
            linha += 1
        if not self.caixas_mps:
            tk.Label(caixa, text="Cadastre produtos acabados (PA) primeiro.",
                     bg=CARTAO, fg=TEXTO_2).pack(anchor="w")
            return
        botoes = tk.Frame(caixa, bg=CARTAO)
        botoes.pack(fill="x", pady=(14, 0))
        self.botao(botoes, "Salvar MPS", self.salvar_mps).pack(side="left")
        self.botao(botoes, "Salvar e executar MRP",
                   self.salvar_mps_e_executar, "destaque").pack(
            side="left", padx=8)

        grafico = self.cartao(self.conteudo, None, fill="both",
                              expand=True, pady=(14, 0))
        tk.Frame(grafico, bg=CARTAO, height=8).pack()
        self.mostrar_grafico(grafico, self.figura_mps(), "grafico_mps.png")

    def ler_mps(self):
        """Lê a grade do MPS. Devolve False se algum valor for inválido."""
        novo = {}
        for codigo, caixas in self.caixas_mps.items():
            demanda = []
            for semana in SEMANAS:
                try:
                    demanda.append(converter_numero(
                        caixas[semana - 1].get(),
                        f"{codigo}, semana {semana}", 0, inteiro=True))
                except ValueError as erro:
                    messagebox.showerror("Dados inválidos", str(erro))
                    return False
            novo[codigo] = demanda
        for codigo, demanda in novo.items():
            if sum(demanda) > 0 or codigo in self.dados["mps"]:
                self.dados["mps"][codigo] = demanda
        return True

    def salvar_mps(self):
        """Grava o MPS editado na grade."""
        if self.ler_mps():
            self.atualizar("MPS salvo com sucesso.")

    def salvar_mps_e_executar(self):
        """Grava o MPS e já executa o MRP."""
        if self.ler_mps():
            persistencia.salvar_dados(self.dados)
            self.executar_mrp(mostrar_pagina=False)
            self.mostrar("mrp")

    # ----- MRP --------------------------------------------------------

    def pagina_mrp(self):
        """Execução do MRP, registro do item escolhido e exceções."""
        topo = self.cartao(self.conteudo, None, fill="x")
        linha = tk.Frame(topo, bg=CARTAO)
        linha.pack(fill="x", pady=(12, 0))
        self.botao(linha, "Executar MRP",
                   self.executar_mrp, "destaque").pack(side="left")
        tk.Label(linha, text=self.resumo_mrp or "Recalcula as necessidades "
                 "e recria as ordens PLANEJADAS (RN08).", bg=CARTAO,
                 fg=TEXTO_2, font=self.fonte).pack(side="left", padx=14)
        opcoes = self.opcoes_itens(utils.TIPOS_ITEM)
        self.mrp_item = ttk.Combobox(linha, values=opcoes, width=34,
                                     state="readonly", font=self.fonte)
        self.mrp_item.pack(side="right")
        tk.Label(linha, text="Item:", bg=CARTAO, fg=TEXTO_2,
                 font=self.fonte).pack(side="right", padx=(0, 8))
        if not opcoes:
            return
        if getattr(self, "item_mrp", None) not in self.dados["itens"]:
            self.item_mrp = self.codigos(utils.TIPOS_ITEM)[0]
        self.mrp_item.set(self.descricao(self.item_mrp))
        self.mrp_item.bind("<<ComboboxSelected>>",
                           lambda evento: self.trocar_item_mrp())
        codigo = self.item_mrp
        registro = mrp.calcular_mrp(self.dados)[codigo]
        item = self.dados["itens"][codigo]

        caixa = self.cartao(self.conteudo,
                            f"Registro MRP - {self.descricao(codigo)}",
                            fill="x", pady=(14, 0))
        saldo = estoque.obter_saldo(self.dados, codigo)
        info = (f"Lead time: {item['lead_time']} sem   |   Estoque de "
                f"segurança: "
                f"{utils.formatar_quantidade(item['estoque_seguranca'])}"
                f"   |   Lote mínimo: "
                f"{utils.formatar_quantidade(item['lote_minimo'])}   |   "
                f"Estoque atual: {utils.formatar_quantidade(saldo)}")
        tk.Label(caixa, text=info, bg=CARTAO, fg=TEXTO_2,
                 font=self.fonte_pequena).pack(anchor="w", pady=(0, 8))
        colunas = [("descricao", "Semana", 190, "w")]
        for semana in SEMANAS:
            colunas.append((f"s{semana}", str(semana), 95, "e"))
        tabela = self.tabela(caixa, colunas, altura=6)
        linhas = [
            ("Necessidade bruta", "necessidade_bruta", ""),
            ("Receb. programados", "recebimentos_programados", "par"),
            ("Estoque projetado", "estoque_projetado", ""),
            ("Necessidade líquida", "necessidade_liquida", "par"),
            ("Receb. planejados", "recebimentos_planejados", "aviso"),
            ("Liberação planejada", "liberacoes_planejadas", "firme"),
        ]
        for nome, chave, etiqueta in linhas:
            valores = [nome]
            for valor in registro[chave]:
                valores.append(utils.formatar_quantidade(valor))
            tabela.insert("", "end", values=valores, tags=(etiqueta,))

        corpo = tk.Frame(self.conteudo, bg=FUNDO)
        corpo.pack(fill="both", expand=True, pady=(14, 0))
        corpo.columnconfigure(0, weight=3, uniform="mrp")
        corpo.columnconfigure(1, weight=2, uniform="mrp")
        corpo.rowconfigure(0, weight=1)
        grafico = self.cartao(corpo, None,
                              grade={"row": 0, "column": 0, "sticky": "nsew",
                                     "padx": (0, 14)})
        self.mostrar_grafico(grafico,
                             self.figura_projetado(codigo, registro, 7, 2.3),
                             f"grafico_estoque_projetado_{codigo}.png")

        caixa_excecoes = self.cartao(corpo, "Mensagens de exceção (RN07)",
                                     grade={"row": 0, "column": 1,
                                            "sticky": "nsew"})
        texto = tk.Text(caixa_excecoes, bg=CARTAO, relief="flat", height=6,
                        wrap="word", font=self.fonte, cursor="arrow")
        texto.pack(fill="both", expand=True)
        texto.tag_configure("critico", foreground=VERMELHO)
        texto.tag_configure("normal", foreground=TEXTO_2)
        if not self.excecoes:
            atrasadas = []
            for numero, ordem in sorted(self.dados["ordens"].items()):
                if ordens.texto_status(ordem) == "ATRASADA":
                    atrasadas.append(f"{numero} {ordem['item']}: liberar "
                                     f"na semana "
                                     f"{ordem['semana_liberacao']}")
            self.excecoes = atrasadas
        if self.excecoes:
            for mensagem in self.excecoes:
                texto.insert("end", "• " + mensagem + "\n", "critico")
        else:
            texto.insert("end", "Nenhuma ordem atrasada.", "normal")
        texto.configure(state="disabled")

    def trocar_item_mrp(self):
        """Guarda o item escolhido e remonta a página do MRP."""
        self.item_mrp = self.mrp_item.get()[:6]
        self.mostrar("mrp")

    def executar_mrp(self, mostrar_pagina=True):
        """Executa o MRP e recria as ordens planejadas (RF08, RF09)."""
        if not self.dados["mps"]:
            messagebox.showerror("MPS vazio",
                                 "Cadastre o MPS antes de executar o MRP.")
            return
        registros = mrp.calcular_mrp(self.dados)
        novas = ordens.substituir_planejadas(self.dados, registros)
        self.excecoes = []
        for numero in novas:
            ordem = self.dados["ordens"][numero]
            if ordem["atrasada"]:
                self.excecoes.append(
                    f"{numero} {ordem['item']}: liberar na semana "
                    f"{ordem['semana_liberacao']}")
        hora = datetime.now().strftime("%H:%M")
        self.resumo_mrp = (f"Executado às {hora}: {len(novas)} ordem(ns) "
                           f"planejada(s), {len(self.excecoes)} "
                           f"atrasada(s).")
        self.status.set("MRP executado. " + self.resumo_mrp)
        if mostrar_pagina:
            self.mostrar("mrp")

    # ----- Ordens -----------------------------------------------------

    def pagina_ordens(self):
        """Lista de ordens com filtros, ações e componentes da OP."""
        topo = self.cartao(self.conteudo, None, fill="x")
        linha = tk.Frame(topo, bg=CARTAO)
        linha.pack(fill="x", pady=(12, 0))
        tk.Label(linha, text="Mostrar:", bg=CARTAO, fg=TEXTO_2,
                 font=self.fonte).pack(side="left")
        self.filtro_status = ttk.Combobox(
            linha, state="readonly", width=16, font=self.fonte,
            values=["Em aberto", "Todas", "PLANEJADA", "ATRASADA", "FIRME",
                    "LIBERADA", "ENCERRADA"])
        self.filtro_status.set(getattr(self, "filtro_escolhido",
                                       "Em aberto"))
        self.filtro_status.pack(side="left", padx=8)
        self.filtro_tipo = ttk.Combobox(linha, state="readonly", width=8,
                                        values=["OP e OC", "OP", "OC"],
                                        font=self.fonte)
        self.filtro_tipo.set(getattr(self, "tipo_escolhido", "OP e OC"))
        self.filtro_tipo.pack(side="left")
        for caixa in [self.filtro_status, self.filtro_tipo]:
            caixa.bind("<<ComboboxSelected>>",
                       lambda evento: self.preencher_ordens())
        self.botao(linha, "Apontar produção", self.apontar_producao,
                   "destaque").pack(side="right")
        self.botao(linha, "Encerrar OC", self.encerrar_compra,
                   "secundario").pack(side="right", padx=8)
        self.botao(linha, "Liberar",
                   lambda: self.mudar_status("FIRME", "LIBERADA")).pack(
            side="right")
        self.botao(linha, "Firmar",
                   lambda: self.mudar_status("PLANEJADA", "FIRME")).pack(
            side="right", padx=8)

        corpo = tk.Frame(self.conteudo, bg=FUNDO)
        corpo.pack(fill="both", expand=True, pady=(14, 0))
        direita = tk.Frame(corpo, bg=FUNDO)
        direita.pack(side="right", fill="y", padx=(14, 0))
        esquerda = tk.Frame(corpo, bg=FUNDO)
        esquerda.pack(side="left", fill="both", expand=True)

        caixa = self.cartao(esquerda, "Ordens de produção e de compra",
                            fill="both", expand=True)
        self.tabela_ordens = self.tabela(caixa, [
            ("ordem", "Ordem", 80, "w"),
            ("tipo", "Tipo", 45, "center"),
            ("item", "Item", 70, "w"),
            ("descricao", "Descrição", 150, "w"),
            ("qtde", "Qtde", 65, "e"),
            ("liberar", "Liberar", 65, "center"),
            ("entregar", "Entregar", 75, "center"),
            ("status", "Status", 100, "center"),
        ], altura=17)
        self.tabela_ordens.configure(selectmode="extended")
        self.tabela_ordens.bind("<<TreeviewSelect>>",
                                lambda evento: self.detalhar_ordem())
        self.contagem_ordens = tk.Label(caixa, bg=CARTAO, fg=TEXTO_2,
                                        font=self.fonte_pequena,
                                        anchor="w")
        self.contagem_ordens.pack(fill="x", pady=(6, 0))

        detalhe = self.cartao(direita, "Detalhe da ordem", fill="both",
                              expand=True)
        self.texto_ordem = tk.Label(detalhe, text="Selecione uma ordem.",
                                    bg=CARTAO, fg=TEXTO_2, font=self.fonte,
                                    justify="left", anchor="w")
        self.texto_ordem.pack(fill="x", pady=(0, 10))
        self.tabela_necessidade = self.tabela(detalhe, [
            ("componente", "Item", 75, "w"),
            ("necessario", "Necessário", 90, "e"),
            ("saldo", "Saldo", 75, "e"),
            ("situacao", "", 60, "center"),
        ], altura=7)
        tk.Label(direita, text="Ciclo: PLANEJADA → FIRME → LIBERADA → "
                 "ENCERRADA.\nSelecione várias linhas (Ctrl ou Shift) para "
                 "firmar ou liberar mais de uma ordem.\nEncerrar uma OC "
                 "dá entrada do material no estoque.", bg=FUNDO,
                 fg=TEXTO_2, font=self.fonte_pequena, wraplength=300,
                 justify="left").pack(anchor="w", pady=10)
        self.preencher_ordens()

    def preencher_ordens(self):
        """Preenche a tabela de ordens conforme os filtros."""
        self.filtro_escolhido = self.filtro_status.get()
        self.tipo_escolhido = self.filtro_tipo.get()
        tabela = self.tabela_ordens
        tabela.delete(*tabela.get_children())
        etiquetas = {"ATRASADA": "alerta", "FIRME": "firme",
                     "LIBERADA": "aviso", "ENCERRADA": "ok"}
        total = 0
        for tipo in ["OP", "OC"]:
            if self.tipo_escolhido not in ("OP e OC", tipo):
                continue
            for numero in sorted(self.dados["ordens"]):
                ordem = self.dados["ordens"][numero]
                if ordem["tipo"] != tipo:
                    continue
                status = ordens.texto_status(ordem)
                filtro = self.filtro_escolhido
                if filtro == "Em aberto" and status == "ENCERRADA":
                    continue
                if filtro not in ("Em aberto", "Todas", status):
                    continue
                total += 1
                tabela.insert("", "end", iid=numero,
                              tags=(etiquetas.get(status, ""),), values=(
                                  numero, tipo, ordem["item"],
                                  self.dados["itens"][ordem["item"]]
                                  ["descricao"],
                                  utils.formatar_quantidade(
                                      ordem["quantidade"]),
                                  f"S{ordem['semana_liberacao']}",
                                  f"S{ordem['semana_entrega']}", status))
        self.contagem_ordens.configure(text=f"{total} ordem(ns) exibida(s).")

    def ordens_selecionadas(self):
        """Devolve os números das ordens selecionadas na tabela."""
        return list(self.tabela_ordens.selection())

    def necessidades_op(self, numero):
        """Lista (componente, necessário, saldo) de uma OP."""
        ordem = self.dados["ordens"][numero]
        resultado = []
        for linha in estrutura.obter_componentes(self.dados, ordem["item"]):
            necessario = round(linha["quantidade"] * ordem["quantidade"], 3)
            saldo = estoque.obter_saldo(self.dados, linha["componente"])
            resultado.append((linha["componente"], necessario, saldo))
        return resultado

    def detalhar_ordem(self):
        """Mostra os dados da ordem e, se for OP, os componentes."""
        selecao = self.ordens_selecionadas()
        tabela = self.tabela_necessidade
        tabela.delete(*tabela.get_children())
        if len(selecao) != 1:
            self.texto_ordem.configure(
                text=f"{len(selecao)} ordens selecionadas.")
            return
        numero = selecao[0]
        ordem = self.dados["ordens"][numero]
        item = self.dados["itens"][ordem["item"]]
        self.texto_ordem.configure(text=(
            f"{numero}  ·  {ordens.texto_status(ordem)}\n"
            f"{ordem['item']} {item['descricao']}\n"
            f"Quantidade: {utils.formatar_quantidade(ordem['quantidade'])} "
            f"{item['unidade']}\n"
            f"Liberar na semana {ordem['semana_liberacao']}, entregar na "
            f"semana {ordem['semana_entrega']}"))
        if ordem["tipo"] != "OP":
            tabela.insert("", "end", values=("Ordem de compra:", "", "",
                                             ""))
            return
        for componente, necessario, saldo in self.necessidades_op(numero):
            if saldo >= necessario:
                situacao = "OK"
                etiqueta = "ok"
            else:
                situacao = "FALTA"
                etiqueta = "alerta"
            tabela.insert("", "end", tags=(etiqueta,), values=(
                componente, utils.formatar_quantidade(necessario),
                utils.formatar_quantidade(saldo), situacao))

    def mudar_status(self, de, para):
        """Firma ou libera as ordens selecionadas (RF10)."""
        selecao = self.ordens_selecionadas()
        if not selecao:
            messagebox.showinfo("Ordens", "Selecione uma ou mais ordens.")
            return
        alteradas = []
        ignoradas = []
        for numero in selecao:
            ordem = self.dados["ordens"][numero]
            if ordem["status"] == de:
                ordem["status"] = para
                alteradas.append(numero)
            else:
                ignoradas.append(f"{numero} ({ordens.texto_status(ordem)})")
        if ignoradas:
            messagebox.showwarning(
                "Algumas ordens não foram alteradas",
                f"Só ordens {de} podem passar para {para}:\n"
                + "\n".join(ignoradas))
        if alteradas:
            self.atualizar(f"{len(alteradas)} ordem(ns): {de} -> {para}.")

    def encerrar_compra(self):
        """Encerra a OC selecionada e dá entrada no estoque (RF10)."""
        selecao = self.ordens_selecionadas()
        if len(selecao) != 1:
            messagebox.showinfo("Encerrar OC", "Selecione uma única OC.")
            return
        numero = selecao[0]
        ordem = self.dados["ordens"][numero]
        if ordem["tipo"] != "OC" or ordem["status"] != "LIBERADA":
            messagebox.showerror("Encerrar OC", "Só uma OC LIBERADA pode "
                                 "ser encerrada.\nOPs são encerradas pelo "
                                 "apontamento de produção.")
            return
        estoque.movimentar(self.dados, ordem["item"], "ENTRADA",
                           ordem["quantidade"], f"{numero} (recebimento)",
                           utils.data_hoje())
        ordem["status"] = "ENCERRADA"
        self.atualizar(f"{numero} encerrada: "
                       f"{utils.formatar_quantidade(ordem['quantidade'])} "
                       f"de {ordem['item']} recebidos no estoque.")

    def apontar_producao(self):
        """Aponta a produção da OP selecionada (RF11)."""
        selecao = self.ordens_selecionadas()
        if len(selecao) != 1:
            messagebox.showinfo("Apontar produção", "Selecione uma única OP.")
            return
        numero = selecao[0]
        ordem = self.dados["ordens"][numero]
        if ordem["tipo"] != "OP" or ordem["status"] != "LIBERADA":
            messagebox.showerror("Apontar produção", "Só uma OP LIBERADA "
                                 "pode ser apontada.")
            return
        necessidades = self.necessidades_op(numero)
        faltas = []
        for componente, necessario, saldo in necessidades:
            if saldo < necessario:
                faltas.append(f"{componente}: necessário "
                              f"{utils.formatar_quantidade(necessario)}, "
                              f"saldo {utils.formatar_quantidade(saldo)}")
        if faltas:
            messagebox.showerror("Apontamento rejeitado",
                                 "Falta de componentes:\n\n"
                                 + "\n".join(faltas))
            return
        resumo = []
        for componente, necessario, saldo in necessidades:
            resumo.append(f"- {componente}: "
                          f"{utils.formatar_quantidade(necessario)}")
        if not messagebox.askyesno(
                "Apontar produção",
                f"Apontar {utils.formatar_quantidade(ordem['quantidade'])} "
                f"de {ordem['item']} na {numero}?\n\nSerão baixados:\n"
                + "\n".join(resumo)):
            return
        documento = f"{numero} ({ordem['item']})"
        hoje = utils.data_hoje()
        for componente, necessario, saldo in necessidades:
            estoque.movimentar(self.dados, componente, "SAIDA", necessario,
                               documento, hoje)
        estoque.movimentar(self.dados, ordem["item"], "ENTRADA",
                           ordem["quantidade"], documento, hoje)
        ordem["status"] = "ENCERRADA"
        saldo = utils.formatar_quantidade(
            estoque.obter_saldo(self.dados, ordem["item"]))
        self.atualizar(f"Produção apontada: {numero} encerrada. Saldo de "
                       f"{ordem['item']}: {saldo}.")

    # ----- Capacidade -------------------------------------------------

    def pagina_capacidade(self):
        """Abas: carga x capacidade, centros e roteiros."""
        abas = ttk.Notebook(self.conteudo)
        abas.pack(fill="both", expand=True)
        aba_carga = tk.Frame(abas, bg=FUNDO)
        aba_centros = tk.Frame(abas, bg=FUNDO)
        aba_roteiros = tk.Frame(abas, bg=FUNDO)
        abas.add(aba_carga, text="Carga x capacidade")
        abas.add(aba_centros, text="Centros de trabalho")
        abas.add(aba_roteiros, text="Roteiros")
        abas.select(getattr(self, "aba_capacidade", 0))
        abas.bind("<<NotebookTabChanged>>", lambda evento: setattr(
            self, "aba_capacidade", abas.index(abas.select())))
        self.montar_aba_carga(aba_carga)
        self.montar_aba_centros(aba_centros)
        self.montar_aba_roteiros(aba_roteiros)

    def montar_aba_carga(self, aba):
        """Gráfico e tabela da carga de um centro (RF12, RN09)."""
        if not self.dados["centros"]:
            tk.Label(aba, text="Nenhum centro cadastrado.", bg=FUNDO,
                     fg=TEXTO_2).pack(pady=20)
            return
        centros = sorted(self.dados["centros"])
        if getattr(self, "centro_escolhido", None) not in centros:
            self.centro_escolhido = centros[-1]
        topo = tk.Frame(aba, bg=FUNDO)
        topo.pack(fill="x", pady=12)
        for centro in centros:
            if centro == self.centro_escolhido:
                tipo = "primario"
            else:
                tipo = "secundario"
            self.botao(topo, f"{centro}  "
                       f"{self.dados['centros'][centro]['descricao']}",
                       lambda codigo=centro: self.escolher_centro(codigo),
                       tipo).pack(side="left", padx=(0, 8))

        corpo = tk.Frame(aba, bg=FUNDO)
        corpo.pack(fill="both", expand=True)
        centro = self.centro_escolhido
        caixa = self.cartao(corpo, "Semana a semana", side="right",
                            fill="y", padx=(14, 0))
        grafico = self.cartao(corpo, None, side="left", fill="both",
                              expand=True)
        tk.Frame(grafico, bg=CARTAO, height=8).pack()
        self.mostrar_grafico(grafico, self.figura_carga(centro, 7, 3.3),
                             f"grafico_carga_{centro}.png")

        tabela = self.tabela(caixa, [
            ("semana", "Sem", 50, "center"),
            ("carga", "Carga (h)", 85, "e"),
            ("uso", "Uso", 60, "e"),
            ("situacao", "Situação", 110, "center"),
        ], altura=8)
        limite = self.dados["centros"][centro]["capacidade_horas"]
        carga = capacidade.calcular_carga(self.dados, centro)
        sobrecarga = []
        for semana in SEMANAS:
            horas = carga[semana - 1]
            uso = horas / limite * 100
            if horas > limite:
                situacao = "SOBRECARGA"
                etiqueta = "alerta"
                sobrecarga.append(str(semana))
            else:
                situacao = "OK"
                etiqueta = ""
            tabela.insert("", "end", tags=(etiqueta,), values=(
                semana, capacidade.formatar_horas(horas), f"{round(uso)}%",
                situacao))
        if sobrecarga:
            dica = ("Sugestão: antecipar OPs ou programar hora extra nas "
                    "semanas " + ", ".join(sobrecarga) + ".")
        else:
            dica = "Nenhuma semana com sobrecarga."
        tk.Label(caixa, text=dica, bg=CARTAO, fg=TEXTO_2,
                 font=self.fonte_pequena, wraplength=280,
                 justify="left").pack(anchor="w", pady=(8, 0))

    def escolher_centro(self, centro):
        """Troca o centro exibido na aba de carga."""
        self.centro_escolhido = centro
        self.mostrar("capacidade")

    def montar_aba_centros(self, aba):
        """Tabela e formulário de centros de trabalho (RF06)."""
        formulario = self.cartao(aba, "Novo centro / alterar",
                                 side="right", fill="y", padx=(14, 0),
                                 pady=12)
        esquerda = self.cartao(aba, "Centros cadastrados", side="left",
                               fill="both", expand=True, pady=12)
        self.tabela_centros = self.tabela(esquerda, [
            ("codigo", "Código", 80, "w"),
            ("descricao", "Descrição", 220, "w"),
            ("capacidade", "Capacidade (h/sem)", 140, "e"),
            ("custo", "Custo-hora", 110, "e"),
        ], altura=8)
        for codigo in sorted(self.dados["centros"]):
            centro = self.dados["centros"][codigo]
            self.tabela_centros.insert("", "end", iid=codigo, values=(
                codigo, centro["descricao"],
                utils.formatar_quantidade(centro["capacidade_horas"]),
                utils.formatar_moeda(centro["custo_hora"])))
        self.tabela_centros.bind("<<TreeviewSelect>>",
                                 lambda evento: self.carregar_centro())

        formulario.columnconfigure(1, weight=1)
        self.centro_codigo = self.campo(formulario, 0, "Código (CT-00)")
        self.centro_descricao = self.campo(formulario, 1, "Descrição")
        self.centro_capacidade = self.campo(formulario, 2,
                                            "Capacidade (h/semana)")
        self.centro_custo = self.campo(formulario, 3, "Custo-hora (R$)")
        botoes = tk.Frame(formulario, bg=CARTAO)
        botoes.grid(row=4, column=0, columnspan=2, sticky="w", pady=(12, 0))
        self.botao(botoes, "Salvar", self.salvar_centro).pack(side="left")
        self.botao(botoes, "Novo", self.limpar_centro,
                   "secundario").pack(side="left", padx=8)
        self.limpar_centro()

    def limpar_centro(self):
        """Deixa o formulário de centro pronto para um centro novo."""
        self.centro_editando = None
        self.centro_codigo.configure(state="normal")
        for caixa in [self.centro_codigo, self.centro_descricao,
                      self.centro_capacidade, self.centro_custo]:
            caixa.delete(0, "end")

    def carregar_centro(self):
        """Coloca no formulário os dados do centro selecionado."""
        selecao = self.tabela_centros.selection()
        if not selecao:
            return
        codigo = selecao[0]
        centro = self.dados["centros"][codigo]
        self.limpar_centro()
        self.centro_editando = codigo
        self.centro_codigo.insert(0, codigo)
        self.centro_codigo.configure(state="disabled")
        self.centro_descricao.insert(0, centro["descricao"])
        self.centro_capacidade.insert(
            0, utils.formatar_quantidade(centro["capacidade_horas"]))
        self.centro_custo.insert(
            0, utils.formatar_quantidade(centro["custo_hora"]))

    def salvar_centro(self):
        """Cadastra ou altera um centro de trabalho (RF06)."""
        try:
            if self.centro_editando is None:
                codigo = self.centro_codigo.get().strip().upper()
                if not capacidade.validar_codigo_centro(codigo):
                    raise ValueError("Código inválido. Use CT-00, "
                                     "ex.: CT-04.")
                if codigo in self.dados["centros"]:
                    raise ValueError(f"O centro {codigo} já existe.")
            else:
                codigo = self.centro_editando
            descricao = self.centro_descricao.get().strip()
            if not descricao:
                raise ValueError("Preencha a descrição.")
            novo = {
                "descricao": descricao,
                "capacidade_horas": converter_numero(
                    self.centro_capacidade.get(), "Capacidade", 0.1),
                "custo_hora": converter_numero(self.centro_custo.get(),
                                               "Custo-hora", 0),
            }
        except ValueError as erro:
            messagebox.showerror("Dados inválidos", str(erro))
            return
        self.dados["centros"][codigo] = novo
        self.aba_capacidade = 1
        self.atualizar(f"Centro {codigo} salvo.")

    def montar_aba_roteiros(self, aba):
        """Tabela e formulário de roteiros dos itens fabricados (RF06)."""
        formulario = self.cartao(aba, "Definir roteiro", side="right",
                                 fill="y", padx=(14, 0), pady=12)
        esquerda = self.cartao(aba, "Roteiros (operação única)",
                               side="left", fill="both", expand=True,
                               pady=12)
        tabela = self.tabela(esquerda, [
            ("item", "Item", 80, "w"),
            ("descricao", "Descrição", 220, "w"),
            ("centro", "Centro", 80, "center"),
            ("tempo", "Tempo (h/un)", 110, "e"),
        ], altura=8)
        for codigo in self.codigos(["PA", "SA"]):
            roteiro = capacidade.obter_roteiro(self.dados, codigo)
            if roteiro is None:
                tabela.insert("", "end", tags=("alerta",), values=(
                    codigo, self.dados["itens"][codigo]["descricao"], "-",
                    "SEM ROTEIRO"))
            else:
                tabela.insert("", "end", values=(
                    codigo, self.dados["itens"][codigo]["descricao"],
                    roteiro["centro"],
                    utils.formatar_quantidade(roteiro["tempo_unitario"])))

        formulario.columnconfigure(1, weight=1)
        self.roteiro_item = self.lista(formulario, 0, "Item fabricado",
                                       self.opcoes_itens(["PA", "SA"]))
        self.roteiro_centro = self.lista(formulario, 1, "Centro",
                                         sorted(self.dados["centros"]))
        self.roteiro_tempo = self.campo(formulario, 2, "Tempo (h/un)")
        self.botao(formulario, "Salvar roteiro", self.salvar_roteiro).grid(
            row=3, column=0, columnspan=2, sticky="w", pady=(12, 0))

    def salvar_roteiro(self):
        """Define o centro e o tempo por unidade de um item (RF06)."""
        codigo = self.roteiro_item.get()[:6]
        centro = self.roteiro_centro.get()
        if not codigo or not centro:
            messagebox.showerror("Dados incompletos",
                                 "Escolha o item e o centro.")
            return
        try:
            tempo = converter_numero(self.roteiro_tempo.get(), "Tempo",
                                     0.001)
        except ValueError as erro:
            messagebox.showerror("Dados inválidos", str(erro))
            return
        self.dados["roteiros"][codigo] = {"centro": centro,
                                          "tempo_unitario": tempo}
        self.aba_capacidade = 2
        self.atualizar(f"Roteiro de {codigo} definido: {centro}.")

    # ----- Custos -----------------------------------------------------

    def pagina_custos(self):
        """Resumo do custo padrão e composição do item escolhido."""
        fabricados = self.codigos(["PA", "SA"])
        if not fabricados:
            tk.Label(self.conteudo, text="Nenhum item fabricado.",
                     bg=FUNDO, fg=TEXTO_2).pack()
            return
        if getattr(self, "item_custo", None) not in fabricados:
            self.item_custo = fabricados[0]

        esquerda = self.cartao(self.conteudo, "Itens fabricados",
                               side="left", fill="y")
        tabela = self.tabela(esquerda, [
            ("item", "Item", 70, "w"),
            ("descricao", "Descrição", 175, "w"),
            ("custo", "Custo padrão", 125, "e"),
        ], altura=12)
        for codigo in fabricados:
            tabela.insert("", "end", iid=codigo, values=(
                codigo, self.dados["itens"][codigo]["descricao"],
                utils.formatar_moeda(custos.custo_padrao(self.dados,
                                                         codigo))))
        tabela.selection_set(self.item_custo)
        tabela.bind("<<TreeviewSelect>>",
                    lambda evento: self.escolher_custo(tabela))

        codigo = self.item_custo
        direita = self.cartao(self.conteudo,
                              f"Composição - {self.descricao(codigo)}",
                              side="left", fill="both", expand=True,
                              padx=(14, 0))
        detalhe = self.tabela(direita, [
            ("item", "Item", 70, "w"),
            ("descricao", "Descrição", 170, "w"),
            ("qtde", "Qtde", 60, "e"),
            ("unitario", "Custo un.", 100, "e"),
            ("total", "Total", 105, "e"),
        ], altura=8)
        materiais = 0
        for linha in estrutura.obter_componentes(self.dados, codigo):
            componente = linha["componente"]
            unitario = custos.custo_padrao(self.dados, componente)
            total = linha["quantidade"] * unitario
            materiais += total
            detalhe.insert("", "end", values=(
                componente, self.dados["itens"][componente]["descricao"],
                utils.formatar_quantidade(linha["quantidade"]),
                utils.formatar_moeda(unitario), utils.formatar_moeda(total)))
        roteiro = capacidade.obter_roteiro(self.dados, codigo)
        mao_de_obra = custos.custo_mao_de_obra(self.dados, codigo)
        if roteiro is None:
            detalhe.insert("", "end", tags=("aviso",), values=(
                "", "Mão de obra (sem roteiro)", "", "", "R$ 0,00"))
        else:
            custo_hora = self.dados["centros"][roteiro["centro"]][
                "custo_hora"]
            detalhe.insert("", "end", tags=("firme",), values=(
                "", f"Mão de obra {roteiro['centro']}",
                utils.formatar_quantidade(roteiro["tempo_unitario"]) + " h",
                utils.formatar_moeda(custo_hora),
                utils.formatar_moeda(mao_de_obra)))

        totais = tk.Frame(direita, bg=CARTAO)
        totais.pack(fill="x", pady=(14, 0))
        for rotulo, valor, cor in [
                ("Materiais", materiais, AZUL),
                ("Mão de obra", mao_de_obra, LARANJA),
                ("Custo padrão", custos.custo_padrao(self.dados, codigo),
                 TEXTO)]:
            bloco = tk.Frame(totais, bg=CARTAO)
            bloco.pack(side="left", padx=(0, 36))
            tk.Label(bloco, text=rotulo, bg=CARTAO, fg=TEXTO_2,
                     font=self.fonte).pack(anchor="w")
            tk.Label(bloco, text=utils.formatar_moeda(valor), bg=CARTAO,
                     fg=cor, font=(self.familia, 18, "bold")).pack(
                anchor="w")
        tk.Label(direita, text="O custo de cada semiacabado já inclui os "
                 "materiais e a mão de obra dele (cálculo recursivo pela "
                 "estrutura).", bg=CARTAO, fg=TEXTO_2, wraplength=520,
                 font=self.fonte_pequena, justify="left").pack(
            anchor="w", pady=(12, 0))

    def escolher_custo(self, tabela):
        """Mostra a composição do item selecionado na tabela de custos."""
        selecao = tabela.selection()
        if selecao and selecao[0] != self.item_custo:
            self.item_custo = selecao[0]
            self.mostrar("custos")

    # ----- Relatórios -------------------------------------------------

    def pagina_relatorios(self):
        """Exportação CSV, gráficos em PNG e posição de estoque."""
        linha = tk.Frame(self.conteudo, bg=FUNDO)
        linha.pack(fill="x")
        acoes = [
            ("Posição de estoque", "Saldo, estoque de segurança e situação "
             "de todos os itens (posicao_estoque.csv).", "Exportar CSV",
             lambda: self.exportar(relatorios.exportar_estoque)),
            ("Lista de ordens", "OPs e OCs com semanas e status "
             "(ordens.csv).", "Exportar CSV",
             lambda: self.exportar(relatorios.exportar_ordens)),
            ("Todos os gráficos", "Posição de estoque, ordens, carga de "
             "cada centro e estoque projetado dos PA em PNG.",
             "Gerar PNGs", self.salvar_todos_graficos),
        ]
        for coluna in range(len(acoes)):
            titulo, texto, rotulo, comando = acoes[coluna]
            linha.columnconfigure(coluna, weight=1)
            moldura = tk.Frame(linha, bg=CARTAO, highlightthickness=1,
                               highlightbackground=BORDA,
                               highlightcolor=BORDA)
            moldura.grid(row=0, column=coluna, sticky="nsew",
                         padx=(0 if coluna == 0 else 14, 0))
            tk.Label(moldura, text=titulo, bg=CARTAO, fg=TEXTO,
                     font=self.fonte_cartao).pack(anchor="w", padx=16,
                                                  pady=(14, 4))
            tk.Label(moldura, text=texto, bg=CARTAO, fg=TEXTO_2,
                     font=self.fonte, wraplength=300,
                     justify="left").pack(anchor="w", padx=16)
            self.botao(moldura, rotulo, comando).pack(anchor="w", padx=16,
                                                      pady=14)
        rodape = tk.Frame(self.conteudo, bg=FUNDO)
        rodape.pack(fill="x", pady=10)
        self.botao(rodape, "Abrir a pasta exports", self.abrir_exportacao,
                   "secundario").pack(side="left")
        tk.Label(rodape, text=f"Os arquivos são gravados em "
                 f"{persistencia.PASTA_EXPORTACAO}", bg=FUNDO, fg=TEXTO_2,
                 font=self.fonte_pequena).pack(side="left", padx=12)

        corpo = tk.Frame(self.conteudo, bg=FUNDO)
        corpo.pack(fill="both", expand=True)
        corpo.columnconfigure(0, weight=3)
        corpo.columnconfigure(1, weight=2)
        corpo.rowconfigure(0, weight=1)
        esquerda = self.cartao(corpo, None,
                               grade={"row": 0, "column": 0, "sticky": "nsew",
                                      "padx": (0, 14)})
        tk.Frame(esquerda, bg=CARTAO, height=8).pack()
        self.mostrar_grafico(esquerda, self.figura_posicao(7, 3.3),
                             "grafico_posicao_estoque.png")
        direita = self.cartao(corpo, None,
                              grade={"row": 0, "column": 1, "sticky": "nsew"})
        tk.Frame(direita, bg=CARTAO, height=8).pack()
        self.mostrar_grafico(direita, self.figura_ordens(5, 3.3),
                             "grafico_ordens_por_semana.png")

    def exportar(self, funcao):
        """Chama uma exportação do relatorios.py e mostra o resultado."""
        _, mensagem = capturar_saida(funcao, self.dados)
        ultima = mensagem.splitlines()[-1] if mensagem else ""
        messagebox.showinfo("Exportação", ultima)
        self.status.set(ultima)

    def salvar_todos_graficos(self):
        """Gera todos os gráficos de gestão em PNG (RF16)."""
        arquivos = []
        figuras = [(self.figura_posicao(), "grafico_posicao_estoque.png"),
                   (self.figura_ordens(), "grafico_ordens_por_semana.png")]
        for centro in sorted(self.dados["centros"]):
            figuras.append((self.figura_carga(centro),
                            f"grafico_carga_{centro}.png"))
        registros = mrp.calcular_mrp(self.dados)
        for codigo in self.codigos(["PA"]):
            figuras.append((self.figura_projetado(codigo,
                                                  registros[codigo]),
                            f"grafico_estoque_projetado_{codigo}.png"))
        for figura, nome in figuras:
            figura.tight_layout()
            self.salvar_png(figura, nome)
            arquivos.append(nome)
        messagebox.showinfo("Gráficos", f"{len(arquivos)} gráficos salvos "
                            f"em exports/:\n\n" + "\n".join(arquivos))

    def abrir_exportacao(self):
        """Abre a pasta exports/ no gerenciador de arquivos."""
        persistencia.caminho_exportacao("")
        pasta = persistencia.PASTA_EXPORTACAO
        try:
            if sys.platform.startswith("win"):
                os.startfile(pasta)
            elif sys.platform == "darwin":
                subprocess.run(["open", str(pasta)], check=False)
            else:
                subprocess.run(["xdg-open", str(pasta)], check=False)
        except OSError:
            messagebox.showinfo("Pasta de exportação", str(pasta))


def main():
    """Abre a janela da interface gráfica."""
    janela = tk.Tk()
    AplicativoMRP(janela)
    janela.mainloop()


if __name__ == "__main__":
    main()
