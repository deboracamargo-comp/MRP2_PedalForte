"""Funções auxiliares de validação de entradas e de formatação.

As funções 'ler_...' repetem a pergunta até o usuário digitar um valor
válido (RNF05). As funções 'formatar_...' preparam valores para exibir
na tela no padrão brasileiro.
"""

from datetime import date, datetime

TIPOS_ITEM = ("PA", "SA", "MP")
LARGURA_TELA = 50


# ---------------------------------------------------------------------
# Leitura e validação de entradas
# ---------------------------------------------------------------------

def ler_texto(mensagem):
    """Lê um texto não vazio."""
    while True:
        texto = input(mensagem).strip()
        if texto != "":
            return texto
        print("ERRO: o campo não pode ficar vazio.")


def ler_inteiro(mensagem, minimo=None, maximo=None):
    """Lê um número inteiro, opcionalmente dentro de um intervalo."""
    while True:
        try:
            valor = int(input(mensagem))
        except ValueError:
            print("ERRO: digite um número inteiro.")
            continue
        if minimo is not None and valor < minimo:
            print(f"ERRO: o valor deve ser no mínimo {minimo}.")
        elif maximo is not None and valor > maximo:
            print(f"ERRO: o valor deve ser no máximo {maximo}.")
        else:
            return valor


def ler_decimal(mensagem, minimo=None):
    """Lê um número decimal. Aceita vírgula ou ponto (ex.: 0,5 ou 0.5)."""
    while True:
        texto = input(mensagem).strip().replace(",", ".")
        try:
            valor = float(texto)
        except ValueError:
            print("ERRO: digite um número (ex.: 12 ou 0,5).")
            continue
        if minimo is not None and valor < minimo:
            print(f"ERRO: o valor deve ser no mínimo "
                  f"{formatar_quantidade(minimo)}.")
        else:
            return valor


def ler_opcao(mensagem, opcoes):
    """Lê uma opção que precisa estar na lista 'opcoes'.

    A comparação ignora maiúsculas e minúsculas, e a opção é devolvida
    em maiúsculas. Exemplo: ler_opcao("Tipo [E/S/A]: ", ["E", "S", "A"])
    """
    while True:
        opcao = input(mensagem).strip().upper()
        if opcao in opcoes:
            return opcao
        print(f"ERRO: opção inválida. Opções: {', '.join(opcoes)}.")


def confirmar(mensagem):
    """Faz uma pergunta de sim ou não e devolve True ou False."""
    resposta = ler_opcao(mensagem + " [S/N]: ", ["S", "N"])
    return resposta == "S"


def validar_codigo(codigo):
    """Verifica se o código segue o formato Tipo-Número (RN01).

    Formato aceito: PA-001, SA-020, MP-201 (tipo + hífen + 3 dígitos).
    """
    return (len(codigo) == 6
            and codigo[:2] in TIPOS_ITEM
            and codigo[2] == "-"
            and codigo[3:].isdigit())


def ler_codigo(mensagem):
    """Lê um código de item no formato da RN01 e o devolve em maiúsculas.

    Só verifica o formato. Se o item existe ou não, quem verifica é o
    módulo que chamou esta função.
    """
    while True:
        codigo = input(mensagem).strip().upper()
        if validar_codigo(codigo):
            return codigo
        print("ERRO: código inválido. Use o formato Tipo-Número, "
              "ex.: PA-001, SA-020, MP-201.")


def ler_data(mensagem):
    """Lê uma data no formato dd/mm/aaaa e a devolve como aaaa-mm-dd.

    Se o usuário apenas apertar Enter, usa a data de hoje.
    """
    while True:
        texto = input(mensagem + " (dd/mm/aaaa, Enter = hoje): ").strip()
        if texto == "":
            return data_hoje()
        try:
            data = datetime.strptime(texto, "%d/%m/%Y")
            return data.strftime("%Y-%m-%d")
        except ValueError:
            print("ERRO: data inválida. Use o formato dd/mm/aaaa.")


# ---------------------------------------------------------------------
# Datas e formatação
# ---------------------------------------------------------------------

def data_hoje():
    """Devolve a data de hoje no formato aaaa-mm-dd."""
    return date.today().strftime("%Y-%m-%d")


def formatar_data(data_iso):
    """Converte uma data de aaaa-mm-dd para dd/mm/aaaa."""
    ano, mes, dia = data_iso.split("-")
    return f"{dia}/{mes}/{ano}"


def formatar_quantidade(valor):
    """Formata uma quantidade: 18.0 vira '18' e 0.5 vira '0,5'."""
    valor = round(valor, 3)
    if valor == int(valor):
        return str(int(valor))
    return str(valor).replace(".", ",")


def formatar_moeda(valor):
    """Formata um valor em reais: 1234.5 vira 'R$ 1.234,50'."""
    texto = f"{valor:,.2f}"
    texto = texto.replace(",", "#").replace(".", ",").replace("#", ".")
    return "R$ " + texto


# ---------------------------------------------------------------------
# Tela
# ---------------------------------------------------------------------

def exibir_titulo(titulo):
    """Exibe um título centralizado entre linhas de '='."""
    print("=" * LARGURA_TELA)
    print(titulo.center(LARGURA_TELA))
    print("=" * LARGURA_TELA)


def exibir_linha():
    """Exibe uma linha separadora de '-'."""
    print("-" * LARGURA_TELA)


def pausar():
    """Espera o usuário apertar Enter para continuar."""
    input("\nPressione Enter para continuar...")
