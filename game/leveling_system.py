# game/leveling_system.py
from firebase_config import db
from data.game_config import calcular_xp_para_nivel

def grant_xp(user_id: str, amount: int) -> dict:
    """
    Dá uma quantidade de XP a um personagem, processa o level up e retorna o resultado.
    """
    char_ref = db.collection('characters').document(user_id)
    char_doc = char_ref.get()

    if not char_doc.exists:
        return {"success": False, "reason": "Personagem não encontrado."}

    char_data = char_doc.to_dict()
    
    # Pega os dados atuais ou define valores padrão se não existirem
    current_level = char_data.get('nivel', 1)
    current_xp = char_data.get('xp', 0)
    
    # Guarda o nível original para comparar depois
    original_level = current_level
    
    # Adiciona o novo XP
    current_xp += amount

    # Calcula o XP necessário para o próximo nível
    xp_needed = calcular_xp_para_nivel(current_level)

    # --- O LOOP DE LEVEL UP ---
    # Este loop continua rodando enquanto o jogador tiver XP para subir de nível.
    # Isso lida com múltiplos level ups de uma vez.
    while current_xp >= xp_needed:
        # Sobe de nível
        current_xp -= xp_needed
        current_level += 1
        
        # Calcula o XP necessário para o *novo* próximo nível
        xp_needed = calcular_xp_para_nivel(current_level)

    # Prepara os dados para salvar no Firebase
    update_data = {
        'nivel': current_level,
        'xp': current_xp
    }
    char_ref.update(update_data)

    # Retorna um dicionário com o resultado da operação
    return {
        "success": True,
        "leveled_up": current_level > original_level,
        "original_level": original_level,
        "new_level": current_level,
        "xp_ganho": amount,
        "xp_atual": current_xp,
        "xp_para_upar": xp_needed
    }