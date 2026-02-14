#Criação de recursos AWS para testes do projeto

provider "aws" {
  region = "us-east-1"
}

# 1. Criando um volume EBS de 1GB (Custo baixo)
resource "aws_ebs_volume" "test_volume" {
  count = 3
  availability_zone = "us-east-1a"
  size              = 1
  tags = {
    Name = "Lixo-Teste-FinOps"
  }
}

# 2. Cria um IP Elástico (IP Público)
resource "aws_eip" "test_ip" {
  count = 3
  domain = "vpc"
  tags = {
    Name = "IP-Teste-FinOps"
  }
}