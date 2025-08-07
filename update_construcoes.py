# update_construcoes.py
# Este é um script temporário para adicionar novas construções a todas as cidades existentes.

from firebase_config import db
from data.construcoes_library import CONSTRUCOES # Importa a lista mestre de construções

print("--- Iniciando script de atualização de construções das cidades ---")

try:
    cidades_ref = db.collection('cidades')
    all_cidades = cidades_ref.stream()

    batch = db.batch()
    updated_count = 0
    total_processed = 0

    # Pega a lista de todos os IDs de construções que devem existir
    master_building_ids = set(CONSTRUCOES.keys())

    # Itera sobre cada cidade
    for cidade_doc in all_cidades:
        total_processed += 1
        cidade_data = cidade_doc.to_dict()
        cidade_id = cidade_doc.id
        cidade_nome = cidade_data.get('nome', cidade_id)
        
        # Pega as construções que a cidade já tem
        construcoes_cidade = cidade_data.get('construcoes', {})
        
        construcoes_faltando = False
        # Compara a lista mestre com as construções da cidade
        for building_id in master_building_ids:
            if building_id not in construcoes_cidade:
                print(f"  -> Adicionando '{building_id}' à cidade '{cidade_nome}'...")
                # Adiciona a construção faltando com nível 0 (não construída)
                construcoes_cidade[building_id] = {"nivel": 0}
                construcoes_faltando = True

        # Se encontramos alguma construção faltando, preparamos a atualização
        if construcoes_faltando:
            print(f"Atualizando cidade: {cidade_nome} (ID: {cidade_id})")
            cidade_ref_to_update = cidades_ref.document(cidade_id)
            batch.update(cidade_ref_to_update, {'construcoes': construcoes_cidade})
            updated_count += 1
        else:
            print(f"Cidade '{cidade_nome}' (ID: {cidade_id}) já tem todas as construções. Ignorando.")

    # Executa todas as atualizações no Firebase
    if updated_count > 0:
        batch.commit()
        print(f"\n✅ Operação concluída! {updated_count}/{total_processed} cidade(s) foram atualizadas com as novas construções.")
    else:
        print(f"\n✅ Operação concluída! Nenhuma cidade precisou ser atualizada. ({total_processed} processadas)")

except Exception as e:
    print(f"\n❌ Ocorreu um erro durante a atualização: {e}")

print("--- Script finalizado ---")