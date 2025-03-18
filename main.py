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
from PyQt6.QtWidgets import QApplication
from controller.uasg_controller import UASGController
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

    # Inicializa o controlador com o diretório base
    controller = UASGController(base_dir)
    controller.run()

    # Executa a aplicação
    sys.exit(app.exec())

if __name__ == "__main__":
    setup_application()

# 711000, 787000, 787010, 787200, 787310, 787320, 787700, 787900, 787400
