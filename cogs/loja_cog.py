# cogs/loja_cog.py
import discord
from discord import app_commands
from discord.ext import commands
from firebase_config import db
from ui.loja_views import LojaView # Importa nossa nova View

class LojaCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.item_templates_cache = {}
        try:
            templates_stream = db.collection('item_templates').stream()
            for template in templates_stream:
                self.item_templates_cache[template.id] = template.to_dict()
        except Exception as e:
            print(f"❌ ERRO ao carregar templates de itens na Loja: {e}")

    @app_commands.command(name="loja", description="Acesse a loja da cidade para comprar itens.")
    async def loja(self, interaction: discord.Interaction):
        if interaction.guild is None:
            return await interaction.response.send_message("❌ A Loja só pode ser acessada dentro de uma cidade.", ephemeral=True)

        await interaction.response.defer(ephemeral=True)
        user_id_str = str(interaction.user.id)
        cidade_atual_id = str(interaction.guild.id)

        char_ref = db.collection('characters').document(user_id_str)
        char_doc = char_ref.get()
        cidade_ref = db.collection('cidades').document(cidade_atual_id)
        cidade_doc = cidade_ref.get()
        
        if not cidade_doc.exists:
            await interaction.followup.send(f"A cidade de **{interaction.guild.name}** ainda não foi fundada.", ephemeral=True)
            return
            
        # 4. Se tudo estiver certo, verifica o nível da Loja
        cidade_data = cidade_doc.to_dict()
        if cidade_data.get('construcoes', {}).get('LOJA', {}).get('nivel', 0) == 0:
            return await interaction.followup.send("🏪 A Loja de Utilidades ainda não foi construída nesta cidade!", ephemeral=True)

        # Se todas as verificações passaram, abre a interface da loja
        view = LojaView(
            author=interaction.user,
            char_data=char_doc.to_dict(),
            cidade_data=cidade_doc.to_dict(),
            item_templates_cache=self.item_templates_cache
        )
        embed = view.create_embed()
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(LojaCog(bot))