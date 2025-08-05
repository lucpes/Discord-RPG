# upload_templates.py

from firebase_config import db

print("Iniciando upload de templates de itens para o Firebase...")

TEMPLATES_PARA_UPLOAD = {
    # --- EQUIPAMENTOS ---
    "espada_guerreira_raro": {
        "nome": "Espada Longa do Guerreiro",
        "emote": "⚔️",
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
        "emote": "🗡️",
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
        "emote": "🪄",
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
        "emote": "🛡️",
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
        "emote": "🎽",
        "tipo": "ARMADURA",
        "raridade": "COMUM",
        "slot": "PEITORAL",
        "slots_encantamento": 1,
        "stats_base": {
            "ARMADURA": { "min": 10, "max": 15 },
            "ARMADURA_MAGICA": { "min": 10, "max": 15 },
            "VIDA_MAXIMA": { "min": 15, "max": 25 },
            "MANA_MAXIMA": { "min": 100, "max": 100 }
        }
    },
    
    # --- MATERIAIS DE CRAFTING ---
    "pele_de_lobo": {
        "nome": "Pele de Lobo",
        "emote": "🐺",
        "tipo": "MATERIAL",
        "raridade": "COMUM",
        "descricao": "Uma pele resistente, usada em armaduras de couro e outros artesanatos."
    },
    "minerio_ferro": {
        "nome": "Minério de Ferro",
        "emote": "🪨",
        "tipo": "MATERIAL",
        "raridade": "INCOMUM",
        "descricao": "Uma rocha rica em ferro, pronta para ser refinada em uma forja."
    },
    
    # --- FERRAMENTAS ---
    "picareta_ferro": {
        "nome": "Picareta de Ferro",
        "emote": "⛏️",
        "tipo": "FERRAMENTA",
        "raridade": "INCOMUM",
        "slot": "PICARETA",
        "slots_encantamento": 0,
        "descricao": "Permite a mineração de veios de ferro e outros minerais.",
        "atributos_ferramenta": {
            "nivel_mineração": 2,
            "poder_coleta": 0.25,
            "eficiencia": 0.15,
            "durabilidade_max": 250,
            "fortuna": 0
        }
    },
    "machado_lenhador": {
        "nome": "Machado de Lenhador",
        "emote": "🪓",
        "tipo": "FERRAMENTA",
        "raridade": "COMUM",
        "slot": "MACHADO",
        "slots_encantamento": 0,
        "descricao": "Ideal para derrubar árvores e coletar madeira.",
        "atributos_ferramenta": {
            "nivel_mineração": 2,
            "poder_coleta": 0.25,
            "eficiencia": 0.15,
            "durabilidade_max": 250,
            "fortuna": 0
        }
    },

    # --- CONSUMÍVEIS (POÇÕES) ---
    "pocao_vida_pequena": {
        "nome": "Poção de Vida Pequena",
        "emote": "🧪",
        "tipo": "CONSUMIVEL",
        "raridade": "COMUM",
        "descricao": "Restaura instantaneamente uma pequena quantidade de vida.",
        "efeito_consumo": {
            "CURA_VIDA": 50
        }
    },
}

# --- O SCRIPT DE UPLOAD ---
for doc_id, data in TEMPLATES_PARA_UPLOAD.items():
    try:
        doc_ref = db.collection('item_templates').document(doc_id)
        doc_ref.set(data)
        print(f"✅ Template '{doc_id}' enviado com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao enviar '{doc_id}': {e}")

print("\nUpload de templates concluído!")

# comando
# python upload_templates.py