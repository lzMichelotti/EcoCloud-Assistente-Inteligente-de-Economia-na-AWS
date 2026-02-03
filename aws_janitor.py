from fastapi import FastAPI, BackgroundTasks
import boto3
import requests

app = FastAPI()

#Alternar a região para a que costuma usar (ex: 'us-west-2' ou 'us-east-1')
REGION = 'us-east-1'
N8N_WEBHOOK_URL = "http://localhost:5678/webhook-test/aws-finops-alert"


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
        except Exception as e:
            print(f"Erro ao deletar volume {volume_id}: {e}")

    for ip in resorce_list.get('ips', []):
        alloc_id = None
        try:
            alloc_id = ip.get('allocation_id') if isinstance(ip, dict) else ip
            print(f"Liberando IP: {alloc_id}")
            ec2_client.release_address(AllocationId=alloc_id)
            print(f"Endereço IP com alocação {alloc_id} liberado com sucesso.")
        except Exception as e:
            print(f"Erro ao liberar endereço IP com alocação {alloc_id}: {e}")

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

@app.get("/scan")
def scan_aws():
    dados_aws = scan_resources(REGION)
    
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
