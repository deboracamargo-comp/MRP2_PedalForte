"""Ponto de entrada do sistema MRP II - Pedal Forte Bicicletas."""

import menu
import persistencia


def main():
    """Carrega os dados (RF15) e abre o menu principal."""
    dados = persistencia.carregar_dados()
    try:
        menu.exibir_menu_principal(dados)
    except (KeyboardInterrupt, EOFError):
        print("\nPrograma interrompido pelo usuário.")


if __name__ == "__main__":
    main()
