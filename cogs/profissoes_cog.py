# cogs/profissoes_cog.py
import discord
from discord import app_commands
from discord.ext import commands
from firebase_config import db
from ui.profissoes_views import ProfissoesView # Importa nossa nova View

class ProfissoesCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="profissoes", description="Veja o progresso das suas profissões.")
    async def profissoes(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        user_id_str = str(interaction.user.id)

        char_ref = db.collection('characters').document(user_id_str)
        char_doc = char_ref.get()

        if not char_doc.exists:
            await interaction.followup.send("❌ Você precisa ter um personagem para ver suas profissões. Use `/perfil`.", ephemeral=True)
            return

        view = ProfissoesView(author=interaction.user, char_data=char_doc.to_dict())
        embed = view.create_embed()
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(ProfissoesCog(bot))