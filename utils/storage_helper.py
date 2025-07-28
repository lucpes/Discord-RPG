# utils/storage_helper.py
from datetime import datetime, timedelta, timezone

# Importa o 'bucket' que configuramos
from firebase_config import bucket

def get_signed_url(file_path: str) -> str:
    """
    Gera uma URL pública e temporária para um arquivo no Firebase Storage.
    """
    try:
        # Pega a referência do arquivo no bucket
        blob = bucket.blob(file_path)
        
        # Gera uma URL que expira em 1 dia.
        # Isso é mais que suficiente para o Discord carregar e exibir a imagem.
        expiration_time = datetime.now(timezone.utc) + timedelta(days=1)
        
        return blob.generate_signed_url(expiration=expiration_time)
    except Exception as e:
        print(f"Erro ao gerar URL assinada para '{file_path}': {e}")
        # Retorna uma URL de placeholder se der erro
        return "https://i.imgur.com/sB02t2c.png" # Link para uma imagem de 'erro'