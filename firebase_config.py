# firebase_config.py
import firebase_admin
from firebase_admin import credentials, firestore, storage

# Carrega as credenciais do arquivo JSON que você baixou
# Certifique-se de que o caminho está correto
cred = credentials.Certificate("firebase-credentials.json")

BUCKET_NAME = "discordrpg-a9420.firebasestorage.app" 

# Inicializa o app do Firebase. A verificação 'try/except' garante que isso só aconteça uma vez.
try:
    firebase_admin.initialize_app(cred, {
        'storageBucket': BUCKET_NAME
    })
    print("App do Firebase inicializado com sucesso!")
except ValueError:
    print("O app do Firebase já foi inicializado.")

# Cria uma instância do cliente do Firestore para que possamos usá-la em outros arquivos
db = firestore.client()
bucket = storage.bucket() # Objeto para interagir com o Storage
print(f"Conectado ao bucket: {bucket.name}")

# --- ESTRUTURA DO BANCO DE DADOS QUE USAREMOS ---
#
# game_counters (coleção)
# └── player_id (documento)
#     └── {'last_id': 1000} (campo)
#
# players (coleção)
# └── {discord_user_id} (documento)
#     ├── {'nick': 'NomeDoJogador'}
#     └── {'game_id': 1001}
#
# characters (coleção)
# └── {discord_user_id} (documento)
#     ├── {'classe': 'Guerreiro'}
#     ├── {'nivel': 1}
#     └── ... outros dados do personagem
#