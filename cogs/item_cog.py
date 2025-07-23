# cogs/item_cog.py
import discord
import random
from discord import app_commands
from discord.ext import commands
from firebase_admin import firestore

from firebase_config import db
from data.stats_library import format_stat

# Dicionário de cores para cada raridade
RARITY_COLORS = {
    "COMUM": discord.Color.light_grey(),
    "INCOMUM": discord.Color.green(),
    "RARO": discord.Color.blue(),
    "EPICO": discord.Color.purple(),
    "LENDARIO": discord.Color.gold()
}

@firestore.transactional
def get_and_increment_item_id(transaction):
    # (Esta função continua a mesma, sem alterações)
    counter_ref = db.collection('game_counters').document('item_id')
    snapshot = counter_ref.get(transaction=transaction)
    if not snapshot.exists:
        new_id = 1
        transaction.set(counter_ref, {'last_id': new_id})
    else:
        last_id = snapshot.to_dict().get('last_id', 0)
        new_id = last_id + 1
        transaction.update(counter_ref, {'last_id': new_id})
    return new_id

class ItemCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="criaritem", description="[Admin] Cria uma nova instância de item a partir de um template.")
    @app_commands.describe(template_id="O ID do template do item (ex: espada_ferro_comum)",
                           alvo="O jogador que receberá o item.")
    @commands.is_owner()
    async def criar_item(self, interaction: discord.Interaction, template_id: str, alvo: discord.Member):
        await interaction.response.defer(ephemeral=True)

        # 1. Buscar o template do item no Firebase
        template_ref = db.collection('item_templates').document(template_id)
        template_doc = template_ref.get()
        if not template_doc.exists:
            await interaction.followup.send(f"❌ Template com ID `{template_id}` não encontrado.")
            return
        template_data = template_doc.to_dict()

        # 2. ### NOVO: BUSCAR OS DADOS DO PERSONAGEM ALVO ###
        char_ref = db.collection('characters').document(str(alvo.id))
        char_doc = char_ref.get()
        if not char_doc.exists:
            await interaction.followup.send(f"❌ O jogador {alvo.mention} não possui um personagem criado.")
            return
        char_data = char_doc.to_dict()

        # 3. ### NOVO: VERIFICAR A RESTRIÇÃO DE CLASSE ###
        item_class_req = template_data.get('classe') # Pega a restrição de classe do item
        
        # A verificação só acontece se o campo 'classe' existir no template
        if item_class_req:
            player_class = char_data.get('classe')
            
            # Converte para lista para lidar com casos de string única ou lista de strings
            if isinstance(item_class_req, str):
                item_class_req = [item_class_req]

            if player_class not in item_class_req:
                allowed_classes_str = ", ".join(item_class_req)
                await interaction.followup.send(
                    f"❌ **Falha na Criação!**\n"
                    f"O item **{template_data['nome']}** só pode ser usado por: `{allowed_classes_str}`.\n"
                    f"O(A) jogador(a) {alvo.mention} é da classe **{player_class}**."
                )
                return # Interrompe a criação do item

        # 4. "Rolar" os status do item
        stats_gerados = {}
        for stat_id, value_range in template_data.get('stats_base', {}).items():
            rolled_value = random.randint(value_range['min'], value_range['max'])
            stats_gerados[stat_id] = rolled_value

        # 5. Obter um novo ItemID único
        transaction = db.transaction()
        item_id = get_and_increment_item_id(transaction)

        # 6. Criar a instância do item na coleção 'items'
        item_ref = db.collection('items').document(str(item_id))
        item_data = {"template_id": template_id, "owner_id": str(alvo.id), "stats_gerados": stats_gerados, "encantamentos_aplicados": []}
        item_ref.set(item_data)
        inventory_ref = db.collection('characters').document(str(alvo.id)).collection('inventario').document(str(item_id))
        inventory_ref.set({'equipado': False})

        # 7. Criar um embed de confirmação (agora com raridade e cor!)
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

    @criar_item.error
    async def criar_item_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        # (Esta função continua a mesma, sem alterações)
        if isinstance(error, app_commands.errors.NotOwner):
            await interaction.response.send_message("❌ Apenas o dono do bot pode usar este comando.", ephemeral=True)
        else:
            await interaction.response.send_message(f"Ocorreu um erro: {error}", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(ItemCog(bot))