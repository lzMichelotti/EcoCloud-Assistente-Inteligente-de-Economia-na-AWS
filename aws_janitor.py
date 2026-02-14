from fastapi import FastAPI, BackgroundTasks
import boto3
import requests
import google.generativeai as genai
from database import SessionLocal, HistoricoLimpeza
import os
from dotenv import load_dotenv
import time
from datadog import initialize, api

app = FastAPI()

# Carrega variáveis de ambiente
load_dotenv()
REGION = os.getenv('REGION', 'us-east-1')
N8N_WEBHOOK_URL = os.getenv('N8N_WEBHOOK_URL')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
options = {
    'api_key': os.getenv('DD_API_KEY'),
    'app_key': os.getenv('DD_APP_KEY'),
    'api_host': 'https://api.datadoghq.com'
}
initialize(**options)


#Configurações
# Cálculo de discos EBS soltos
def get_unused_ebs_costs(region):
    ec2 = boto3.resource('ec2', region_name=region)
    unused_volumes = []
    total_monthly_loss = 0

    for volume in ec2.volumes.filter(Filters=[{'Name': 'status', 'Values': ['available']}]):
        #Preço médio estimado de $0.10 por GB/mês (General Purpose SSD)
        monthly_cost = volume.size * 0.10
        unused_volumes.append({
            'id': volume.id,
            'size_gb': volume.size,
            'cost_est': monthly_cost
        })
        total_monthly_loss += monthly_cost
    return unused_volumes, total_monthly_loss

def get_unassociated_ips(region):
    client = boto3.client('ec2', region_name=region)
    addresses = client.describe_addresses()
    unassociated_ips = []
    total_cost = 0

    for addr in addresses['Addresses']:
        if 'InstanceId' not in addr and 'NetworkInterfaceId' not in addr:
            #IPs elásticos não associados custam aproximadamente $0.005 por hora (~$3.60 por mês)
            cost = 3.60
            unassociated_ips.append({
                'public_ip': addr['PublicIp'],
                'allocation_id': addr['AllocationId'],
                'cost_est': 3.60
            })
            total_cost += cost
    return unassociated_ips, total_cost

def delete_resources(resorce_list, region):
    ec2_client = boto3.client('ec2', region_name=region)

    #Deletando volumes
    for vol in resorce_list.get('volumes', []):
        volume_id = None
        try:
            volume_id = vol.get('id') if isinstance(vol, dict) else vol
            print(f"Limpando Volume: {volume_id}")
            ec2_client.delete_volume(VolumeId=volume_id)
            print(f"Volume {volume_id} deletado com sucesso.")
            registrar_limpeza_banco(
                recurso_id=volume_id,
                tipo="EBS",
                valor=vol['cost_est'],
                regiao=region
            )
            
            # 2. Envia para o Datadog
            valor = vol.get('cost_est', 0.0)
            tipo = vol.get('tipo', 'EBS')
            
            api.Metric.send(
                metric='ecocloud.economia_real',
                points=[(int(time.time()), valor)],
                tags=[f"tipo:{tipo}", "env:prod", "projeto:cloudthrift"]
            )
            print(f"Metrica de ${valor} enviada ao Datadog!")
            
        except Exception as e:
            print(f"Erro ao processar limpeza: {e}")

    for ip in resorce_list.get('ips', []):
        alloc_id = None
        try:
            alloc_id = ip.get('allocation_id') if isinstance(ip, dict) else ip
            print(f"Liberando IP: {alloc_id}")
            ec2_client.release_address(AllocationId=alloc_id)
            print(f"Endereço IP com alocação {alloc_id} liberado com sucesso.")
            registrar_limpeza_banco(
                recurso_id=alloc_id,
                tipo="EIP",
                valor=ip['cost_est'],
                regiao=region
            )
            
            # 2. Envia para o Datadog
            valor = ip.get('cost_est', 0.0)
            tipo = ip.get('tipo', 'EIP')
            
            api.Metric.send(
                metric='ecocloud.economia_real',
                points=[(int(time.time()), valor)],
                tags=[f"tipo:{tipo}", "env:prod", "projeto:cloudthrift"]
            )
            print(f"Metrica de ${valor} enviada ao Datadog!")
            
        except Exception as e:
            print(f"Erro ao processar limpeza: {e}")

def scan_resources(region):
    """Escaneia todos os recursos não utilizados em uma região"""
    try:
        volumes, vol_cost = get_unused_ebs_costs(region)
        ips, ip_cost = get_unassociated_ips(region)
        
        return {
            "region": region,
            "volumes": volumes,
            "vol_cost": vol_cost,
            "ips": ips,
            "ip_cost": ip_cost,
            "total_economia": vol_cost + ip_cost
        }
    except Exception as e:
        raise Exception(f"Erro ao scanear recursos: {str(e)}")

# Configuração Google AI
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

def gerar_analise_ia(recursos):
    prompt = f"""Como um especialista em FinOps, analise estes recursos ociosos da AWS: {recursos}.
Gere um resumo técnico de até 3 frases para o Discord.
Mencione que a economia total será de ${recursos.get('total_economia', 0)}."""
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        erro_msg = f"Erro na IA: {str(e)}"
        print(erro_msg)
        return erro_msg
    
def registrar_limpeza_banco(recurso_id, tipo, valor, regiao):
    """Função para gravar log no PostgreSQL"""
    db = SessionLocal()
    try:
        novo_registro = HistoricoLimpeza(
            tipo=tipo,
            recurso_id=recurso_id,
            regiao=regiao,
            valor_economizado=valor
        )
        db.add(novo_registro)
        db.commit()
        print(f"Registro de limpeza salvo:{recurso_id}")
    except Exception as e:
        print(f"Erro ao salvar registro de limpeza: {e}")
        db.rollback()
    finally:
        db.close()

@app.get("/scan")
def scan_aws():
    dados_aws = scan_resources(REGION)
    
    # Gerar análise IA dos recursos encontrados
    if dados_aws['volumes'] or dados_aws['ips']:
        try:
            dados_aws['analise_ia'] = gerar_analise_ia(dados_aws)
        except Exception as e:
            print(f"Falha no Gemini: {e}")
            dados_aws['analise_ia'] = "Análise da IA indisponível. Recomenda-se revisão manual."
    
    try:
        response = requests.post(N8N_WEBHOOK_URL, json=dados_aws)
        return {"status": "Sucesso", "n8n_response": response.status_code, "dados": dados_aws}
    except Exception as e:
        return {"status": "Erro", "detalhes": str(e)}
    
@app.post("/clean")
def clean_aws(data: dict, background_tasks: BackgroundTasks):
    """Recebe a ordem de limpeza do n8n (O Microsserviço)"""
    resource_list = data
    
    if not resource_list or (not resource_list.get('volumes') and not resource_list.get('ips')):
        return {"message": "Nenhum recurso para limpar", "status": "aviso"}
    
    # Rodar em background para o n8n não ficar esperando o tempo da AWS
    background_tasks.add_task(delete_resources, resource_list, REGION)
    return {"message": "Limpeza iniciada em background", "recursos": resource_list}





if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
