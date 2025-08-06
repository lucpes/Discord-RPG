# cogs/craft_cog.py
import discord
from discord import app_commands
from discord.ext import commands
from firebase_config import db
from ui.crafting_views import CraftingView

class CraftCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # --- LÓGICA DE CACHE ADICIONADA AQUI ---
        # Carrega todos os templates de itens do Firebase para a memória
        self.item_templates_cache = {}
        try:
            templates_stream = db.collection('item_templates').stream()
            for template in templates_stream:
                self.item_templates_cache[template.id] = template.to_dict()
            print(f"✅ {len(self.item_templates_cache)} templates de itens carregados no cache.")
        except Exception as e:
            print(f"❌ ERRO ao carregar templates de itens: {e}")

    @app_commands.command(name="craft", description="Abre a interface de criação de itens.")
    async def craft(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        user_id_str = str(interaction.user.id)

        char_ref = db.collection('characters').document(user_id_str)
        char_doc = char_ref.get()
        cidade_ref = db.collection('cidades').document(str(interaction.guild.id))
        cidade_doc = cidade_ref.get()

        if not char_doc.exists or not cidade_doc.exists:
            await interaction.followup.send("Você precisa ter um personagem e estar em uma cidade para usar a Mesa de Trabalho.", ephemeral=True)
            return

        stackable_inventory = {item.id: item.to_dict().get('quantidade', 0) for item in char_ref.collection('inventario_empilhavel').stream()}

        # --- ALTERAÇÃO AQUI ---
        # Passa o cache de itens para a View
        view = CraftingView(
            author=interaction.user,
            char_data=char_doc.to_dict(),
            cidade_data=cidade_doc.to_dict(),
            stackable_inventory=stackable_inventory,
            item_templates_cache=self.item_templates_cache # Passa o cache
        )
        embed = view.create_embed()
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(CraftCog(bot))