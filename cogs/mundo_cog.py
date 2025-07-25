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
from game.motor_combate import (
    processar_acao_jogador, processar_turno_monstro, 
    aplicar_efeitos_periodicos, decrementar_duracao_efeitos, esta_incapacitado
)
from data.construcoes_library import CONSTRUCOES


def criar_barra_status(atual: int, maximo: int, cor_cheia: str, tamanho: int = 10) -> str:
    if maximo <= 0: maximo = 1
    atual = max(0, atual)
    percentual = atual / maximo
    blocos_cheios = round(percentual * tamanho)
    blocos_vazios = tamanho - blocos_cheios
    cor_vazia = '▬'
    return f"`[{cor_cheia * blocos_cheios}{cor_vazia * blocos_vazios}]`"

class BattleView(discord.ui.View):
    def __init__(self, author: discord.User, bot: commands.Bot, jogador_data: dict, monstro_data: dict):
        super().__init__(timeout=None)
        self.author = author
        self.bot = bot
        self.jogador = jogador_data
        self.monstro = monstro_data
        self.log_batalha = "Batalha iniciada! É a sua vez."
        self.message: discord.Message = None
        self.timer_task = None
        self.add_skill_buttons()
    
    def add_skill_buttons(self):
        # ... (esta função não precisa de alterações)
        self.clear_items()
        ataque_basico_button = discord.ui.Button(label="Ataque Básico", style=discord.ButtonStyle.secondary, custom_id="basic_attack", emoji="🗡️")
        ataque_basico_button.callback = self.on_skill_use
        self.add_item(ataque_basico_button)
        for skill_id in self.jogador['habilidades_equipadas']:
            skill_info = HABILIDADES.get(skill_id)
            if skill_info:
                is_passive = skill_info.get('tipo') == 'PASSIVA'
                button_style = discord.ButtonStyle.secondary if is_passive else discord.ButtonStyle.primary
                button = discord.ui.Button(label=skill_info['nome'], style=button_style, custom_id=skill_id, emoji=skill_info.get('emoji'), disabled=is_passive)
                if not is_passive:
                    button.callback = self.on_skill_use
                self.add_item(button)
        backpack_button = discord.ui.Button(label="Mochila", style=discord.ButtonStyle.secondary, emoji="🎒", custom_id="backpack")
        backpack_button.callback = self.on_backpack_use
        self.add_item(backpack_button)

    def start_turn_timer(self):
        if self.timer_task: self.timer_task.cancel()
        self.timer_task = self.bot.loop.create_task(self.turn_timeout_task())

    # --- FUNÇÃO DE TIMEOUT CORRIGIDA ---
    async def turn_timeout_task(self):
        await asyncio.sleep(20.0)
        
        # --- CORREÇÃO APLICADA AQUI ---
        # 1. Desativa todos os botões para mostrar que o turno acabou.
        for item in self.children:
            item.disabled = True
            
        # 2. Atualiza o log e a mensagem para refletir o estado de botões desativados.
        self.log_batalha = "Você demorou demais para agir e perdeu o turno!"
        await self.message.edit(view=self) # Edita a view com os botões já desativados
        
        # 3. Continua para o turno do monstro.
        await self.process_monster_turn()

    async def on_skill_use(self, interaction: discord.Interaction):
        await interaction.response.defer()
        if self.timer_task: self.timer_task.cancel()
        
        # --- NOVO FLUXO DE TURNO DO JOGADOR ---
        # 1. Efeitos de início de turno (ex: veneno)
        self.log_batalha = aplicar_efeitos_periodicos(self.jogador)
        if self.jogador['vida_atual'] <= 0: return await self.derrota()

        # 2. Verifica se o jogador pode agir
        incapacitado, log_incapacitado = esta_incapacitado(self.jogador)
        if incapacitado:
            self.log_batalha += log_incapacitado
        else:
            # 3. Fase de Ação do Jogador
            skill_id = interaction.data['custom_id']
            resultado_jogador = processar_acao_jogador(self.jogador, self.monstro, skill_id)
            self.log_batalha += f"\n{resultado_jogador.get('log', '')}"
        
        # 4. Efeitos de fim de turno (decrementa durações)
        self.log_batalha += decrementar_duracao_efeitos(self.jogador)

        # Atualiza a UI e desativa botões
        for child in self.children: child.disabled = True
        await self.message.edit(embed=self.create_battle_embed(turno_de='jogador'), view=self)

        if "mana suficiente" in self.log_batalha:
            self.add_skill_buttons(); await self.message.edit(view=self); self.start_turn_timer()
            return

        if self.monstro['vida_atual'] <= 0: return await self.vitoria()
        
        # O turno do monstro agora é uma função separada para ser chamada tanto daqui quanto do timeout
        await self.process_monster_turn()

    async def process_monster_turn(self):
        self.log_batalha += f"\n\nO {self.monstro['nome']} está preparando uma ação..."
        await self.message.edit(embed=self.create_battle_embed(turno_de='monstro'), view=self)
        await asyncio.sleep(3)
        
        log_turno_monstro = ""

        # 1. Efeitos de início de turno do monstro
        log_turno_monstro += aplicar_efeitos_periodicos(self.monstro)
        if self.monstro['vida_atual'] <= 0: return await self.vitoria()

        # 2. Verifica se o monstro pode agir
        incapacitado, log_incapacitado = esta_incapacitado(self.monstro)
        if incapacitado:
            log_turno_monstro += log_incapacitado
        else:
            # 3. Fase de Ação do Monstro
            resultado_monstro = processar_turno_monstro(self.monstro, self.jogador)
            log_turno_monstro += f"\n{resultado_monstro['log']}"

        # 4. Efeitos de fim de turno do monstro
        log_turno_monstro += decrementar_duracao_efeitos(self.monstro)
        
        # Junta o log do jogador com o log completo do turno do monstro
        self.log_batalha = f"{self.log_batalha.splitlines()[0]}{log_turno_monstro}"
        if self.jogador['vida_atual'] <= 0: return await self.derrota()
        
        # Prepara a UI para o próximo turno do jogador
        self.add_skill_buttons()
        await self.message.edit(embed=self.create_battle_embed(turno_de='jogador'), view=self)
        self.start_turn_timer()

    # (O resto do código: create_battle_embed, on_stop, vitoria, derrota, etc. continua o mesmo)
    # ...
    def create_battle_embed(self, turno_de: str) -> discord.Embed:
        embed = discord.Embed(title="⚔️ BATALHA EM ANDAMENTO ⚔️", color=discord.Color.dark_orange())
        if turno_de == 'jogador':
            embed.set_image(url=self.jogador['imagem_url'])
            embed.set_author(name=f"Seu Turno, {self.jogador['nick']}!", icon_url=self.bot.user.display_avatar.url)
        elif turno_de == 'monstro':
            embed.set_image(url=self.monstro['imagem_url'])
            embed.set_author(name=f"Turno de: {self.monstro['nome']}", icon_url=self.monstro['imagem_url'])
        hp_bar_p = criar_barra_status(self.jogador['vida_atual'], self.jogador['stats']['VIDA_MAXIMA'], '🟥')
        mp_bar_p = criar_barra_status(self.jogador['mana_atual'], self.jogador['stats']['MANA_MAXIMA'], '🟦')
        jogador_stats_str = f"**HP:** `{self.jogador['vida_atual']}/{self.jogador['stats']['VIDA_MAXIMA']}`\n{hp_bar_p}\n\n**MP:** `{self.jogador['mana_atual']}/{self.jogador['stats']['MANA_MAXIMA']}`\n{mp_bar_p}"
        embed.add_field(name=f"VOCÊ ({self.jogador['classe']})", value=jogador_stats_str, inline=True)
        vida_monstro_atual = max(0, self.monstro['vida_atual'])
        hp_bar_m = criar_barra_status(vida_monstro_atual, self.monstro['stats']['VIDA_MAXIMA'], '🟥')
        monstro_stats_str = f"**HP:** `{vida_monstro_atual}/{self.monstro['stats']['VIDA_MAXIMA']}`\n{hp_bar_m}"
        embed.add_field(name=f"{self.monstro['emoji']} {self.monstro['nome']}", value=monstro_stats_str, inline=True)
        embed.add_field(name="Log de Batalha", value=f">>> {self.log_batalha}", inline=False)
        return embed
    
    async def on_stop(self):
        if self.timer_task:
            self.timer_task.cancel()

    async def vitoria(self):
        self.stop()
        for child in self.children: child.disabled = True
        xp_ganho = self.monstro.get('xp_recompensa', 0)
        if xp_ganho > 0:
            from game.leveling_system import grant_xp
            grant_xp(user_id=str(self.author.id), amount=xp_ganho)
        embed = self.create_battle_embed(turno_de='jogador')
        embed.title = "🎉 VITÓRIA! 🎉"; embed.color = discord.Color.gold()
        self.log_batalha += f"\nVocê derrotou o {self.monstro['nome']} e ganhou `{xp_ganho}` de XP!"
        embed.set_field_at(2, name="Log de Batalha", value=f">>> {self.log_batalha}", inline=False)
        await self.message.edit(embed=embed, view=self)
    
    async def derrota(self):
        self.stop()
        for child in self.children: child.disabled = True
        embed = self.create_battle_embed(turno_de='monstro')
        embed.title = "☠️ VOCÊ FOI DERROTADO ☠️"; embed.color = discord.Color.darker_grey()
        await self.message.edit(embed=embed, view=self)
        
    async def on_backpack_use(self, interaction: discord.Interaction):
        await interaction.response.send_message("O uso de itens em batalha será implementado em breve!", ephemeral=True)

class MundoCog(commands.Cog):
    # (A classe MundoCog não precisa de alterações)
    # ...
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="explorar", description="Explore a área em busca de monstros.")
    async def explorar(self, interaction: discord.Interaction):
        await interaction.response.defer()
        user_id_str = str(interaction.user.id)
        player_ref = db.collection('players').document(user_id_str)
        player_doc = player_ref.get()
        char_ref = db.collection('characters').document(user_id_str)
        char_doc = char_ref.get()
        if not player_doc.exists or not char_doc.exists:
            await interaction.followup.send("Você precisa se registrar (`/registrar`) e criar um personagem (`/perfil`) primeiro!")
            return
        player_data = player_doc.to_dict()
        char_data = char_doc.to_dict()
        equipped_items_data = []
        inventory_snapshot = db.collection('characters').document(user_id_str).collection('inventario').where('equipado', '==', True).stream()
        for item_ref in inventory_snapshot:
            instance_doc = db.collection('items').document(item_ref.id).get()
            if instance_doc.exists:
                equipped_items_data.append({"instance_data": instance_doc.to_dict()})
        stats_completos = calcular_stats_completos(char_data, equipped_items_data)
        vida_maxima_final = stats_completos.get('VIDA_MAXIMA', 100)
        mana_maxima_final = stats_completos.get('MANA_MAXIMA', 100)
        vida_atual_corrigida = min(char_data.get('vida_atual', vida_maxima_final), vida_maxima_final)
        mana_atual_corrigida = min(char_data.get('mana_atual', mana_maxima_final), mana_maxima_final)
        jogador_para_batalha = {
            "stats": stats_completos,
            "vida_atual": vida_atual_corrigida,
            "mana_atual": mana_atual_corrigida,
            "habilidades_equipadas": char_data.get('habilidades_equipadas', []),
            "classe": char_data.get('classe'),
            "imagem_url": CLASSES_DATA.get(char_data.get('classe'), {}).get('image_url'),
            "nick": player_data.get('nick', interaction.user.display_name),
            "nome": player_data.get('nick', interaction.user.display_name), # Adicionado para consistência
            "efeitos_ativos": [] # NOVO: Inicializa a lista de efeitos
        }
        monster_id = random.choice(list(MONSTROS.keys()))
        monstro_template = MONSTROS.get(monster_id)
        if not monstro_template:
            await interaction.followup.send(f"Erro ao encontrar dados do monstro: {monster_id}")
            return
        monstro_para_batalha = {
            "id": monster_id, "nome": monstro_template['nome'], "emoji": monstro_template['emoji'],
            "stats": monstro_template['stats'], "vida_atual": monstro_template['stats']['VIDA_MAXIMA'],
            "xp_recompensa": monstro_template.get('xp_recompensa', 0),
            "imagem_url": monstro_template.get('imagem_url'),
            "efeitos_ativos": [] # NOVO: Inicializa a lista de efeitos
        }
        view = BattleView(author=interaction.user, bot=self.bot, jogador_data=jogador_para_batalha, monstro_data=monstro_para_batalha)
        embed = view.create_battle_embed(turno_de='jogador')
        message = await interaction.followup.send(embed=embed, view=view)
        view.message = message
        view.start_turn_timer()
        
    # --- NOVO COMANDO /VIAJAR ---
    @app_commands.command(name="viajar", description="Viaje para a cidade atual (o servidor onde o comando é usado).")
    async def viajar(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        user_id_str = str(interaction.user.id)
        cidade_alvo_id = str(interaction.guild.id)
        cidade_alvo_nome = interaction.guild.name

        char_ref = db.collection('characters').document(user_id_str)
        char_doc = char_ref.get()

        if not char_doc.exists:
            await interaction.followup.send("Você precisa ter um personagem para viajar. Use `/perfil` para criar um.", ephemeral=True)
            return
            
        char_data = char_doc.to_dict()
        localizacao_atual_id = char_data.get('localizacao_id')

        # Verifica se o jogador já está na cidade
        if localizacao_atual_id == cidade_alvo_id:
            await interaction.followup.send(f"Você já está em **{cidade_alvo_nome}**!", ephemeral=True)
            return
            
        # Atualiza a localização no Firebase
        char_ref.update({
            'localizacao_id': cidade_alvo_id
        })

        embed = discord.Embed(
            title="🛶 Viagem Concluída!",
            description=f"Você chegou à cidade de **{cidade_alvo_nome}**.\nSua localização foi atualizada.",
            color=discord.Color.blue()
        )
        embed.set_footer(text="Explore os arredores com /explorar.")
        
        await interaction.followup.send(embed=embed, ephemeral=True)
        
    # --- NOVO COMANDO /CIDADE ---
    @app_commands.command(name="cidade", description="Mostra as informações da cidade atual.")
    async def cidade(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        cidade_id = str(interaction.guild.id)
        cidade_ref = db.collection('cidades').document(cidade_id)
        cidade_doc = cidade_ref.get()

        if not cidade_doc.exists:
            await interaction.followup.send(
                "Este lugar parece selvagem e não civilizado...\n"
                "*Um administrador do servidor precisa usar o comando `!configurar_cidade` para fundar a cidade.*",
                ephemeral=True
            )
            return

        cidade_data = cidade_doc.to_dict()
        
        # --- NOVO EMBED REDESENHADO ---
        embed = discord.Embed(
            title=f"📍 Bem-vindo(a) a {cidade_data.get('nome', 'Cidade Desconhecida')}!",
            description=f"*{cidade_data.get('descricao', 'Um lugar com muito a se explorar.')}*",
            color=discord.Color.from_rgb(128, 174, 184) # Um tom de azul acinzentado
        )

        # Busca o nome do prefeito
        prefeito_nome = "Ninguém"
        if prefeito_id := cidade_data.get('prefeito_id'):
            try:
                prefeito_user = await self.bot.fetch_user(int(prefeito_id))
                prefeito_nome = prefeito_user.display_name
            except discord.NotFound:
                prefeito_nome = "Um líder esquecido"
        
        embed.add_field(name="👑 Prefeito(a)", value=prefeito_nome, inline=False)
        embed.add_field(name="\u200b", value="\u200b", inline=False) # Linha em branco para espaçamento

        # Agrupando construções por categoria
        recursos_str = ""
        criacao_str = ""
        servicos_str = ""

        construcoes_data = cidade_data.get('construcoes', {})

        for building_id, building_info in CONSTRUCOES.items():
            if building_id in construcoes_data:
                nivel = construcoes_data[building_id].get('nivel')
                emoji = building_info.get('emoji', '')
                nome = building_info.get('nome', building_id)
                
                # Exibe "Não construído" para nível 0
                nivel_str = f"Nível {nivel}" if nivel > 0 else "*(Não Construído)*"
                linha = f"{emoji} **{nome}** - {nivel_str}\n"

                if building_id in ["MINA", "FLORESTA"]:
                    recursos_str += linha
                elif building_id in ["FORJA", "MESA_TRABALHO", "MESA_POCOES"]:
                    criacao_str += linha
                else:
                    servicos_str += linha
        
        if recursos_str:
            embed.add_field(name="Recursos", value=recursos_str, inline=True)
        if criacao_str:
            embed.add_field(name="Criação", value=criacao_str, inline=True)
        if servicos_str:
            embed.add_field(name="Serviços", value=servicos_str, inline=True)
        
        await interaction.followup.send(embed=embed, ephemeral=True)
        

async def setup(bot: commands.Bot):
    await bot.add_cog(MundoCog(bot))