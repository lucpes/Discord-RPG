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

    # --- COMANDO /CRIARITEM MODIFICADO ---
    @app_commands.command(name="criaritem", description="[Admin] Cria uma nova instância de item a partir de um template.")
    @app_commands.describe(template_id="O ID do template do item (ex: espada_ferro_comum)", alvo="O jogador que receberá o item.")
    @commands.is_owner()
    async def criar_item(self, interaction: discord.Interaction, template_id: str, alvo: discord.Member):
        await interaction.response.defer(ephemeral=True)

        # Busca o template (sem alterações aqui)
        template_ref = db.collection('item_templates').document(template_id)
        template_doc = template_ref.get()
        if not template_doc.exists:
            await interaction.followup.send(f"❌ Template com ID `{template_id}` não encontrado.")
            return
        template_data = template_doc.to_dict()

        # O BLOCO DE VERIFICAÇÃO DE CLASSE FOI REMOVIDO DAQUI.
        # Agora o item sempre será criado, não importa a classe do alvo.

        # "Rola" os status do item (sem alterações aqui)
        stats_gerados = {}
        for stat_id, value_range in template_data.get('stats_base', {}).items():
            rolled_value = random.randint(value_range['min'], value_range['max'])
            stats_gerados[stat_id] = rolled_value

        # Obter um novo ItemID único (sem alterações aqui)
        transaction = db.transaction()
        item_id = get_and_increment_item_id(transaction)

        # Criar a instância e a referência no inventário (sem alterações aqui)
        item_ref = db.collection('items').document(str(item_id))
        item_data = {"template_id": template_id, "owner_id": str(alvo.id), "stats_gerados": stats_gerados, "encantamentos_aplicados": []}
        item_ref.set(item_data)
        inventory_ref = db.collection('characters').document(str(alvo.id)).collection('inventario').document(str(item_id))
        inventory_ref.set({'equipado': False})

        # Criar um embed de confirmação (sem alterações aqui)
        rarity = template_data.get("raridade", "COMUM").upper()
        embed_color = RARITY_COLORS.get(rarity, discord.Color.default())
        embed = discord.Embed(
            title="✨ Item Forjado com Sucesso! ✨",
            description=f"Um novo item foi criado e entregue para {alvo.mention}.",
            color=embed_color
        )
        embed.add_field(name="Nome do Item", value=f"**{template_data['nome']}** `[ID: {item_id}]`", inline=False)
        embed.add_field(name="Raridade", value=f"**{rarity.capitalize()}**", inline=False)
        stats_str = "\n".join([format_stat(stat, val) for stat, val in stats_gerados.items()]) or "Nenhum atributo base."
        embed.add_field(name="Atributos", value=stats_str, inline=False)
        embed.set_footer(text=f"Template base: {template_id}")
        await interaction.followup.send(embed=embed)
        try:
            await alvo.send(f"Parabéns! Você recebeu um novo item: **{template_data['nome']}** ({rarity.capitalize()}).")
        except discord.Forbidden:
            pass
    
    # --- NOVO COMANDO /EQUIPAR ---
    @app_commands.command(name="equipar", description="Equipa um item do seu inventário.")
    @app_commands.describe(item_id="O ID do item que você deseja equipar.")
    async def equipar(self, interaction: discord.Interaction, item_id: int):
        await interaction.response.defer(ephemeral=True)
        user_id = str(interaction.user.id)

        # 1. Verificar se o item existe e se pertence ao jogador
        item_ref = db.collection('items').document(str(item_id))
        item_doc = item_ref.get()

        if not item_doc.exists or item_doc.to_dict().get('owner_id') != user_id:
            await interaction.followup.send("❌ Item não encontrado ou não pertence a você.", ephemeral=True)
            return
        
        item_data = item_doc.to_dict()
        
        # 2. Buscar dados do template e do personagem para a verificação
        template_ref = db.collection('item_templates').document(item_data['template_id'])
        template_doc = template_ref.get()
        template_data = template_doc.to_dict()
        
        char_ref = db.collection('characters').document(user_id)
        char_doc = char_ref.get()
        char_data = char_doc.to_dict()

        # 3. ### A VERIFICAÇÃO DE CLASSE AGORA ACONTECE AQUI! ###
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

        # 4. Desequipar item antigo no mesmo slot (se houver)
        item_slot = template_data.get('slot')
        if item_slot:
            inventory_snapshot = db.collection('characters').document(user_id).collection('inventario').where('equipado', '==', True).stream()
            for old_item_ref in inventory_snapshot:
                old_item_doc = db.collection('items').document(old_item_ref.id).get()
                old_template_doc = db.collection('item_templates').document(old_item_doc.to_dict()['template_id']).get()
                if old_template_doc.to_dict().get('slot') == item_slot:
                    old_item_ref.reference.update({'equipado': False}) # Desequipa o item antigo
                    await interaction.followup.send(f"ℹ️ Item '{old_template_doc.to_dict()['nome']}' foi desequipado automaticamente.", ephemeral=True)

        # 5. Equipar o novo item
        inventory_ref = db.collection('characters').document(user_id).collection('inventario').document(str(item_id))
        inventory_ref.update({'equipado': True})

        await interaction.followup.send(f"✅ Você equipou **{template_data['nome']}** com sucesso!", ephemeral=True)

    @criar_item.error
    async def criar_item_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.errors.NotOwner):
            await interaction.response.send_message("❌ Apenas o dono do bot pode usar este comando.", ephemeral=True)
        else:
            await interaction.response.send_message(f"Ocorreu um erro inesperado: {error}", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(ItemCog(bot))