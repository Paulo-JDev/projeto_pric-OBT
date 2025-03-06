
# esse codigo coloca check box para mostrar ou não os dados
# from PyQt6.QtWidgets import QDialog, QLabel, QVBoxLayout, QCheckBox, QScrollArea, QWidget, QPushButton

# class DetailsDialog(QDialog):
#     def __init__(self, data, parent=None):
#         super().__init__(parent)
#         self.setWindowTitle("Detalhes do Contrato")
#         self.setFixedSize(800, 600)

#         self.data = data  # Dados do contrato

#         # Layout principal
#         self.main_layout = QVBoxLayout(self)

#         # Criar um widget rolável para acomodar as informações
#         scroll = QScrollArea(self)
#         scroll.setWidgetResizable(True)
#         self.scroll_widget = QWidget()
#         self.scroll_layout = QVBoxLayout(self.scroll_widget)
#         scroll.setWidget(self.scroll_widget)

#         self.main_layout.addWidget(scroll)

#         # Criar checkboxes dinâmicos para ativar/desativar campos
#         self.checkboxes = {}
#         self.labels = {}

#         for key, value in self.data.items():
#             # Criar checkbox para cada campo
#             checkbox = QCheckBox(f"{key.replace('_', ' ').title()}")
#             checkbox.setChecked(True)  # Marcar por padrão
#             checkbox.stateChanged.connect(self.update_display)
#             self.checkboxes[key] = checkbox

#             # Criar label para exibir o valor do campo
#             label = QLabel(str(value))
#             self.labels[key] = label

#             # Adicionar checkbox e label ao layout
#             self.scroll_layout.addWidget(checkbox)
#             self.scroll_layout.addWidget(label)

#         # Botão para fechar
#         close_button = QPushButton("Fechar")
#         close_button.clicked.connect(self.close)
#         self.main_layout.addWidget(close_button)

#     def update_display(self):
#         """Atualiza a exibição dos detalhes conforme os checkboxes são ativados/desativados."""
#         for key, label in self.labels.items():
#             label.setVisible(self.checkboxes[key].isChecked())  # Exibir apenas se o checkbox estiver ativado
