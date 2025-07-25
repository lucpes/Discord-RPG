# upload_templates.py

# Importa a configuração do nosso banco de dados
from firebase_config import db

print("Iniciando upload de templates de itens para o Firebase...")

# --- DEFINA AQUI TODOS OS TEMPLATES DE ITENS QUE VOCÊ QUER ENVIAR ---
# A chave do dicionário será o ID do documento no Firebase.
TEMPLATES_PARA_UPLOAD = {
    "espada_guerreira_raro": {
        "nome": "Espada Longa do Guerreiro",
        "tipo": "ARMA",
        "classe": "Guerreiro",
        "raridade": "RARO",
        "slot": "MAO_PRINCIPAL",
        "slots_encantamento": 2,
        "stats_base": {
            "DANO": { "min": 25, "max": 40 },
            "CRITICO_CHANCE": { "min": 5, "max": 10 }
        }
    },
    "adaga_agil": {
        "nome": "Adaga Ágil",
        "tipo": "ARMA",
        "classe": ["Assassino", "Goblin"],
        "raridade": "INCOMUM",
        "slot": "MAO_PRINCIPAL",
        "slots_encantamento": 1,
        "stats_base": {
            "DANO": { "min": 10, "max": 18 },
            "CRITICO_CHANCE": { "min": 10, "max": 15 }
        }
    },
    "cajado_aprendiz": {
        "nome": "Cajado de Aprendiz",
        "tipo": "ARMA",
        "classe": "Mago",
        "raridade": "COMUM",
        "slot": "MAO_PRINCIPAL",
        "slots_encantamento": 1,
        "stats_base": {
            "DANO": { "min": 12, "max": 20 }
        }
    },
    "escudo_madeira": {
        "nome": "Escudo de Madeira",
        "tipo": "ESCUDO",
        "raridade": "COMUM",
        "slot": "MAO_SECUNDARIA",
        "slots_encantamento": 0,
        "stats_base": {
            "ARMADURA": { "min": 5, "max": 10 },
            "BLOQUEIO_CHANCE": { "min": 5, "max": 10 }
        }
    },
    "peitoral_couro": {
        "nome": "Peitoral de Couro",
        "tipo": "ARMADURA",
        "raridade": "COMUM",
        "slot": "PEITORAL",
        "slots_encantamento": 1,
        "stats_base": {
            "ARMADURA": { "min": 10, "max": 15 },
            "VIDA_MAXIMA": { "min": 15, "max": 25 },
            "MANA_MAXIMA": { "min": 100, "max": 100 }
        }
    }
}

# --- O SCRIPT DE UPLOAD ---
# Este loop vai percorrer cada item e enviá-lo para o Firebase
for doc_id, data in TEMPLATES_PARA_UPLOAD.items():
    try:
        # Pega a referência do documento e usa .set() para criar/sobrescrever
        doc_ref = db.collection('item_templates').document(doc_id)
        doc_ref.set(data)
        print(f"✅ Template '{doc_id}' enviado com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao enviar '{doc_id}': {e}")

print("\nUpload de templates concluído!")

# comando
# python upload_templates.py