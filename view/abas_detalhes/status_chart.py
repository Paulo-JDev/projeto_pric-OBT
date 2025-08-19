# view/abas_detalhes/status_chart.py

from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCharts import QChart, QChartView, QPieSeries
from PyQt6.QtGui import QPainter, QColor
from PyQt6.QtCore import Qt

class StatusChartWidget(QWidget):
    """
    Um widget customizado para exibir um gráfico de pizza (pie chart) com a 
    distribuição de status dos contratos.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.chart = QChart()
        self.chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        self.chart.setBackgroundVisible(False)
        self.chart.setTitleBrush(QColor("#FFFFFF"))
        self.chart.legend().setLabelColor(QColor("#FFFFFF"))
        self.chart.legend().setAlignment(Qt.AlignmentFlag.AlignRight)

        self.chart_view = QChartView(self.chart)
        self.chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.chart_view)

    def update_chart(self, status_data, color_map):
        """
        Limpa e atualiza o gráfico com novos dados e cores.
        
        Args:
            status_data (dict): Dicionário com status como chaves e contagem como valores.
            color_map (dict): Dicionário mapeando status para cores (QColor).
        """
        self.chart.removeAllSeries()
        
        series = QPieSeries()
        series.setHoleSize(0.35) # Cria o efeito "donut chart"

        for status, count in status_data.items():
            if count > 0:
                slice_ = series.append(f"{status} ({count})", count)
                slice_.setLabelVisible()
                slice_.setLabelColor(QColor("#FFFFFF"))
                
                # Aplica a cor customizada do mapa de cores
                if status in color_map:
                    slice_.setBrush(color_map[status])
        
        self.chart.addSeries(series)

    def clear_chart(self):
        """Limpa todas as séries do gráfico."""
        self.chart.removeAllSeries()