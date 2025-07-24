# cogs/mundo_cog.py
import discord
import random
from discord import app_commands
from discord.ext import commands
import asyncio

from firebase_config import db
from data.monstros_library import MONSTROS
from data.habilidades_library import HABILIDADES
from data.classes_data import CLASSES_DATA

# Importa nossas novas ferramentas de lógica
from game.stat_calculator import calcular_stats_completos
from game.motor_combate import processar_acao_jogador, processar_turno_monstro

def criar_barra_status(atual: int, maximo: int, cor_cheia: str = '█', cor_vazia: str = '░', tamanho: int = 10) -> str:
    if maximo <= 0: maximo = 1
    percentual = atual / maximo
    blocos_cheios = int(percentual * tamanho)
    blocos_vazios = tamanho - blocos_cheios
    return f"`[{cor_cheia * blocos_cheios}{cor_vazia * blocos_vazios}]`"

# --- BATTLEVIEW TOTALMENTE REFEITA ---
class BattleView(discord.ui.View):
    def __init__(self, author: discord.User, jogador_data: dict, monstro_data: dict):
        super().__init__(timeout=300)
        self.author = author
        self.jogador = jogador_data
        self.monstro = monstro_data
        self.log_batalha = "Batalha iniciada! É a sua vez."

        self.add_skill_buttons()
    
    def add_skill_buttons(self):
        # Limpa botões antigos antes de adicionar novos
        self.clear_items()
        for skill_id in self.jogador['habilidades_equipadas']:
            skill_info = HABILIDADES.get(skill_id)
            if skill_info:
                button = discord.ui.Button(label=skill_info['nome'], style=discord.ButtonStyle.primary, custom_id=skill_id, emoji=skill_info.get('emoji'))
                button.callback = self.on_skill_use
                self.add_item(button)
        backpack_button = discord.ui.Button(label="Mochila", style=discord.ButtonStyle.secondary, emoji="🎒", custom_id="backpack")
        backpack_button.callback = self.on_backpack_use
        self.add_item(backpack_button)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("Não é a sua batalha!", ephemeral=True)
            return False
        return True

    def create_battle_embed(self, turno_de: str) -> discord.Embed:
        """Cria o embed com base no turno atual."""
        embed = discord.Embed(title="⚔️ BATALHA EM ANDAMENTO ⚔️", color=discord.Color.dark_orange())
        
        # --- MUDANÇA NA IMAGEM DO TURNO ---
        # Usamos set_image para a foto principal, que é maior e mais impactante
        if turno_de == 'jogador':
            embed.set_image(url=self.jogador['imagem_url'])
            embed.set_author(name=f"Seu Turno, {self.author.display_name}!", icon_url=self.author.display_avatar.url)
        elif turno_de == 'monstro':
            embed.set_image(url=self.monstro['imagem_url'])
            embed.set_author(name=f"Turno de: {self.monstro['nome']}")

        hp_bar_p = criar_barra_status(self.jogador['vida_atual'], self.jogador['stats']['VIDA_MAXIMA'], '🟥')
        mp_bar_p = criar_barra_status(self.jogador['mana_atual'], self.jogador['stats']['MANA_MAXIMA'], '🟦')
        embed.add_field(name=f"VOCÊ ({self.jogador['classe']})", value=f"HP: {hp_bar_p} `{self.jogador['vida_atual']}/{self.jogador['stats']['VIDA_MAXIMA']}`\nMP: {mp_bar_p} `{self.jogador['mana_atual']}/{self.jogador['stats']['MANA_MAXIMA']}`", inline=True)

        hp_bar_m = criar_barra_status(self.monstro['vida_atual'], self.monstro['stats']['VIDA_MAXIMA'], '🟥')
        embed.add_field(name=f"{self.monstro['emoji']} {self.monstro['nome']}", value=f"HP: {hp_bar_m} `{self.monstro['vida_atual']}/{self.monstro['stats']['VIDA_MAXIMA']}`", inline=True)

        embed.add_field(name="Log de Batalha", value=f">>> {self.log_batalha}", inline=False)
        return embed

    async def on_skill_use(self, interaction: discord.Interaction):
        # Desativa os botões para o jogador não clicar de novo
        for child in self.children: child.disabled = True

        # --- TURNO DO JOGADOR ---
        skill_id = interaction.data['custom_id']
        resultado_jogador = processar_acao_jogador(self.jogador, self.monstro, skill_id)
        self.log_batalha = resultado_jogador['log']
        
        # Atualiza a tela IMEDIATAMENTE com o resultado da ação do jogador
        # A imagem ainda é a do jogador aqui
        embed = self.create_battle_embed(turno_de='jogador')
        await interaction.response.edit_message(embed=embed, view=self)

        # Verifica se o monstro foi derrotado
        if self.monstro['vida_atual'] <= 0:
            await self.vitoria(interaction)
            return

        # --- TRANSIÇÃO PARA O TURNO DO MONSTRO ---
        self.log_batalha += f"\nO {self.monstro['nome']} está preparando uma ação..."
        embed = self.create_battle_embed(turno_de='monstro') # Agora a imagem é a do monstro
        await interaction.edit_original_response(embed=embed, view=self)

        await asyncio.sleep(3) # A pausa de 3 segundos!

        # --- TURNO DO MONSTRO ---
        resultado_monstro = processar_turno_monstro(self.monstro, self.jogador)
        self.log_batalha = f"{resultado_jogador['log']}\n{resultado_monstro['log']}"

        # Verifica se o jogador foi derrotado
        if self.jogador['vida_atual'] <= 0:
            await self.derrota(interaction)
            return

        # Prepara para o próximo turno do jogador (reativa os botões)
        self.add_skill_buttons()
        embed = self.create_battle_embed(turno_de='jogador')
        await interaction.edit_original_response(embed=embed, view=self)

    async def on_backpack_use(self, interaction: discord.Interaction):
        await interaction.response.send_message("O uso de itens em batalha será implementado em breve!", ephemeral=True)

    async def vitoria(self, interaction: discord.Interaction):
        """Processa o fim da batalha em caso de vitória."""
        for child in self.children: child.disabled = True
        
        xp_ganho = self.monstro.get('xp_recompensa', 0)
        if xp_ganho > 0:
            from game.leveling_system import grant_xp
            grant_xp(user_id=str(interaction.user.id), amount=xp_ganho)
        
        # --- CORREÇÃO AQUI ---
        # Adicionamos o argumento 'turno_de'. Na tela de vitória, a imagem do jogador faz sentido.
        embed = self.create_battle_embed(turno_de='jogador')
        embed.title = "🎉 VITÓRIA! 🎉"
        embed.color = discord.Color.gold()
        self.log_batalha += f"\nVocê derrotou o {self.monstro['nome']} e ganhou `{xp_ganho}` de XP!"
        embed.set_field_at(2, name="Log de Batalha", value=f">>> {self.log_batalha}", inline=False)
        
        # Usamos edit_original_response para editar a mensagem de batalha existente
        await interaction.edit_original_response(embed=embed, view=self)
        self.stop()
    
    async def derrota(self, interaction: discord.Interaction):
        """Processa o fim da batalha em caso de derrota."""
        for child in self.children: child.disabled = True
        
        # --- CORREÇÃO AQUI ---
        # Na tela de derrota, mostrar a imagem do monstro vitorioso dá um toque final.
        embed = self.create_battle_embed(turno_de='monstro')
        embed.title = "☠️ VOCÊ FOI DERROTADO ☠️"
        embed.color = discord.Color.darker_grey()
        
        await interaction.edit_original_response(embed=embed, view=self)
        self.stop()


class MundoCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="explorar", description="Explore a área em busca de monstros.")
    async def explorar(self, interaction: discord.Interaction):
        await interaction.response.defer()
        user_id_str = str(interaction.user.id)

        # 1. Pega os dados do personagem
        char_ref = db.collection('characters').document(user_id_str)
        char_doc = char_ref.get()
        if not char_doc.exists:
            await interaction.followup.send("Você precisa criar um personagem com `/perfil` primeiro!")
            return
        char_data = char_doc.to_dict()

        # 2. Calcula os status completos do jogador
        # (Em uma implementação real, os itens equipados seriam buscados aqui)
        stats_completos = calcular_stats_completos(char_data, [])

        # 3. Prepara o dicionário de dados do jogador para a batalha
        jogador_para_batalha = {
            "stats": stats_completos,
            "vida_atual": char_data.get('vida_atual', stats_completos.get('VIDA_MAXIMA', 100)),
            "mana_atual": char_data.get('mana_atual', stats_completos.get('MANA_MAXIMA', 100)),
            "habilidades_equipadas": char_data.get('habilidades_equipadas', []),
            "classe": char_data.get('classe'),
            "imagem_url": CLASSES_DATA.get(char_data.get('classe'), {}).get('image_url')
        }

        # 4. Prepara o dicionário de dados do monstro
        monster_id = random.choice(list(MONSTROS.keys()))
        monstro_template = MONSTROS[monster_id]
        monstro_para_batalha = {
            "id": monster_id,
            "nome": monstro_template['nome'],
            "emoji": monstro_template['emoji'],
            "imagem_url": monstro_template.get('imagem_url'),
            "stats": monstro_template['stats'],
            "vida_atual": monstro_template['stats']['VIDA_MAXIMA'],
            "xp_recompensa": monstro_template.get('xp_recompensa', 0)
        }

        # 5. Inicia a batalha
        view = BattleView(author=interaction.user, jogador_data=jogador_para_batalha, monstro_data=monstro_para_batalha)
        embed = view.create_battle_embed(turno_de='jogador')
        
        await interaction.followup.send(embed=embed, view=view)

async def setup(bot: commands.Cog):
    await bot.add_cog(MundoCog(bot))