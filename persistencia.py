"""Leitura e gravação dos arquivos de dados do sistema MRP II.

Este é o único módulo do sistema que acessa arquivos. Os demais
módulos trabalham apenas com o dicionário 'dados' em memória.
"""

import csv
import json
from pathlib import Path

PASTA_DADOS = Path(__file__).parent / "data"

ARQUIVOS_JSON = {
    "itens": "itens.json",
    "estrutura": "estrutura.json",
    "estoque": "estoque.json",
    "centros": "centros.json",
    "roteiros": "roteiros.json",
    "mps": "mps.json",
    "ordens": "ordens.json",
}

ARQUIVO_MOVIMENTOS = PASTA_DADOS / "movimentos.csv"
PASTA_EXPORTACAO = Path(__file__).parent / "exports"
CAMPOS_MOVIMENTO = ["data", "codigo", "tipo", "quantidade", "saldo",
                    "documento"]


def carregar_json(nome_arquivo):
    """Lê um arquivo JSON da pasta data/ e devolve seu conteúdo.

    Devolve um dicionário vazio se o arquivo não existir. Se o arquivo
    estiver corrompido, ele é renomeado para '.corrompido' (para que
    os dados não sejam sobrescritos) e um dicionário vazio é devolvido.
    """
    caminho = PASTA_DADOS / nome_arquivo
    try:
        with open(caminho, "r", encoding="utf-8") as arquivo:
            return json.load(arquivo)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        copia = PASTA_DADOS / (nome_arquivo + ".corrompido")
        caminho.replace(copia)
        print(f"AVISO: {nome_arquivo} estava corrompido e foi "
              f"renomeado para {copia.name}.")
        return {}


def salvar_json(nome_arquivo, conteudo):
    """Grava o conteúdo (dicionário) em um arquivo JSON na pasta data/."""
    PASTA_DADOS.mkdir(exist_ok=True)
    caminho = PASTA_DADOS / nome_arquivo
    with open(caminho, "w", encoding="utf-8") as arquivo:
        json.dump(conteudo, arquivo, ensure_ascii=False, indent=2)


def carregar_dados():
    """Carrega todos os arquivos JSON e devolve o dicionário 'dados'."""
    dados = {}
    for chave, nome_arquivo in ARQUIVOS_JSON.items():
        dados[chave] = carregar_json(nome_arquivo)
    return dados


def salvar_dados(dados):
    """Grava todas as partes do dicionário 'dados' em seus arquivos."""
    for chave, nome_arquivo in ARQUIVOS_JSON.items():
        salvar_json(nome_arquivo, dados[chave])


def registrar_movimento(movimento):
    """Acrescenta uma movimentação ao final do kardex (movimentos.csv).

    O arquivo só recebe linhas novas: nenhuma linha é alterada ou
    apagada (RN10). O cabeçalho é escrito se o arquivo for novo.
    """
    PASTA_DADOS.mkdir(exist_ok=True)
    arquivo_novo = (not ARQUIVO_MOVIMENTOS.exists()
                    or ARQUIVO_MOVIMENTOS.stat().st_size == 0)
    with open(ARQUIVO_MOVIMENTOS, "a", encoding="utf-8",
              newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_MOVIMENTO,
                                  delimiter=";")
        if arquivo_novo:
            escritor.writeheader()
        escritor.writerow(movimento)


def ler_movimentos(codigo=None):
    """Lê o kardex e devolve uma lista de movimentações (dicionários).

    Se 'codigo' for informado, devolve apenas as movimentações desse
    item. Devolve uma lista vazia se o arquivo ainda não existir.
    """
    movimentos = []
    try:
        with open(ARQUIVO_MOVIMENTOS, "r", encoding="utf-8",
                  newline="") as arquivo:
            leitor = csv.DictReader(arquivo, delimiter=";")
            for linha in leitor:
                if codigo is None or linha["codigo"] == codigo:
                    linha["quantidade"] = float(linha["quantidade"])
                    linha["saldo"] = float(linha["saldo"])
                    movimentos.append(linha)
    except FileNotFoundError:
        pass
    return movimentos


def caminho_exportacao(nome_arquivo):
    """Devolve o caminho de um arquivo na pasta exports/, criando a
    pasta se ela não existir."""
    PASTA_EXPORTACAO.mkdir(exist_ok=True)
    return PASTA_EXPORTACAO / nome_arquivo


def exportar_csv(nome_arquivo, campos, linhas):
    """Grava uma lista de dicionários em um CSV na pasta exports/.

    Usa ';' como separador e 'utf-8-sig' para que o Excel em português
    abra o arquivo com as colunas e os acentos corretos. Devolve o
    caminho do arquivo gravado.
    """
    caminho = caminho_exportacao(nome_arquivo)
    with open(caminho, "w", encoding="utf-8-sig", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=campos,
                                  delimiter=";")
        escritor.writeheader()
        escritor.writerows(linhas)
    return caminho
