🚀 CloudThrift: FinOps Intelligent Automation
O CloudThrift é um microsserviço de automação voltado para governança financeira (FinOps) na AWS. O projeto identifica recursos ociosos (Volumes EBS e IPs Elásticos), utiliza inteligência artificial para análise e gerencia o ciclo de vida da deleção através de uma interface de aprovação via Discord.

Status do Projeto: 🛠️ Em fase de testes de observabilidade (Simulação de ciclo de 1 semana).

🛠️ Tecnologias Utilizadas
Linguagem: Python 3.10+ (FastAPI)

IA Generativa: Google Gemini API (Análise de impacto e justificativa)

Observabilidade: Datadog (Métricas customizadas e Dashboards de FinOps)

Infraestrutura: AWS (EC2, EBS, VPC)

IaC: Terraform

Orquestração: n8n (Self-hosted via Docker)

Interface: Discord (ChatOps)

Integração Cloud: Boto3

🏗️ Arquitetura do Sistema
Scanner: Script Python que consulta a API da AWS em busca de recursos sem uso.

Análise Inteligente: O Gemini analisa os recursos encontrados e gera uma descrição técnica do potencial de economia.

Orquestração & Webhooks: O n8n recebe os dados, pausa a execução e envia um card interativo para o Discord.

Aprovação Humana: Após o clique no botão de aprovação, o n8n sinaliza o microsserviço para executar a limpeza.

Observabilidade: Cada dólar economizado é enviado em tempo real para o Datadog para monitoramento de ROI.

📋 Como Executar o Projeto
1. Preparar a Infraestrutura (AWS)
Utilize o Terraform para criar recursos de teste ociosos:

Bash
cd terraform/
terraform init
terraform apply
2. Rodar o Microsserviço
Bash
# Instalar dependências
pip install -r requirements.txt

# Iniciar API
uvicorn aws_janitor:app --reload
3. Configurar o n8n
Importe o arquivo .json do workflow (pasta /n8n) e configure o Webhook para o endpoint /scan.

🔮 Roadmap & Evolução
[x] PostgreSQL: Camada de dados para registrar o histórico de economias.

[x] Agente de IA (Gemini): Integração de análise técnica para explicar por que os recursos foram esquecidos.

[⏳] Observabilidade (Datadog): Atualmente em teste de estresse de 1 semana para validar a persistência de métricas e comportamento dos gráficos de "Custo Evitado" (Cost Avoidance).

🎯 Objetivo do Projeto
Este projeto foi desenvolvido para fins de treino e estudo avançado em:

Desenvolvimento Backend com Python focado em automação.

Integração de workflows inteligentes com n8n e IA.

Implementação de cultura SRE/FinOps com foco em observabilidade real utilizando Datadog.

👨‍💻 Autor
Lorenzo Michelotti (Lotti)

Acadêmico de Redes de Computadores na UFSM (6º Semestre).

Estagiário de Desenvolvimento no LAMIC.

GitHub: lzMichelotti
