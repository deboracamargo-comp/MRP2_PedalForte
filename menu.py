"""Menus e navegação do sistema (RF01)."""

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
        else:
            print("Opção em construção.")
        utils.pausar()
