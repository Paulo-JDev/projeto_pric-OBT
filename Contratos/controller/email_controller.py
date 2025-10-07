# controller/email_controller.py

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import os
from dotenv import load_dotenv
from Contratos.model.uasg_model import resource_path

dotenv_path = resource_path(os.path.join('config', '.env'))
load_dotenv(dotenv_path=dotenv_path)

class EmailController:
    def __init__(self, parent_view=None):
        self.parent_view = parent_view
        
        # Suas credenciais e configurações
        # Lê as variáveis do ambiente usando os.getenv()
        self.EMAIL_REMETENTE = os.getenv('EMAIL_REMETENTE')
        self.EMAIL_SENHA = os.getenv('EMAIL_SENHA')
        self.SMTP_SERVER = 'smtp.gmail.com'
        self.SMTP_PORT = 587

    def send_email(self, recipient_email, subject, body, file_path):
        """Envia um e-mail com um anexo."""
        if not recipient_email or not file_path:
            return False, "E-mail do destinatário ou arquivo não fornecido."

        try:
            # Configuração da mensagem
            msg = MIMEMultipart()
            msg['From'] = self.EMAIL_REMETENTE
            msg['To'] = recipient_email
            msg['Subject'] = subject

            # Corpo do e-mail
            msg.attach(MIMEText(body, 'plain'))

            # Anexo
            with open(file_path, 'rb') as f:
                part = MIMEApplication(f.read(), Name=os.path.basename(file_path))
            part['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
            msg.attach(part)

            # Conexão e envio
            with smtplib.SMTP(self.SMTP_SERVER, self.SMTP_PORT) as server:
                server.starttls()
                server.login(self.EMAIL_REMETENTE, self.EMAIL_SENHA)
                server.send_message(msg)
            
            print(f"E-mail enviado com sucesso para {recipient_email}")
            return True, "E-mail enviado com sucesso!"

        except Exception as e:
            print(f"Erro ao enviar e-mail: {e}")
            return False, f"Ocorreu um erro ao enviar o e-mail:\n{str(e)}"