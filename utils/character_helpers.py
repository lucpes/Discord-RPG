# utils/character_helpers.py
from firebase_config import db

def load_player_sheet(user_id_str: str):
    """
    Carrega todos os dados de um personagem, incluindo itens equipados no formato correto.
    Retorna um dicionário com 'player_data', 'char_data', e 'equipped_items', ou None se não encontrado.
    """
    player_ref = db.collection('players').document(user_id_str)
    char_ref = db.collection('characters').document(user_id_str)

    player_doc = player_ref.get()
    char_doc = char_ref.get()

    if not player_doc.exists or not char_doc.exists:
        return None

    player_data = player_doc.to_dict()
    char_data = char_doc.to_dict()

    equipped_items = []
    # Lê da coleção correta 'inventario_equipamentos'
    inventory_snapshot = char_ref.collection('inventario_equipamentos').where('equipado', '==', True).stream()

    for item_ref in inventory_snapshot:
        item_id = item_ref.id
        instance_doc = db.collection('items').document(item_id).get()
        if not instance_doc.exists:
            continue

        instance_data = instance_doc.to_dict()
        template_id = instance_data.get('template_id')
        if not template_id:
            continue

        template_doc = db.collection('item_templates').document(template_id).get()
        if not template_doc.exists:
            continue

        # Monta o dicionário completo e padronizado do item
        full_item_data = {
            "id": item_id,
            "instance_data": instance_data,
            "template_data": template_doc.to_dict()
        }
        equipped_items.append(full_item_data)

    return {
        "player_data": player_data,
        "char_data": char_data,
        "equipped_items": equipped_items
    }