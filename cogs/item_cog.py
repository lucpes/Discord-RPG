# cogs/item_cog.py
import discord
import random
from discord import app_commands
from discord.ext import commands
from firebase_admin import firestore

from firebase_config import db
from data.stats_library import format_stat

RARITY_COLORS = {
    "COMUM": discord.Color.light_grey(), "INCOMUM": discord.Color.green(),
    "RARO": discord.Color.blue(), "EPICO": discord.Color.purple(),
    "LENDARIO": discord.Color.gold()
}

@firestore.transactional
def get_and_increment_item_id(transaction):
    counter_ref = db.collection('game_counters').document('item_id')
    snapshot = counter_ref.get(transaction=transaction)
    if not snapshot.exists: new_id = 1; transaction.set(counter_ref, {'last_id': new_id})
    else: last_id = snapshot.to_dict().get('last_id', 0); new_id = last_id + 1; transaction.update(counter_ref, {'last_id': new_id})
    return new_id

class ItemCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    # --- COMANDO /EQUIPAR ATUALIZADO ---
    @app_commands.command(name="equipar", description="Equipa um item do seu inventário.")
    @app_commands.describe(item_id="O ID do item que você deseja equipar.")
    async def equipar(self, interaction: discord.Interaction, item_id: int):
        await interaction.response.defer(ephemeral=True)
        user_id = str(interaction.user.id)
        char_ref = db.collection('characters').document(user_id)
        item_ref = db.collection('items').document(str(item_id))
        item_doc = item_ref.get()

        if not item_doc.exists or item_doc.to_dict().get('owner_id') != user_id:
            await interaction.followup.send("❌ Item não encontrado ou não pertence a você.", ephemeral=True)
            return
        
        item_data = item_doc.to_dict()
        template_ref = db.collection('item_templates').document(item_data['template_id'])
        template_doc = template_ref.get()
        template_data = template_doc.to_dict()
        
        char_doc = char_ref.get()
        char_data = char_doc.to_dict()

        # Verificação de Classe (já existente)
        item_class_req = template_data.get('classe')
        if item_class_req:
            player_class = char_data.get('classe')
            if isinstance(item_class_req, str): item_class_req = [item_class_req]
            
            if player_class not in item_class_req:
                allowed_classes_str = ", ".join(item_class_req)
                await interaction.followup.send(
                    f"❌ **Você não pode equipar este item!**\n"
                    f"O item **{template_data['nome']}** é restrito para: `{allowed_classes_str}`.\n"
                    f"Sua classe é **{player_class}**."
                )
                return
        
        # --- NOVA LÓGICA: VERIFICAÇÃO DE NÍVEL REQUERIDO ---
        requisito = template_data.get('nivel_requerido')
        if requisito:
            # Caso 1: Requisito de Profissão (ex: { "profissao": "minerador", "nivel": 5 })
            if isinstance(requisito, dict):
                req_profissao = requisito['profissao']
                req_nivel = requisito['nivel']
                
                # Pega o nível da profissão do jogador, com 1 como padrão se não existir.
                nivel_jogador_profissao = char_data.get('profissoes', {}).get(req_profissao, {}).get('nivel', 1)
                
                if nivel_jogador_profissao < req_nivel:
                    return await interaction.followup.send(
                        f"❌ Você não pode equipar **{template_data['nome']}**!\n"
                        f"Requer **{req_profissao.capitalize()} Nível {req_nivel}**, mas o seu é {nivel_jogador_profissao}.",
                        ephemeral=True
                    )
            
            # Caso 2: Requisito de Nível de Personagem (ex: 10)
            elif isinstance(requisito, int):
                nivel_jogador = char_data.get('nivel', 1)
                if nivel_jogador < requisito:
                    return await interaction.followup.send(
                        f"❌ Você não pode equipar **{template_data['nome']}**!\n"
                        f"Requer **Nível de Personagem {requisito}**, mas o seu é {nivel_jogador}.",
                        ephemeral=True
                    )
        # --- FIM DA NOVA LÓGICA ---

        item_slot = template_data.get('slot')
        if item_slot:
            inventory_snapshot = char_ref.collection('inventario_equipamentos').where('equipado', '==', True).stream()
            
            for old_item_doc_ref in inventory_snapshot:
                old_item_doc = db.collection('items').document(old_item_doc_ref.id).get()
                if not old_item_doc.exists: continue
                
                old_template_doc = db.collection('item_templates').document(old_item_doc.to_dict()['template_id']).get()
                if not old_template_doc.exists: continue
                
                if old_template_doc.to_dict().get('slot') == item_slot:
                    old_item_doc_ref.reference.update({'equipado': False})
                    # Use um followup separado para a mensagem de desequipar
                    await interaction.followup.send(f"ℹ️ Item '{old_template_doc.to_dict()['nome']}' foi desequipado automaticamente.", ephemeral=True)
                    break 

        inventory_ref = char_ref.collection('inventario_equipamentos').document(str(item_id))
        inventory_ref.update({'equipado': True})

        await interaction.followup.send(f"✅ Você equipou **{template_data['nome']}** com sucesso!", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(ItemCog(bot))