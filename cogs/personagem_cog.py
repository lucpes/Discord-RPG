# cogs/personagem_cog.py
import discord
from discord import app_commands
from discord.ext import commands

from firebase_config import db
from data.classes_data import CLASSES_DATA # Importa os dados estáticos
from ui.views import ClasseSelectionView, PerfilView # Importa as Views de UI
from data.game_config import calcular_xp_para_nivel 
from ui.views import ClasseSelectionView, PerfilView

class PersonagemCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="perfil", description="Veja seu perfil ou crie um novo personagem.")
    async def perfil(self, interaction: discord.Interaction):
        # (Cole aqui o código do comando /perfil, sem alterações)
        user_id_str = str(interaction.user.id)
        player_ref = db.collection('players').document(user_id_str)
        player_doc = player_ref.get()
        if not player_doc.exists:
            await interaction.response.send_message("Você ainda não está registrado. Use `/registrar` primeiro!", ephemeral=True)
            return

        char_ref = db.collection('characters').document(user_id_str)
        char_doc = char_ref.get()
        if char_doc.exists:
            player_data = player_doc.to_dict()
            char_data = char_doc.to_dict()
            embed = discord.Embed(
                title=f"Perfil de {player_data.get('nick', 'Aventureiro')}",
                description=f"Um(a) {char_data.get('classe', 'Desconhecido')} de nível {char_data.get('nivel', 0)} explorando o mundo.",
                color=interaction.user.color
            )
            classe_info = CLASSES_DATA.get(char_data.get('classe'))
            if classe_info:
                embed.set_thumbnail(url=classe_info['image_url'])
            embed.add_field(name="Informações Básicas", value=f"**Classe:** {char_data.get('classe', 'N/A')}\n**Nível:** {char_data.get('nivel', 0)}\n**Guilda:** Sem guilda (em breve)", inline=True)
            embed.add_field(name="Riquezas", value=f"🪙 **Moedas:** {char_data.get('moedas', 0)}\n🏦 **Banco:** {char_data.get('banco', 0)}\n💎 **Diamantes:** {char_data.get('diamantes', 0)}", inline=True)
            
            # --- LÓGICA DA BARRA DE XP ADICIONADA AQUI ---
            
            # 1. Pega os dados de XP e Nível do Firebase
            xp_atual = char_data.get('xp', 0)
            nivel_atual = char_data.get('nivel', 1)
            
            # 2. Calcula o XP necessário para o próximo nível usando nossa função
            xp_necessario = calcular_xp_para_nivel(nivel_atual)
            
            # 3. Calcula a porcentagem, evitando divisão por zero
            percent_xp = (xp_atual / xp_necessario * 100) if xp_necessario > 0 else 100
            
            # 4. Cria a barra de progresso visual com 10 blocos
            total_blocos = 10
            blocos_preenchidos = int(percent_xp / 10)
            blocos_vazios = total_blocos - blocos_preenchidos
            barra_xp = '█' * blocos_preenchidos + '░' * blocos_vazios
            
            # 5. Formata o texto final do campo
            # Usamos {:,} para formatar números grandes com vírgulas (ex: 1,000)
            # Usamos {percent_xp:.1f} para mostrar o percentual com 1 casa decimal
            xp_texto = f"{barra_xp} `[{xp_atual:,}/{xp_necessario:,}]` ({percent_xp:.1f}%)"
            
            # Adiciona o campo ao embed
            embed.add_field(name="🌟 Progresso de Nível", value=xp_texto, inline=False)
            
            # --- FIM DA LÓGICA DA BARRA DE XP ---
            
            habilidades_list = char_data.get('habilidades_equipadas', ['Nenhuma habilidade equipada.'])
            embed.add_field(name="Habilidades Equipadas", value=">>> " + "\n".join(f"• {hab}" for hab in habilidades_list), inline=False)
            view = PerfilView()
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        else:
            view = ClasseSelectionView(user=interaction.user)
            initial_embed = view.create_embed()
            await interaction.response.send_message(
                "Você ainda não tem um personagem. Vamos criar um agora! Escolha sua classe abaixo:",
                embed=initial_embed,
                view=view,
                ephemeral=True
            )

async def setup(bot: commands.Bot):
    await bot.add_cog(PersonagemCog(bot))