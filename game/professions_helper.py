# game/professions_helper.py
from firebase_config import db
from data.profissoes_library import PROFISSOES

def grant_profession_xp(user_id: str, profession_id: str, amount: int):
    """
    Concede XP a uma profissão específica, processa o level up e retorna o resultado.
    """
    char_ref = db.collection('characters').document(user_id)
    char_doc = char_ref.get()
    if not char_doc.exists:
        return

    char_data = char_doc.to_dict()
    prof_data = char_data.get('profissoes', {}).get(profession_id, {'nivel': 1, 'xp': 0})
    
    current_level = prof_data['nivel']
    current_xp = prof_data['xp'] + amount
    
    profession_info = PROFISSOES.get(profession_id)
    if not profession_info:
        return

    # Loop de Level Up
    leveled_up = False
    while current_level <= len(profession_info['niveis']):
        xp_needed = profession_info['niveis'][current_level - 1].get('xp_para_upar')
        if xp_needed is None: # Nível máximo
            break
            
        if current_xp >= xp_needed:
            current_xp -= xp_needed
            current_level += 1
            leveled_up = True
        else:
            break # XP insuficiente para o próximo nível

    # Atualiza os dados no Firebase
    update_path = f"profissoes.{profession_id}"
    char_ref.update({
        update_path: {'nivel': current_level, 'xp': current_xp}
    })

    # No futuro, podemos fazer esta função retornar um dicionário com os detalhes do level up
    # para enviar uma notificação por DM, como fizemos com o nível do personagem.
    if leveled_up:
        print(f"O jogador {user_id} subiu para o nível {current_level} em {profession_id}!")