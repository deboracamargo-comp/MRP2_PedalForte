"""Menus e navegação do sistema (RF01)."""

import capacidade
import custos
import estoque
import estrutura
import graficos
import itens
import mps
import mrp
import ordens
import relatorios
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
        print(" 9. Gráficos de gestão")
        print(" 0. Sair")
        utils.exibir_linha()
        opcao = utils.ler_inteiro(" Escolha uma opção: ", 0, 9)

        if opcao == 0:
            print("Encerrando o sistema. Até logo!")
            break
        elif opcao == 1:
            menu_cadastros(dados)
        elif opcao == 2:
            menu_estoque(dados)
        elif opcao == 3:
            menu_mps(dados)
        elif opcao == 4:
            menu_mrp(dados)
        elif opcao == 5:
            menu_ordens(dados)
        elif opcao == 6:
            capacidade.exibir_crp(dados)
            utils.pausar()
        elif opcao == 7:
            custos.exibir_custos(dados)
            utils.pausar()
        elif opcao == 8:
            menu_relatorios(dados)
        elif opcao == 9:
            menu_graficos(dados)


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


def menu_mps(dados):
    """Exibe o submenu do Plano Mestre de Produção (RF07)."""
    while True:
        print()
        utils.exibir_titulo("PLANO MESTRE DE PRODUÇÃO (MPS)")
        print(" 1. Cadastrar MPS de um produto (8 semanas)")
        print(" 2. Alterar demanda de uma semana")
        print(" 3. Exibir MPS")
        print(" 0. Voltar")
        utils.exibir_linha()
        opcao = utils.ler_inteiro(" Escolha uma opção: ", 0, 3)

        if opcao == 0:
            break
        elif opcao == 1:
            mps.cadastrar_mps(dados)
        elif opcao == 2:
            mps.alterar_semana(dados)
        elif opcao == 3:
            mps.exibir_mps(dados)
        utils.pausar()


def menu_mrp(dados):
    """Exibe o submenu do MRP (RF08, RF09)."""
    while True:
        print()
        utils.exibir_titulo("MRP")
        print(" 1. Executar MRP (gerar ordens planejadas)")
        print(" 2. Exibir registro MRP de um item")
        print(" 0. Voltar")
        utils.exibir_linha()
        opcao = utils.ler_inteiro(" Escolha uma opção: ", 0, 2)

        if opcao == 0:
            break
        elif opcao == 1:
            mrp.executar_mrp(dados)
        elif opcao == 2:
            mrp.exibir_registro(dados)
        utils.pausar()


def menu_ordens(dados):
    """Exibe as ordens e as ações do ciclo de status (RF10, RF11)."""
    while True:
        print()
        ordens.listar_ordens(dados)
        utils.exibir_linha()
        print("[F] Firmar  [L] Liberar  [E] Encerrar OC  "
              "[A] Apontar produção  [V] Voltar")
        opcao = utils.ler_opcao("Escolha: ", ["F", "L", "E", "A", "V"])

        if opcao == "V":
            break
        elif opcao == "F":
            ordens.firmar_ordem(dados)
        elif opcao == "L":
            ordens.liberar_ordem(dados)
        elif opcao == "E":
            ordens.encerrar_compra(dados)
        elif opcao == "A":
            ordens.apontar_producao(dados)
        utils.pausar()


def menu_relatorios(dados):
    """Exibe o submenu de exportação de relatórios em CSV (RF14)."""
    while True:
        print()
        utils.exibir_titulo("RELATÓRIOS (EXPORTAR CSV)")
        print(" 1. Exportar posição de estoque")
        print(" 2. Exportar lista de ordens")
        print(" 0. Voltar")
        utils.exibir_linha()
        opcao = utils.ler_inteiro(" Escolha uma opção: ", 0, 2)

        if opcao == 0:
            break
        elif opcao == 1:
            relatorios.exportar_estoque(dados)
        elif opcao == 2:
            relatorios.exportar_ordens(dados)
        utils.pausar()


def menu_graficos(dados):
    """Exibe o submenu de gráficos de gestão (RF16)."""
    while True:
        print()
        utils.exibir_titulo("GRÁFICOS DE GESTÃO")
        print(" 1. Posição de estoque (saldo x estoque de segurança)")
        print(" 2. Estoque projetado de um item (MRP)")
        print(" 3. Ordens por semana de entrega (OP x OC)")
        print(" 4. Carga x capacidade de um centro")
        print(" 0. Voltar")
        utils.exibir_linha()
        opcao = utils.ler_inteiro(" Escolha uma opção: ", 0, 4)

        if opcao == 0:
            break
        elif opcao == 1:
            graficos.grafico_posicao_estoque(dados)
        elif opcao == 2:
            graficos.grafico_estoque_projetado(dados)
        elif opcao == 3:
            graficos.grafico_ordens_por_semana(dados)
        elif opcao == 4:
            graficos.grafico_carga_capacidade(dados)
        utils.pausar()
