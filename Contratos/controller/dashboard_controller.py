# Contratos/controller/dashboard_controller.py

from PyQt6.QtCore import QObject
from PyQt6.QtGui import QColor
from datetime import datetime

class DashboardController(QObject):
    # CORREÇÃO 1: A ordem dos parâmetros deve ser (model, view) para bater com uasg_controller.py
    def __init__(self, model, view):
        super().__init__()
        self.model = model
        self.view = view
        
        # Mapeamento de cores solicitado (Mantido exatamente como você pediu)
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
            "PRORROGADO": QColor(135, 206, 250),
            "SIGAD" : QColor(230, 180, 100)
        }

    def clear_dashboard(self):
        """Limpa os dados do dashboard."""
        widgets = self.view.dashboard_widgets
        if widgets:
            widgets['value_label']['total_contratos'].setText("0")
            widgets['value_label']['valor_total'].setText("R$ 0,00")
            widgets['value_label']['ativos'].setText("0")
            widgets['value_label']['expirando'].setText("0")
            widgets['status_chart'].clear_chart()

    def _get_status_for_contrato(self, contrato_id):
        """Helper para pegar o status real (banco ou calculado) de um contrato."""
        # Agora self.model é realmente o modelo, então _get_db_connection vai funcionar
        if not contrato_id:
            return "SEÇÃO CONTRATOS"

        try:
            conn = self.model._get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT status FROM status_contratos WHERE contrato_id = ?", (contrato_id,))
            row = cursor.fetchone()
            conn.close()

            if row and row[0]:
                return row[0]
        except Exception as e:
            print(f"Erro ao buscar status do contrato {contrato_id}: {e}")
            return "SEÇÃO CONTRATOS"

        return "SEÇÃO CONTRATOS"

    def update_dashboard(self, data):
        """Calcula as métricas e atualiza os widgets do dashboard, incluindo o tooltip."""
        if not data:
            self.clear_dashboard()
            return
            
        # --- Cálculos das Métricas ---
        total_contratos = len(data)
        status_counts = {}
        
        # Inicializa contadores baseados no mapa de cores conhecido
        for status_key in self.status_color_map.keys():
            status_counts[status_key] = 0

        # Conta os status reais
        for contrato in data:
            status = self._get_status_for_contrato(contrato.get('id'))
            # Se o status do banco estiver no nosso mapa, incrementa
            if status in status_counts:
                status_counts[status] += 1
            else:
                # Se for um status novo/estranho, adiciona dinamicamente ou agrupa em "Outros"
                status_counts[status] = status_counts.get(status, 0) + 1

        # --- FUNÇÃO DE CONVERSÃO SEGURA (Do erro anterior) ---
        def safe_float(val):
            if not val:
                return 0.0
            try:
                # 1. Converte para string e limpa "R$" e espaços
                val_str = str(val).replace("R$", "").strip()
                
                # 2. Lógica de decisão de formato:
                if ',' in val_str:
                    # Se tem vírgula, assume formato BR (1.000,00 ou 1000,00)
                    val_str = val_str.replace('.', '').replace(',', '.')
                
                return float(val_str)
            except ValueError:
                return 0.0

        # Calcula valor total usando a função segura
        valor_total = sum(safe_float(c.get("valor_global")) for c in data)
        
        hoje = datetime.now().date()
        contratos_ativos = 0
        expirando_90_dias_list = []
        
        for contrato in data:
            fim_vigencia_str = contrato.get("vigencia_fim")
            if fim_vigencia_str:
                try:
                    data_limpa = fim_vigencia_str.split(' ')[0]
                    fim_vigencia = datetime.strptime(data_limpa, "%Y-%m-%d").date()
                    
                    if fim_vigencia >= hoje:
                        contratos_ativos += 1
                        if (fim_vigencia - hoje).days <= 90:
                            expirando_90_dias_list.append(contrato)
                except (ValueError, TypeError):
                    continue
        
        # --- Geração do Tooltip ---
        if expirando_90_dias_list:
            tooltip_html = """
            <style>
                table { 
                    border-collapse: collapse; 
                    background-color: #2b2b2b; 
                    color: #e0e0e0; 
                    font-family: Segoe UI, sans-serif;
                    font-size: 11px;
                }
                th, td { 
                    border: 1px solid #555; 
                    padding: 4px 8px; 
                    text-align: left; 
                }
                th { 
                    background-color: #3a3a3a; 
                    font-weight: bold; 
                    color: #ffffff;
                }
                tr:nth-child(even) {
                    background-color: #333333;
                }
            </style>
            <p style='color:white; font-weight:bold'>Contratos vencendo em 90 dias:</p>
            <table>
                <tr><th>Número</th><th>Licitação</th><th>Vencimento</th></tr>
            """
            expirando_90_dias_list.sort(key=lambda x: x.get("vigencia_fim", ""))
            
            for contrato in expirando_90_dias_list[:15]:
                numero = contrato.get('numero', 'N/A')
                licitacao = contrato.get('licitacao_numero', '-')
                venc = contrato.get('vigencia_fim', '').split(' ')[0]
                try:
                    venc_br = datetime.strptime(venc, "%Y-%m-%d").strftime("%d/%m/%Y")
                except:
                    venc_br = venc
                
                tooltip_html += f"<tr><td>{numero}</td><td>{licitacao}</td><td>{venc_br}</td></tr>"
            
            if len(expirando_90_dias_list) > 15:
                 tooltip_html += f"<tr><td colspan='3' style='text-align:center'>... e mais {len(expirando_90_dias_list)-15} contratos ...</td></tr>"
            
            tooltip_html += "</table>"
        else:
            tooltip_html = "Nenhum contrato expirando nos próximos 90 dias."

        # --- Atualização dos Widgets na View ---
        if self.view.dashboard_widgets:
            widgets = self.view.dashboard_widgets
            widgets['value_label']['total_contratos'].setText(str(total_contratos))
            
            valor_fmt = f"R$ {valor_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            widgets['value_label']['valor_total'].setText(valor_fmt)
            
            widgets['value_label']['ativos'].setText(str(contratos_ativos))
            widgets['value_label']['expirando'].setText(str(len(expirando_90_dias_list)))

            # Envia o mapa de cores personalizado para o gráfico
            widgets['status_chart'].update_chart(status_counts, self.status_color_map)

            widgets['card']['expirando'].setToolTip(tooltip_html)