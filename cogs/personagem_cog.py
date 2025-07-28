# cogs/personagem_cog.py
import discord
from discord import app_commands
from discord.ext import commands

from firebase_config import db
from data.classes_data import CLASSES_DATA
from data.game_config import calcular_xp_para_nivel
from data.habilidades_library import HABILIDADES
from ui.views import ClasseSelectionView, PerfilView
from utils.storage_helper import get_signed_url

# Importa nosso novo calculador de status
from game.stat_calculator import calcular_stats_completos

class PersonagemCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="perfil", description="Veja seu perfil ou crie um novo personagem.")
    async def perfil(self, interaction: discord.Interaction):
        # Usamos defer() no início pois a busca de dados pode demorar um pouco
        await interaction.response.defer(ephemeral=True)
        
        user_id_str = str(interaction.user.id)
        player_ref = db.collection('players').document(user_id_str)
        player_doc = player_ref.get()
        if not player_doc.exists:
            await interaction.followup.send("Você ainda não está registrado. Use `/registrar` primeiro!", ephemeral=True)
            return

        char_ref = db.collection('characters').document(user_id_str)
        char_doc = char_ref.get()
        if char_doc.exists:
            # --- BLOCO DE CÓDIGO TOTALMENTE ATUALIZADO ---

            # 1. Busca os dados brutos do Firebase
            player_data = player_doc.to_dict()
            char_data = char_doc.to_dict()

            # 2. Busca todos os itens equipados pelo jogador
            equipped_items_data = []
            inventory_snapshot = db.collection('characters').document(user_id_str).collection('inventario').where('equipado', '==', True).stream()
            for item_ref in inventory_snapshot:
                instance_doc = db.collection('items').document(item_ref.id).get()
                if instance_doc.exists:
                    equipped_items_data.append({"instance_data": instance_doc.to_dict()})
            
            # --- MUDANÇA NO RODAPÉ DO EMBED ---
            # Busca o nome da cidade a partir do ID salvo
            cidade_atual_nome = "Lugar Desconhecido"
            if cidade_id := char_data.get('localizacao_id'):
                if guild := self.bot.get_guild(int(cidade_id)):
                    cidade_atual_nome = guild.name
            
            
            # 3. Chama o calculador para obter os status finais
            stats_finais = calcular_stats_completos(char_data, equipped_items_data)

            # 4. Monta o novo Embed com o layout redesenhado
            # --- EMBED REDESENHADO COM A CORREÇÃO DE LÓGICA ---
            embed = discord.Embed(
                title=f"Perfil de {player_data.get('nick', 'Aventureiro')}",
                description=f"*{char_data.get('classe', 'Desconhecido')} explorando o mundo.*",
                color=interaction.user.color
            )
            classe_info = CLASSES_DATA.get(char_data.get('classe'))
            if classe_info:
                image_path = classe_info.get('profile_image_path')
                if image_path:
                    public_url = get_signed_url(image_path)
                    embed.set_thumbnail(url=public_url)

            # Bloco de Atributos de Combate (agora sem ler/escrever no DB)
            vida_maxima_final = stats_finais.get('VIDA_MAXIMA', 100)
            mana_maxima_final = stats_finais.get('MANA_MAXIMA', 100)
            
            # Os valores atuais são sempre considerados iguais aos máximos
            vida_atual = vida_maxima_final
            mana_atual = mana_maxima_final
            
            stats_str = (
                f"❤️ **Vida:** `{vida_atual:,} / {vida_maxima_final:,}`\n"
                f"💧 **Mana:** `{mana_atual:,} / {mana_maxima_final:,}`\n"
                f"⚔️ **Dano Físico:** `{stats_finais.get('DANO', 0):,}`\n"
            )
            if stats_finais.get('DANO_MAGICO', 0) > 0:
                stats_str += f"✨ **Dano Mágico:** `{stats_finais.get('DANO_MAGICO', 0):,}`\n"
            stats_str += f"🛡️ **Armadura:** `{stats_finais.get('ARMADURA', 0):,}`"
            embed.add_field(name="Atributos de Combate", value=stats_str, inline=True)
            
            # Bloco de Riquezas
            riquezas_str = (
                f"🪙 **Moedas:** {char_data.get('moedas', 0):,}\n"
                f"🏦 **Banco:** {char_data.get('banco', 0):,}\n"
                f"💎 **Diamantes:** {char_data.get('diamantes', 0):,}"
            )
            embed.add_field(name="Riquezas", value=riquezas_str, inline=True)

            # Bloco de Progressão (Nível + XP)
            nivel_atual = char_data.get('nivel', 1)
            xp_atual = char_data.get('xp', 0)
            xp_necessario = calcular_xp_para_nivel(nivel_atual)
            percent_xp = (xp_atual / xp_necessario * 100) if xp_necessario > 0 else 100
            barra_xp = '█' * int(percent_xp / 10) + '░' * (10 - int(percent_xp / 10))
            xp_texto = f"{barra_xp} `[{xp_atual:,}/{xp_necessario:,}]` ({percent_xp:.1f}%)"
            embed.add_field(name=f"🌟 Nível {nivel_atual}", value=xp_texto, inline=False)

            # Bloco de Habilidades (Corrigido para mostrar nomes)
            habilidades_ids = char_data.get('habilidades_equipadas', [])
            habilidades_nomes = [HABILIDADES.get(hab_id, {}).get('nome', f"`{hab_id}`") for hab_id in habilidades_ids]
            habilidades_str = ">>> " + "\n".join(f"• {hab}" for hab in habilidades_nomes) if habilidades_nomes else "Nenhuma habilidade equipada."
            embed.add_field(name="Habilidades Equipadas", value=habilidades_str, inline=False)
            
            game_id = player_data.get('game_id', 'N/A')
            # Atualiza o rodapé para incluir a localização
            embed.set_footer(text=f"Localização: {cidade_atual_nome} | ID de Jogo: {game_id}")

            view = PerfilView()
            # Usamos followup.send pois a interação foi "deferida" no início
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)
            
            # --- FIM DO BLOCO ATUALIZADO ---
        else:
            # Lógica para criar personagem continua a mesma
            view = ClasseSelectionView(user=interaction.user)
            initial_embed = view.create_embed()
            await interaction.followup.send( # followup.send aqui também
                "Você ainda não tem um personagem. Vamos criar um agora! Escolha sua classe abaixo:",
                embed=initial_embed, view=view, ephemeral=True
            )

async def setup(bot: commands.Cog):
    await bot.add_cog(PersonagemCog(bot))