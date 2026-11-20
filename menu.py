"""Menus e navegação do sistema (RF01)."""

import capacidade
import estoque
import estrutura
import itens
import utils


def exibir_menu_principal(dados):
    """Exibe o menu principal até o usuário escolher sair (RF01)."""
    while True:
        print()
        utils.exibir_titulo("MRP II - PEDAL FORTE BICICLETAS")
        print(" 1. Cadastros (itens, estrutura, centros, roteiros)")
        print(" 2. Estoque (movimentar, saldo, kardex)")
        print(" 3. Plano Mestre de Produção (MPS)")
        print(" 4. Executar MRP")
        print(" 5. Ordens de produção e de compra")
        print(" 6. Carga x capacidade (CRP)")
        print(" 7. Custo padrão dos produtos")
        print(" 8. Relatórios (exportar CSV)")
        print(" 0. Sair")
        utils.exibir_linha()
        opcao = utils.ler_inteiro(" Escolha uma opção: ", 0, 8)

        if opcao == 0:
            print("Encerrando o sistema. Até logo!")
            break
        elif opcao == 1:
            menu_cadastros(dados)
        elif opcao == 2:
            menu_estoque(dados)
        else:
            print("Opção em construção.")
            utils.pausar()


def menu_cadastros(dados):
    """Exibe o submenu de cadastros até o usuário escolher voltar."""
    while True:
        print()
        utils.exibir_titulo("CADASTROS")
        print(" 1. Cadastrar item")
        print(" 2. Listar itens")
        print(" 3. Alterar item")
        print(" 4. Estrutura de produto (BOM)")
        print(" 5. Centros de trabalho")
        print(" 6. Roteiros")
        print(" 0. Voltar")
        utils.exibir_linha()
        opcao = utils.ler_inteiro(" Escolha uma opção: ", 0, 6)

        if opcao == 0:
            break
        elif opcao == 1:
            itens.cadastrar_item(dados)
        elif opcao == 2:
            itens.listar_itens(dados)
        elif opcao == 3:
            itens.alterar_item(dados)
        elif opcao == 4:
            menu_estrutura(dados)
            continue
        elif opcao == 5:
            menu_centros(dados)
            continue
        elif opcao == 6:
            menu_roteiros(dados)
            continue
        else:
            print("Opção em construção.")
        utils.pausar()


def menu_estrutura(dados):
    """Exibe o submenu da estrutura de produto (BOM)."""
    while True:
        print()
        utils.exibir_titulo("ESTRUTURA DE PRODUTO (BOM)")
        print(" 1. Adicionar componente (ou alterar quantidade)")
        print(" 2. Remover componente")
        print(" 3. Exibir estrutura (explosão da BOM)")
        print(" 0. Voltar")
        utils.exibir_linha()
        opcao = utils.ler_inteiro(" Escolha uma opção: ", 0, 3)

        if opcao == 0:
            break
        elif opcao == 1:
            estrutura.adicionar_componente(dados)
        elif opcao == 2:
            estrutura.remover_componente(dados)
        elif opcao == 3:
            estrutura.exibir_estrutura(dados)
        utils.pausar()


def menu_estoque(dados):
    """Exibe o submenu de estoque (RF04, RF05)."""
    while True:
        print()
        utils.exibir_titulo("ESTOQUE")
        print(" 1. Registrar movimentação (entrada, saída, ajuste)")
        print(" 2. Consultar saldo e kardex de um item")
        print(" 3. Posição de estoque (todos os itens)")
        print(" 0. Voltar")
        utils.exibir_linha()
        opcao = utils.ler_inteiro(" Escolha uma opção: ", 0, 3)

        if opcao == 0:
            break
        elif opcao == 1:
            estoque.registrar_movimentacao(dados)
        elif opcao == 2:
            estoque.consultar_kardex(dados)
        elif opcao == 3:
            estoque.listar_posicao(dados)
        utils.pausar()


def menu_centros(dados):
    """Exibe o submenu de centros de trabalho (RF06)."""
    while True:
        print()
        utils.exibir_titulo("CENTROS DE TRABALHO")
        print(" 1. Cadastrar centro")
        print(" 2. Listar centros")
        print(" 3. Alterar centro")
        print(" 0. Voltar")
        utils.exibir_linha()
        opcao = utils.ler_inteiro(" Escolha uma opção: ", 0, 3)

        if opcao == 0:
            break
        elif opcao == 1:
            capacidade.cadastrar_centro(dados)
        elif opcao == 2:
            capacidade.listar_centros(dados)
        elif opcao == 3:
            capacidade.alterar_centro(dados)
        utils.pausar()


def menu_roteiros(dados):
    """Exibe o submenu de roteiros (RF06)."""
    while True:
        print()
        utils.exibir_titulo("ROTEIROS")
        print(" 1. Definir roteiro de um item")
        print(" 2. Listar roteiros")
        print(" 0. Voltar")
        utils.exibir_linha()
        opcao = utils.ler_inteiro(" Escolha uma opção: ", 0, 2)

        if opcao == 0:
            break
        elif opcao == 1:
            capacidade.definir_roteiro(dados)
        elif opcao == 2:
            capacidade.listar_roteiros(dados)
        utils.pausar()
