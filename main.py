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
import logging # Adicionado
from PyQt6.QtWidgets import QApplication
from controller.uasg_controller import UASGController

def setup_logging(base_dir):
    log_dir = os.path.join(base_dir, "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "app.log")

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(module)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout) # Também mostra no console
        ]
    )

def setup_application():
    """Inicializa e executa a aplicação."""
    app = QApplication(sys.argv)

    # Obtém o diretório base (onde o executável está sendo executado)
    if getattr(sys, 'frozen', False):
        # Se estiver rodando como executável
        base_dir = os.path.dirname(sys.executable)
    else:
        # Se estiver rodando como script
        base_dir = os.path.dirname(os.path.abspath(__file__))

    print(f"📁 Diretório base: {base_dir}")
    setup_logging(base_dir) # Configura o logging

    logging.info("Aplicação iniciada.")

    # Inicializa o controlador com o diretório base
    controller = UASGController(base_dir)
    controller.run()

    # Executa a aplicação
    sys.exit(app.exec())
    logging.info("Aplicação finalizada.")

if __name__ == "__main__":
    setup_application()

# 711000, 787000, 787010, 787200, 787310, 787320, 787700, 787900, 787400, 787500 (teste)
# 160298, testando o a parte do git
 