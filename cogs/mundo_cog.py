# cogs/mundo_cog.py
import discord
import random
import asyncio
from discord import app_commands
from discord.ext import commands

from firebase_config import db
from data.monstros_library import MONSTROS
from data.habilidades_library import HABILIDADES
from data.classes_data import CLASSES_DATA
from game.stat_calculator import calcular_stats_completos
from game.motor_combate import processar_acao_jogador, processar_turno_monstro

# --- FUNÇÃO DA BARRA DE STATUS (CORRIGIDA PARA 10 BLOCOS) ---
# O valor padrão de 'tamanho' agora está corrigido para 10.
def criar_barra_status(atual: int, maximo: int, cor_cheia: str, tamanho: int = 10) -> str:
    """Cria uma barra de status de texto usando blocos, baseada em porcentagem."""
    if maximo <= 0: maximo = 1
    atual = max(0, atual)
    percentual = atual / maximo
    blocos_cheios = round(percentual * tamanho)
    blocos_vazios = tamanho - blocos_cheios
    cor_vazia = '▬'
    return f"`[{cor_cheia * blocos_cheios}{cor_vazia * blocos_vazios}]`"

class BattleView(discord.ui.View):
    # (A classe BattleView continua a mesma, as correções são feitas antes de ela ser chamada)
    def __init__(self, author: discord.User, jogador_data: dict, monstro_data: dict):
        super().__init__(timeout=300)
        self.author = author
        self.jogador = jogador_data
        self.monstro = monstro_data
        self.log_batalha = "Batalha iniciada! É a sua vez."
        self.add_skill_buttons()
    
    def add_skill_buttons(self):
        """Cria os botões de ação para todas as habilidades, desativando as passivas."""
        self.clear_items()
        
        for skill_id in self.jogador['habilidades_equipadas']:
            skill_info = HABILIDADES.get(skill_id)
            if skill_info:
                # 1. Verifica se a habilidade é passiva
                is_passive = skill_info.get('tipo') == 'PASSIVA'
                
                # 2. Define o estilo do botão para dar feedback visual (cinza para passivas)
                button_style = discord.ButtonStyle.secondary if is_passive else discord.ButtonStyle.primary

                # 3. Cria o botão, desativando-o se for passivo
                button = discord.ui.Button(
                    label=skill_info['nome'],
                    style=button_style,
                    custom_id=skill_id,
                    emoji=skill_info.get('emoji'),
                    disabled=is_passive # O ponto chave da mudança!
                )
                
                # Apenas habilidades ativas precisam de uma função de callback
                if not is_passive:
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
        embed = discord.Embed(title="⚔️ BATALHA EM ANDAMENTO ⚔️", color=discord.Color.dark_orange())
        
        if turno_de == 'jogador':
            embed.set_image(url=self.jogador['imagem_url'])
            embed.set_author(name=f"Seu Turno, {self.author.display_name}!", icon_url=self.author.display_avatar.url)
        elif turno_de == 'monstro':
            embed.set_image(url=self.monstro['imagem_url'])
            embed.set_author(name=f"Turno de: {self.monstro['nome']}", icon_url=self.monstro['imagem_url'])

        # As chamadas agora usam o tamanho padrão correto (10)
        hp_bar_p = criar_barra_status(self.jogador['vida_atual'], self.jogador['stats']['VIDA_MAXIMA'], '🟥')
        mp_bar_p = criar_barra_status(self.jogador['mana_atual'], self.jogador['stats']['MANA_MAXIMA'], '🟦')
        jogador_stats_str = (
            f"**HP:** `{self.jogador['vida_atual']}/{self.jogador['stats']['VIDA_MAXIMA']}`\n{hp_bar_p}\n\n"
            f"**MP:** `{self.jogador['mana_atual']}/{self.jogador['stats']['MANA_MAXIMA']}`\n{mp_bar_p}"
        )
        embed.add_field(name=f"VOCÊ ({self.jogador['classe']})", value=jogador_stats_str, inline=True)

        vida_monstro_atual = max(0, self.monstro['vida_atual'])
        hp_bar_m = criar_barra_status(vida_monstro_atual, self.monstro['stats']['VIDA_MAXIMA'], '🟥')
        monstro_stats_str = (
            f"**HP:** `{vida_monstro_atual}/{self.monstro['stats']['VIDA_MAXIMA']}`\n{hp_bar_m}"
        )
        embed.add_field(name=f"{self.monstro['emoji']} {self.monstro['nome']}", value=monstro_stats_str, inline=True)

        embed.add_field(name="Log de Batalha", value=f">>> {self.log_batalha}", inline=False)
        return embed

    # (O resto da classe BattleView não precisa de alterações)
    # ...
    async def on_skill_use(self, interaction: discord.Interaction):
        for child in self.children: child.disabled = True
        skill_id = interaction.data['custom_id']
        resultado_jogador = processar_acao_jogador(self.jogador, self.monstro, skill_id)
        self.log_batalha = resultado_jogador['log']
        embed = self.create_battle_embed(turno_de='jogador')
        await interaction.response.edit_message(embed=embed, view=self)
        if self.monstro['vida_atual'] <= 0:
            await self.vitoria(interaction)
            return
        self.log_batalha += f"\nO {self.monstro['nome']} está preparando uma ação..."
        embed = self.create_battle_embed(turno_de='monstro')
        await interaction.edit_original_response(embed=embed, view=self)
        await asyncio.sleep(3)
        resultado_monstro = processar_turno_monstro(self.monstro, self.jogador)
        self.log_batalha = f"{resultado_jogador['log']}\n{resultado_monstro['log']}"
        if self.jogador['vida_atual'] <= 0:
            await self.derrota(interaction)
            return
        self.add_skill_buttons()
        embed = self.create_battle_embed(turno_de='jogador')
        await interaction.edit_original_response(embed=embed, view=self)

    async def on_backpack_use(self, interaction: discord.Interaction):
        await interaction.response.send_message("O uso de itens em batalha será implementado em breve!", ephemeral=True)

    async def vitoria(self, interaction: discord.Interaction):
        for child in self.children: child.disabled = True
        xp_ganho = self.monstro.get('xp_recompensa', 0)
        if xp_ganho > 0:
            from game.leveling_system import grant_xp
            grant_xp(user_id=str(interaction.user.id), amount=xp_ganho)
        embed = self.create_battle_embed(turno_de='jogador')
        embed.title = "🎉 VITÓRIA! 🎉"
        embed.color = discord.Color.gold()
        self.log_batalha += f"\nVocê derrotou o {self.monstro['nome']} e ganhou `{xp_ganho}` de XP!"
        embed.set_field_at(2, name="Log de Batalha", value=f">>> {self.log_batalha}", inline=False)
        await interaction.edit_original_response(embed=embed, view=self)
        self.stop()
    
    async def derrota(self, interaction: discord.Interaction):
        for child in self.children: child.disabled = True
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
        char_ref = db.collection('characters').document(user_id_str)
        char_doc = char_ref.get()
        if not char_doc.exists:
            await interaction.followup.send("Você precisa criar um personagem com `/perfil` primeiro!")
            return
        char_data = char_doc.to_dict()

        # Busca de itens e cálculo de status...
        equipped_items_data = []
        inventory_snapshot = db.collection('characters').document(user_id_str).collection('inventario').where('equipado', '==', True).stream()
        for item_ref in inventory_snapshot:
            instance_doc = db.collection('items').document(item_ref.id).get()
            if instance_doc.exists:
                equipped_items_data.append({"instance_data": instance_doc.to_dict()})
        stats_completos = calcular_stats_completos(char_data, equipped_items_data)

        # --- CORREÇÃO DA VIDA/MANA ATUAL AQUI ---
        # 1. Pega os valores máximos calculados
        vida_maxima_final = stats_completos.get('VIDA_MAXIMA', 100)
        mana_maxima_final = stats_completos.get('MANA_MAXIMA', 100)
        
        # 2. Garante que os valores atuais não ultrapassem os máximos
        vida_atual_corrigida = min(char_data.get('vida_atual', vida_maxima_final), vida_maxima_final)
        mana_atual_corrigida = min(char_data.get('mana_atual', mana_maxima_final), mana_maxima_final)

        # 3. Prepara o dicionário de dados do jogador para a batalha com os valores corrigidos
        jogador_para_batalha = {
            "stats": stats_completos,
            "vida_atual": vida_maxima_final,
            "mana_atual": mana_maxima_final,
            "habilidades_equipadas": char_data.get('habilidades_equipadas', []),
            "classe": char_data.get('classe'),
            "imagem_url": CLASSES_DATA.get(char_data.get('classe'), {}).get('image_url')
        }

        # (O resto da função para preparar o monstro e iniciar a batalha continua o mesmo)
        monster_id = random.choice(list(MONSTROS.keys()))
        monstro_template = MONSTROS.get(monster_id)
        if not monstro_template:
            await interaction.followup.send(f"Erro ao encontrar dados do monstro: {monster_id}")
            return
        monstro_para_batalha = {
            "id": monster_id, "nome": monstro_template['nome'], "emoji": monstro_template['emoji'],
            "stats": monstro_template['stats'], "vida_atual": monstro_template['stats']['VIDA_MAXIMA'],
            "xp_recompensa": monstro_template.get('xp_recompensa', 0),
            "imagem_url": monstro_template.get('imagem_url')
        }
        
        view = BattleView(author=interaction.user, jogador_data=jogador_para_batalha, monstro_data=monstro_para_batalha)
        embed = view.create_battle_embed(turno_de='jogador')
        await interaction.followup.send(embed=embed, view=view)

async def setup(bot: commands.Bot):
    await bot.add_cog(MundoCog(bot))