# update_profissoes.py
# Este é um script temporário para adicionar o mapa de profissões a todos os personagens existentes.

from firebase_config import db
from data.profissoes_library import PROFISSOES # Importa nossa lista de profissões

print("--- Iniciando script de atualização de profissões ---")

try:
    chars_ref = db.collection('characters')
    all_characters = chars_ref.stream()

    batch = db.batch()
    updated_count = 0
    total_processed = 0

    # Itera sobre cada personagem
    for char_doc in all_characters:
        total_processed += 1
        char_data = char_doc.to_dict()
        
        # Pega as profissões que o jogador já tem, ou cria um dicionário vazio se não tiver nenhuma.
        profissoes_jogador = char_data.get('profissoes', {})
        
        # --- LÓGICA CORRIGIDA AQUI ---
        # Verifica se alguma profissão da biblioteca está a faltar no jogador
        profissoes_faltando = False
        for prof_id in PROFISSOES.keys():
            if prof_id not in profissoes_jogador:
                # Se uma profissão está a faltar, adiciona-a com os valores padrão
                print(f"  -> Adicionando profissão '{prof_id}' para o jogador {char_doc.id}...")
                profissoes_jogador[prof_id] = {"nivel": 1, "xp": 0}
                profissoes_faltando = True

        # Se encontrámos alguma profissão em falta, preparamos a atualização
        if profissoes_faltando:
            print(f"Atualizando personagem ID: {char_doc.id} com novas profissões.")
            char_ref_to_update = chars_ref.document(char_doc.id)
            batch.update(char_ref_to_update, {'profissoes': profissoes_jogador})
            updated_count += 1
        else:
            print(f"Personagem ID: {char_doc.id} já tem todas as profissões. Ignorando.")

    # Executa todas as atualizações no Firebase
    if updated_count > 0:
        batch.commit()
        print(f"\n✅ Operação concluída! {updated_count}/{total_processed} personagem(ns) foram atualizados com as novas profissões.")
    else:
        print(f"\n✅ Operação concluída! Nenhum personagem precisou ser atualizado. ({total_processed} processados)")

except Exception as e:
    print(f"\n❌ Ocorreu um erro durante a atualização: {e}")

print("--- Script finalizado ---")