# import sys
# from PyQt6.QtWidgets import QApplication
# from controller import ContController
# from view import ContView

# app = QApplication(sys.argv)
# view = ContView()
# controller = ContController(view)
# view.show()
# sys.exit(app.exec())

# _internal

import sys
import os
import logging
from PyQt6.QtWidgets import QApplication
from utils.utils import resource_path

APP_VERSION = "11.0.1"

def install_global_exception_hook():
    """Evita traceback ruidoso para KeyboardInterrupt disparado dentro do loop Qt."""
    def _hook(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            logging.info("KeyboardInterrupt capturado no loop principal; ação cancelada sem derrubar app.")
            return

        logging.error("Exceção não tratada no loop principal.", exc_info=(exc_type, exc_value, exc_traceback))

    sys.excepthook = _hook

def setup_logging(base_dir):
    # (Sua função de logging continua a mesma)
    log_dir = os.path.join(base_dir, "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "app.log")
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(module)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def setup_application():
    """Inicializa e executa a aplicação com a nova estrutura."""
    app = QApplication(sys.argv)

    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))

    print(f"📦 Versão do APP V{APP_VERSION}")
    print(f"📁 Diretório base: {base_dir}")
    setup_logging(base_dir)
    install_global_exception_hook()
    logging.info("Aplicação iniciada com a nova estrutura modular.")

    # Importações tardias reduzem o custo de bootstrap do Python e evitam
    # travamentos longos durante import em ambientes como VSCode.
    from view.main_shell_view import MainShellView
    from controller.main_controller import MainController

    # Carrega o estilo antes de criar a janela
    style_path = resource_path("utils/css/style.qss")
    try:
        with open(style_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
            #print(f"🎨 Estilo carregado de: {style_path}")
    except FileNotFoundError:
        print(f"AVISO: Arquivo de estilo não encontrado em '{style_path}'.")

    # 1. Cria a janela principal (Shell)
    main_view = MainShellView()
    
    # 2. Cria o controlador principal, que gerencia os módulos
    main_controller = MainController(main_view, base_dir)
    
    # 3. Inicia a aplicação
    main_controller.run()
    
    sys.exit(app.exec())
    logging.info("Aplicação finalizada.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        setup_application()
    except KeyboardInterrupt:
        # Captura o sinal de interrupção (Ctrl+C ou Stop da IDE) graciosamente
        print("\n⏳ Inicialização cancelada (KeyboardInterrupt). Encerrando o programa.")
        sys.exit(0)
    except Exception as e:
        # Captura qualquer outro erro fatal na inicialização
        logging.error(f"Erro fatal ao iniciar a aplicação: {e}")
        print(f"❌ Erro fatal: {e}")
        sys.exit(1)

# 711000, 787000, 787010, 787200, 787310, 787320, 787700, 787900, 787400, 787500 (testes)
# 160298, testando o a parte do git
