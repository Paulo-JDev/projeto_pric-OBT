## Descrição do projeto

Este projeto é uma aplicação desktop desenvolvida em Python com a biblioteca gráfica PyQt6. 
O objetivo é fornecer uma ferramenta robusta e intuitiva para o gerenciamento e acompanhamento do status de contratos,
permitindo a centralização de registros históricos, comentários e o estado atual de cada processo.

A aplicação foi projetada com foco em boas práticas de engenharia de software, utilizando uma arquitetura limpa para garantir manutenibilidade, 
testabilidade e escalabilidade.

## Principais Funcionalidades

- Busca e Visualização de Contratos: Interface para buscar e carregar detalhes de contratos específicos.
- Gerenciamento de Status: Permite a atualização do status, edição do objeto do contrato e seleção de opções de conformidade.
- Histórico e Comentários: Funcionalidades para adicionar, remover e persistir registros de andamento e comentários relevantes para cada contrato.
- Portabilidade de Dados: Capacidade de exportar todos os dados de um contrato em formato JSON para compartilhamento e backup.
- Persistência Local: Utiliza um banco de dados SQLite para armazenar todas as informações de forma segura e local.

## Tecnologias e conceitos aplicados

Este projeto não é apenas uma aplicação funcional, mas também uma demonstração de conhecimento em tecnologias e conceitos fundamentais para o desenvolvimento de software de qualidade.

- Linguagem: Python 3
- Interface Gráfica (GUI): PyQt6
- Banco de Dados: SQLite 3
- Arquitetura de Software: A aplicação foi estruturada seguindo o padrão MVC (Model-View-Controller), garantindo uma clara separação de responsabilidades:
- Princípios de Programação:
    - Programação Orientada a Objetos (POO): Uso de classes e objetos para modelar o domínio do problema de forma clara.
    - Encapsulamento:** A lógica de acesso a dados é protegida, evitando manipulação direta e inesperada.
- Práticas de Segurança:
    - Prevenção de SQL Injection: Todas as queries ao banco de dados são feitas utilizando Parameterized Queries, a prática mais recomendada para garantir a segurança contra ataques de injeção de SQL.
- Containerização (Ambiente Padronizado):
    - Docker: O projeto inclui um `Dockerfile` para criar um ambiente de desenvolvimento e execução padronizado e isolado, eliminando problemas de dependências entre diferentes máquinas.

## Como executar o Projeto

Existem duas maneiras de executar a aplicação: localmente com um ambiente virtual Python ou através do Docker (método recomendado para garantir consistência).

### 1. Rodando Localmente (Ambiente Virtual)

**Pré-requisitos:** Python 3 e pip instalados.

# 1. Clone o repositório -> git clone https://github.com/Paulo-JDev/projeto_pric-OBT
cd seu-repositorio

# 2. Crie e ative um ambiente virtual
# No Windows:
python -m venv env
.\env\Scripts\activate

# No macOS/Linux:
python3 -m venv env
source env/bin/activate

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Execute a aplicação
python main.py`

### 2. Rodando com Docker (Recomendado)

**Pré-requisitos:** Docker Desktop instalado e em execução.

Bash

# 1. Clone o repositório -> git clone https://github.com/seu-usuario/seu-repositorio.git
cd seu-repositorio

# 2. Construa a imagem Docker -> "docker build -t projeto-pric ."

# 3. Execute o container
# Este comando mapeia a pasta do banco de dados e conecta a GUI ao seu sistema.
# (No Windows/macOS, requer um X Server como VcXsrv/XQuartz)
docker run -it --rm \
    --volume="/tmp/.X11-unix:/tmp/.X11-unix:rw" \
    --env="DISPLAY" \
    --volume="./database:/app/database" \
    projeto-pric

# Fazer o Exe do projeto
pyinstaller --name "Contratos360" --icon="utils/icons/mn.ico" --add-data="utils/icons;utils/icons" --add-data="utils/css/style.qss;utils/css" --add-data="utils/msg;utils/msg" --add-data="utils/template;utils/template" main.py