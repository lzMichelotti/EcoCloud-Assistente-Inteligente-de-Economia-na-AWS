# 🚀 CloudThrift: FinOps Intelligent Automation

O CloudThrift é um microsserviço de automação para governança financeira (FinOps) na AWS. O projeto identifica recursos ociosos (Volumes EBS e IPs Elásticos), calcula a economia potencial e gerencia o ciclo de vida da deleção através de uma interface de aprovação via Discord.

🛠️ Tecnologias Utilizadas
Linguagem: Python 3.10+ (FastAPI)

Infraestrutura: AWS (EC2, EBS, VPC)

IaC: Terraform

Orquestração: n8n (Self-hosted via Docker)

Interface: Discord (ChatOps)

Integração Cloud: Boto3

🏗️ Arquitetura do Sistema
Scanner: Um script Python consulta a API da AWS em busca de recursos sem uso.

Webhooks: O Python envia os achados para o n8n.

Human-in-the-loop: O n8n pausa a execução e envia um card para o Discord com os detalhes e um link de aprovação.

Action: Após o clique no link, o n8n sinaliza o microsserviço para executar a limpeza via boto3.

📋 Como Executar o Projeto
1. Preparar a Infraestrutura (AWS)
```bash
cd terraform/
terraform init
terraform apply
```
2. Rodar o Microsserviço
```bash
# Instalar dependências a partir do arquivo requirements.txt
pip install -r requirements.txt

# Iniciar API
uvicorn aws_janitor:app --reload
```
3. Configurar o n8n
Importe o arquivo .json do workflow (disponível na pasta /n8n) e configure o Webhook para apontar para o endpoint /scan do microsserviço.

🔮 Roadmap (O que vem por aí)
O projeto está em constante evolução. Os próximos passos planejados são:

[ ] Persistência com PostgreSQL: Implementar uma camada de dados para registrar o histórico de economias e trilha de auditoria.

[ ] Agente de IA (Gemini): Integrar análise de causa raiz para explicar por que os recursos foram esquecidos antes da deleção.

[ ] Observabilidade com Datadog: Dashboard em tempo real mostrando métricas de "Custo Evitado" (Cost Avoidance).

[ ] Multi-região: Suporte para scan em todas as regiões da AWS simultaneamente.

👨‍💻 Autor
Lorenzo Michelotti

Acadêmico de Redes de Computadores na UFSM.

Estagiário de Infraestrutura e Desenvolvimento no LAMIC.

GitHub: lzMichelotti

💡 Dica para o seu GitHub:
Crie a pasta /n8n no seu repositório e coloque lá o arquivo JSON do seu workflow (Vá no n8n -> Três pontinhos no canto superior direito -> Download).

Crie a pasta /terraform e coloque seus arquivos .tf.

Adicione um GIF ou um print do card chegando no seu Discord. Isso chama muita atenção!
