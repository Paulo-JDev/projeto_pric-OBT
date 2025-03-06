# import sys
# from PyQt6.QtWidgets import QApplication
# from controller import ContController
# from view import ContView

# app = QApplication(sys.argv)
# view = ContView()
# controller = ContController(view)
# view.show()
# sys.exit(app.exec())

import sys
from PyQt6.QtWidgets import QApplication
from controller.uasg_controller import UASGController

def setup_application():
    """Inicializa e executa a aplicação."""
    app = QApplication(sys.argv)
    controller = UASGController()
    controller.run()
    sys.exit(app.exec())

if __name__ == "__main__":
    setup_application()

# 711000, 787000, 787010, 787200, 787310, 787320, 787700, 787900, 787400
