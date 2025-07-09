# tests/test_controller_table.py
import unittest
from datetime import date, timedelta
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtCore import Qt

# Adiciona o diretório raiz ao path para que possamos importar os módulos
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Nota: As funções a serem testadas estão dentro de _populate_or_update_table
# e não são facilmente acessíveis. Para um teste ideal, elas deveriam ser
# extraídas para um módulo de utilidades.
# Por enquanto, vamos recriá-las aqui para demonstrar como testá-las.
# Em uma refatoração futura, você moveria essas funções para 'utils.py'
# e as importaria diretamente.

# Funções extraídas de controller_table.py para teste
def _calculate_dias_restantes_test(vigencia_fim_str):
    from datetime import datetime, date
    if vigencia_fim_str:
        try:
            vigencia_fim = datetime.strptime(vigencia_fim_str, "%Y-%m-%d").date()
            return (vigencia_fim - date.today()).days
        except ValueError:
            return "Erro Data"
    return "Sem Data"

def _get_status_style_test(status_text):
    status_styles = {
        "SEÇÃO CONTRATOS": (Qt.GlobalColor.white, QFont.Weight.Bold),
        "ATA GERADA": (QColor(144, 238, 144), QFont.Weight.Bold),
        "ASSINADO": (QColor(144, 238, 144), QFont.Weight.Bold),
        "ALERTA PRAZO": (QColor(255, 160, 160), QFont.Weight.Bold),
    }
    return status_styles.get(status_text, (Qt.GlobalColor.white, QFont.Weight.Normal))


class TestControllerTableHelpers(unittest.TestCase):

    def test_calculate_dias_restantes(self):
        """
        Testa o cálculo de dias restantes para a vigência do contrato.
        """
        hoje = date.today()
        data_futura = hoje + timedelta(days=30)
        data_passada = hoje - timedelta(days=10)

        self.assertEqual(_calculate_dias_restantes_test(data_futura.strftime("%Y-%m-%d")), 30)
        self.assertEqual(_calculate_dias_restantes_test(data_passada.strftime("%Y-%m-%d")), -10)
        self.assertEqual(_calculate_dias_restantes_test(""), "Sem Data")
        self.assertEqual(_calculate_dias_restantes_test("data-invalida"), "Erro Data")

    def test_get_status_style(self):
        """
        Testa se a formatação de estilo (cor, fonte) para cada status está correta.
        """
        cor_alerta, peso_fonte_alerta = _get_status_style_test("ALERTA PRAZO")
        self.assertEqual(cor_alerta, QColor(255, 160, 160))
        self.assertEqual(peso_fonte_alerta, QFont.Weight.Bold)

        cor_padrao, peso_fonte_padrao = _get_status_style_test("STATUS_INEXISTENTE")
        self.assertEqual(cor_padrao, Qt.GlobalColor.white)
        self.assertEqual(peso_fonte_padrao, QFont.Weight.Normal)

if __name__ == '__main__':
    # Precisamos de uma instância de QApplication para testar widgets do PyQt
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    unittest.main()