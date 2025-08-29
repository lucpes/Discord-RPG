# cogs/mural_cog.py
import discord
from discord import app_commands
from discord.ext import commands
from firebase_config import db
from ui.mural_views import MuralView
from data.mural_library import CONTRATOS

class MuralCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="mural", description="Veja os contratos de caça disponíveis na cidade.")
    async def mural(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        user_id_str = str(interaction.user.id)
        
        char_ref = db.collection('characters').document(user_id_str)
        char_doc = char_ref.get()
        if not char_doc.exists:
            return await interaction.followup.send("Você precisa de um personagem para ver o mural.", ephemeral=True)
            
        char_data = char_doc.to_dict()
        nivel_jogador = char_data.get('nivel', 1)
        
        # Filtra os contratos que o jogador tem nível para ver
        contratos_disponiveis = [
            (cid, cdata) for cid, cdata in CONTRATOS.items()
            if cdata['nivel_requerido'] <= nivel_jogador
        ]
        
        view = MuralView(
            author=interaction.user, 
            bot=self.bot,
            char_data=char_data,
            contratos_disponiveis=contratos_disponiveis
        )
        embed = view.create_embed()
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(MuralCog(bot))