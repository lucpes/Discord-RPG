# cogs/stats_cog.py
import discord
from discord import app_commands
from discord.ext import commands
from firebase_config import db

# Importa as ferramentas corretas
from data.stats_library import STATS, STAT_CATEGORIES, format_stat # Importa a função format_stat
from utils.character_helpers import load_player_sheet
from game.stat_calculator import calcular_stats_completos

class StatsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="status", description="Exibe a ficha completa de status do seu personagem.")
    async def status(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        user_id_str = str(interaction.user.id)

        # Usa a função centralizada para carregar todos os dados do jogador
        sheet = load_player_sheet(user_id_str)
        if not sheet:
            await interaction.followup.send("❌ Você precisa ter um personagem para ver seus status. Use `/perfil`.", ephemeral=True)
            return

        char_data = sheet['char_data']
        equipped_items = sheet['equipped_items']

        # Calcula os status finais, já somando tudo
        stats_finais = calcular_stats_completos(char_data, equipped_items)

        embed = discord.Embed(
            title=f"Ficha de Status de {sheet['player_data'].get('nick')}",
            description="Estes são seus atributos totais, incluindo bônus de equipamentos e habilidades.",
            color=interaction.user.color
        )

        # Organiza os status com base nas categorias do seu stats_library.py
        stats_by_category = {category: [] for category in STAT_CATEGORIES}
        
        for stat_id, stat_info in STATS.items():
            if stat_id in stats_finais and 'category' in stat_info and stats_finais[stat_id] != 0:
                valor = stats_finais[stat_id]
                
                # --- CORREÇÃO APLICADA AQUI ---
                # Agora usa a função de formatação central do stats_library.py
                # que já formata corretamente como "25%" em vez de "25.0%"
                # A linha foi simplificada, pois format_stat já faz todo o trabalho.
                line = format_stat(stat_id, valor)
                
                stats_by_category[stat_info['category']].append(line)

        for category in STAT_CATEGORIES:
            if stats_by_category[category]:
                embed.add_field(
                    name=f"--- {category.capitalize()} ---",
                    value="\n".join(stats_by_category[category]),
                    inline=True
                )
        
        await interaction.followup.send(embed=embed, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(StatsCog(bot))