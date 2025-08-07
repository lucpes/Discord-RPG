# update_profissoes.py
# Este é um script temporário para adicionar o mapa de profissões a todos os personagens existentes.

from firebase_config import db
from data.profissoes_library import PROFISSOES # Importa nossa lista de profissões

print("--- Iniciando script de atualização de profissões ---")

try:
    # 1. Busca todos os documentos da coleção 'characters'
    chars_ref = db.collection('characters')
    all_characters = chars_ref.stream()

    # Cria um batch para executar todas as atualizações de uma vez
    batch = db.batch()
    updated_count = 0

    # 2. Itera sobre cada personagem
    for char_doc in all_characters:
        char_data = char_doc.to_dict()
        
        # 3. Verifica se o personagem já tem o campo 'profissoes'
        if 'profissoes' not in char_data:
            print(f"Atualizando personagem ID: {char_doc.id}...")
            
            # 4. Cria o mapa de profissões padrão
            profissoes_padrao = {}
            for prof_id in PROFISSOES.keys():
                profissoes_padrao[prof_id] = {
                    "nivel": 1,
                    "xp": 0
                }
            
            # 5. Adiciona a atualização ao batch
            char_ref_to_update = chars_ref.document(char_doc.id)
            batch.update(char_ref_to_update, {'profissoes': profissoes_padrao})
            updated_count += 1
        else:
            print(f"Personagem ID: {char_doc.id} já possui profissões. Ignorando.")

    # 6. Executa todas as atualizações no Firebase
    if updated_count > 0:
        batch.commit()
        print(f"\n✅ Operação concluída! {updated_count} personagem(ns) foram atualizados com o novo sistema de profissões.")
    else:
        print("\n✅ Operação concluída! Nenhum personagem precisou ser atualizado.")

except Exception as e:
    print(f"\n❌ Ocorreu um erro durante a atualização: {e}")

print("--- Script finalizado ---")