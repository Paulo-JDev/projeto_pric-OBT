# controller/dashboard_controller.py

from datetime import datetime
import sqlite3
from PyQt6.QtGui import QColor
from PyQt6.QtCore import Qt

class DashboardController:
    def __init__(self, model, view):
        self.model = model
        self.view = view
        # Conecta o botão de atualizar à função de atualização
        self.view.refresh_dashboard_button.clicked.connect(self.refresh_data)

        self.status_color_map = {
            "SEÇÃO CONTRATOS": QColor("#FFFFFF"),
            "PORTARIA": QColor(230, 230, 150),
            "EMPRESA": QColor(230, 230, 150),
            "SIGDEM": QColor(230, 180, 100),
            "ASSINADO": QColor(230, 180, 100),
            "PUBLICADO": QColor(135, 206, 250),
            "ALERTA PRAZO": QColor(255, 160, 160),
            "NOTA TÉCNICA": QColor(255, 160, 160),
            "AGU": QColor(255, 160, 160),
            "PRORROGADO": QColor(135, 206, 250)
        }

    def _get_status_for_contrato(self, contrato_id):
        """
        Busca o status de um contrato específico no banco de dados.
        """
        status_text = "SEÇÃO CONTRATOS"
        if not contrato_id:
            return status_text
        try:
            conn = self.model._get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT status FROM status_contratos WHERE contrato_id = ?", (contrato_id,))
            status_row = cursor.fetchone()
            if status_row and status_row['status']:
                status_text = status_row['status']
            conn.close()
        except sqlite3.Error as e:
            print(f"Erro ao buscar status do DB para contrato {contrato_id}: {e}")
            status_text = "Erro DB"
        return status_text

    def refresh_data(self):
        """Força a atualização do dashboard com os dados atuais da tabela."""
        current_data = self.view.controller.current_data
        if not current_data:
            print("Dashboard: Nenhum dado para atualizar.")
            self.clear_dashboard()
        else:
            self.update_dashboard(current_data)
            
    def clear_dashboard(self):
        """Limpa todos os campos do dashboard e o tooltip."""
        for key in self.view.dashboard_widgets['value_label']:
            self.view.dashboard_widgets['value_label'][key].setText("N/A")
        
        # Limpa o tooltip do card "expirando"
        if 'card' in self.view.dashboard_widgets and 'expirando' in self.view.dashboard_widgets['card']:
            self.view.dashboard_widgets['card']['expirando'].setToolTip("")

    def update_dashboard(self, data):
        """Calcula as métricas e atualiza os widgets do dashboard, incluindo o tooltip."""
        if not data:
            self.clear_dashboard()
            return
            
        # --- Cálculos das Métricas ---
        total_contratos = len(data)
        status_counts = {}
        for status_name in self.status_color_map.keys():
            status_counts[status_name] = 0 # Inicializa todos os status com 0

        for contrato in data:
            status = self._get_status_for_contrato(contrato.get('id'))
            if status in status_counts:
                status_counts[status] += 1
            else: # Caso encontre um status não mapeado
                status_counts[status] = 1

        valor_total = sum(float(c.get("valor_global", "0,00").replace('.', '').replace(',', '.')) for c in data if c.get("valor_global"))
        
        hoje = datetime.now().date()
        contratos_ativos = 0
        expirando_90_dias_list = []
        
        for contrato in data:
            fim_vigencia_str = contrato.get("vigencia_fim")
            if fim_vigencia_str:
                try:
                    fim_vigencia = datetime.strptime(fim_vigencia_str, "%Y-%m-%d").date()
                    if fim_vigencia >= hoje:
                        contratos_ativos += 1
                        if (fim_vigencia - hoje).days <= 90:
                            expirando_90_dias_list.append(contrato)
                except (ValueError, TypeError):
                    continue
        
        # --- Geração do Tooltip em formato de tabela HTML com estilo dark ---
        if expirando_90_dias_list:
            tooltip_html = """
            <style>
                table { 
                    border-collapse: collapse; 
                    width: 100%; 
                    background-color: #1E1E1E; /* Fundo preto */
                    color: #FFFFFF; /* Letra branca */
                }
                th, td { 
                    border: 1px solid #555; 
                    padding: 5px; 
                    text-align: left; 
                }
                th { 
                    background-color: #333; 
                    font-weight: bold; 
                }
            </style>
            <table>
                <tr><th>Contrato/Licitação</th><th>Status</th></tr>
            """
            for contrato in expirando_90_dias_list:
                numero = contrato.get('numero', 'N/A')
                licitacao = contrato.get('licitacao_numero', 'N/A')
                status = self._get_status_for_contrato(contrato.get('id'))
                tooltip_html += f"<tr><td>{numero} / {licitacao}</td><td>{status}</td></tr>"
            
            tooltip_html += "</table>"
        else:
            tooltip_html = "Nenhum contrato expirando nos próximos 90 dias."

        # --- Atualização dos Widgets na View ---
        widgets = self.view.dashboard_widgets
        widgets['value_label']['total_contratos'].setText(str(total_contratos))
        widgets['value_label']['valor_total'].setText(f"R$ {valor_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        widgets['value_label']['ativos'].setText(str(contratos_ativos))
        widgets['value_label']['expirando'].setText(str(len(expirando_90_dias_list)))

        widgets['status_chart'].update_chart(status_counts, self.status_color_map)

        # Aplica o tooltip gerado ao card "Expirando em 90 dias"
        widgets['card']['expirando'].setToolTip(tooltip_html)