# utils/inventory_helpers.py
from firebase_config import db

# MODIFICAÇÃO: A assinatura da função agora inclui 'template_id'
def check_inventory_space(char_ref, char_data: dict, item_template: dict, template_id: str) -> bool:
    """
    Verifica se há espaço no inventário para um novo item, considerando o seu tipo.
    Retorna True se houver espaço, False caso contrário.
    """
    limites = char_data.get('limites_inventario', {'equipamentos': 6, 'empilhavel': 12})
    item_tipo = item_template.get('tipo', 'MATERIAL')

    if item_tipo in ["ARMA", "ARMADURA", "ESCUDO", "FERRAMENTA"]:
        limite_atual = limites.get('equipamentos', 6)
        inventario_atual_count = len(list(char_ref.collection('inventario_equipamentos').stream()))
        return inventario_atual_count < limite_atual
    
    else: # MATERIAL, CONSUMIVEL
        limite_atual = limites.get('empilhavel', 12)
        inv_empilhavel_ref = char_ref.collection('inventario_empilhavel')
        
        # MODIFICAÇÃO: A verificação agora usa o 'template_id' recebido como argumento.
        if inv_empilhavel_ref.document(template_id).get().exists:
            return True # Sempre há espaço se o stack já existe
            
        inventario_atual_count = len(list(inv_empilhavel_ref.stream()))
        return inventario_atual_count < limite_atual
        
    return True