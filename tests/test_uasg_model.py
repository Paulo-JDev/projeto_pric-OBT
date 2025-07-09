# tests/test_uasg_model.py
import unittest
import os
import shutil  # Importado para apagar diretórios de forma recursiva
from unittest.mock import patch, MagicMock
from pathlib import Path

# Adiciona o diretório raiz ao path para que possamos importar o model
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from model.uasg_model import UASGModel

class TestUASGModel(unittest.TestCase):

    def setUp(self):
        """
        Configura um ambiente de teste limpo antes de cada teste.
        Cria um diretório temporário para o banco de dados de teste.
        """
        self.test_dir = Path("test_db_dir_temp") # Usando um nome diferente para evitar conflitos
        self.test_dir.mkdir(exist_ok=True)
        
        # Instancia o modelo para usar o diretório de teste
        # O modelo criará seu próprio DB dentro deste diretório
        self.model = UASGModel(base_dir=str(self.test_dir))

        # Dados de exemplo realistas para simular a resposta da API (fornecidos por você)
        self.mock_api_data = [{
            "id": "ontract1",
            "receita_despesa": "Despesa",
            "numero": "00777/2020",
            "contratante": {
                "orgao": {
                    "codigo": "52131",
                    "nome": "BASE NAVAL DE ARATU/BA",
                    "unidade_gestora": {
                        "codigo": "787010",
                        "nome_resumido": "CEIMBRA",
                        "nome": "CENTRO DE INTENDÊNCIA DA MARINHA EM BRASÍLIA",
                    }
                }
            },
            "fornecedor": {
                "nome": "nome fantasma para testes",
                "cnpj_cpf_idgener": "88.555.999/0000-01"
            },
            "objeto": "CONTRATAÇÃO DE EMPRESA ESPECIALIZADA...",
            "valor_global": "104.961,00",
            "vigencia_inicio": "2020-04-09",
            "vigencia_fim": "2025-04-08",
            "tipo": "Contrato",
            "modalidade": "Pregão",
            "licitacao_numero": "00029/2019",
            "processo": "99999.888888/2020-29",
        }]

    def tearDown(self):
        """
        Limpa o ambiente de teste após cada teste usando shutil.rmtree.
        """
        # shutil.rmtree apaga o diretório e todo o seu conteúdo
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_save_and_load_uasg_data(self):
        """
        Testa se os dados de uma UASG são salvos e carregados corretamente no banco de dados.
        """
        uasg = "787010"
        
        # O __init__ do modelo já cria as tabelas, então não precisamos chamar aqui.
        # Apenas chamamos a função para salvar os dados.
        self.model.save_uasg_data(uasg, self.mock_api_data)

        # Carrega os dados salvos para verificação
        loaded_data = self.model.load_saved_uasgs()

        self.assertIn(uasg, loaded_data)
        self.assertEqual(len(loaded_data[uasg]), 1)
        self.assertEqual(loaded_data[uasg][0]["id"], "ontract1") # Corrigido para "ontract1"
        self.assertEqual(loaded_data[uasg][0]["fornecedor"]["nome"], "nome fantasma para testes")

    @patch('model.uasg_model.requests.get')
    def test_fetch_uasg_data_success(self, mock_get):
        """
        Testa a busca de dados da API simulando uma resposta de sucesso.
        """
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.mock_api_data
        mock_get.return_value = mock_response

        data = self.model.fetch_uasg_data("787010")

        self.assertIsNotNone(data)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["id"], "ontract1") # CORRIGIDO: A asserção agora corresponde aos dados do mock

    @patch('model.uasg_model.requests.get')
    def test_fetch_uasg_data_failure(self, mock_get):
        """
        Testa a busca de dados da API simulando uma falha (ex: erro 404).
        """
        mock_get.side_effect = Exception("API Error") # Simplificando a simulação do erro

        # Verifica se a função levanta uma exceção, como esperado
        with self.assertRaises(Exception):
            self.model.fetch_uasg_data("787010")

if __name__ == '__main__':
    unittest.main()