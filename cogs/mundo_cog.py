# cogs/mundo_cog.py
import discord
import random
import asyncio
from discord import app_commands, ui
from discord.ext import commands
from firebase_admin import firestore
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
from utils.storage_helper import get_signed_url
from ui.views import UpgradeView, GovernarPanelView
from utils.converters import get_player_game_id
from cogs.item_cog import get_and_increment_item_id
from game.motor_combate import processar_acao_em_grupo, processar_turno_monstro_em_grupo
from game.leveling_system import grant_xp


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
        ataque_basico_button = discord.ui.Button(label="", style=discord.ButtonStyle.secondary, custom_id="basic_attack", emoji="🗡️")
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
    
    async def vitoria(self):
        self.stop()
        for child in self.children:
            child.disabled = True

        recompensas_log = []
        user_id_str = str(self.author.id)
        char_ref = db.collection('characters').document(user_id_str)

        # --- 1. Processamento de XP ---
        xp_ganho = self.monstro.get('xp_recompensa', 0)
        if xp_ganho > 0:
            # Importa a função de XP aqui para evitar problemas de dependência
            from game.leveling_system import grant_xp
            grant_xp(user_id=user_id_str, amount=xp_ganho)
            recompensas_log.append(f"🌟 {xp_ganho} Pontos de Experiência")

        # --- 2. Processamento de Moedas ---
        moedas_info = self.monstro.get('moedas_recompensa', {})
        if moedas_info:
            moedas_ganhas = random.randint(moedas_info.get('min', 0), moedas_info.get('max', 0))
            if moedas_ganhas > 0:
                char_ref.update({"moedas": firestore.Increment(moedas_ganhas)})
                recompensas_log.append(f"🪙 {moedas_ganhas} Moedas")

        # --- 3. Processamento de Loot (Itens) ---
        loot_table = self.monstro.get('loot_table', [])
        itens_dropados_nomes = []
        if loot_table:
            for item_drop in loot_table:
                # Rola o dado para ver se o item dropa
                if random.random() < item_drop.get('chance', 0):
                    # Usando a chave correta "item_template_id" do seu arquivo de monstros
                    template_id = item_drop.get('item_template_id')
                    if not template_id:
                        continue

                    template_ref = db.collection('item_templates').document(template_id)
                    template_doc = template_ref.get()
                    if not template_doc.exists:
                        print(f"AVISO DE SISTEMA: Template de loot '{template_id}' não foi encontrado no banco de dados.")
                        continue
                    
                    template_data = template_doc.to_dict()
                    stats_gerados = {s: random.randint(v['min'], v['max']) for s, v in template_data.get('stats_base', {}).items()}
                    
                    transaction = db.transaction()
                    item_id = get_and_increment_item_id(transaction)
                    
                    item_ref = db.collection('items').document(str(item_id))
                    item_data = {
                        "template_id": template_id, 
                        "owner_id": user_id_str, 
                        "stats_gerados": stats_gerados, 
                        "encantamentos_aplicados": []
                    }
                    item_ref.set(item_data)
                    
                    inventory_ref = char_ref.collection('inventario').document(str(item_id))
                    inventory_ref.set({'equipado': False})
                    
                    itens_dropados_nomes.append(template_data['nome'])

        if itens_dropados_nomes:
            for nome_item in itens_dropados_nomes:
                 recompensas_log.append(f"🎁 {nome_item}")

        # --- 4. Criação do Embed de Vitória Limpo ---
        embed = discord.Embed(
            title="🎉 VITÓRIA! 🎉",
            description=f"Você derrotou o **{self.monstro['nome']}** e saiu vitorioso do combate!",
            color=discord.Color.gold()
        )
        
        # Adiciona a imagem do jogador como miniatura
        if self.jogador.get('imagem_url'):
            embed.set_thumbnail(url=self.jogador['imagem_url'])

        if recompensas_log:
            # Usando quebras de linha \n para separar os itens da recompensa
            recompensas_texto = "\n".join(recompensas_log)
            embed.add_field(
                name="Recompensas Coletadas",
                value=f"```\n{recompensas_texto}\n```",
                inline=False
            )
        else:
            embed.add_field(
                name="Recompensas",
                value="Você não coletou nenhuma recompensa específica desta batalha.",
                inline=False
            )

        embed.set_footer(text="A aventura continua...")
        
        # Edita a mensagem original com o novo embed limpo e sem botões
        await self.message.edit(embed=embed, view=None)
    
    async def derrota(self):
        self.stop() # Para a View e desativa o timeout
        
        # --- 1. Criação do Novo Embed de Derrota ---
        embed = discord.Embed(
            title="☠️ VOCÊ FOI DERROTADO ☠️",
            description=f"Você não resistiu ao poder de **{self.monstro['nome']}** e sucumbiu em batalha.",
            color=discord.Color.dark_red()
        )
        
        # Adiciona a imagem do monstro que venceu, para dar mais impacto
        if self.monstro.get('imagem_url'):
            embed.set_image(url=self.monstro['imagem_url'])
        
        # --- 2. Adiciona um campo para as Consequências ---
        # Por enquanto, é um texto temático. No futuro, podemos adicionar penalidades aqui.
        consequencias_texto = (
            "Você acorda um tempo depois, sentindo-se enfraquecido, mas vivo.\n"
            "Felizmente, você não perdeu nenhum item ou experiência desta vez."
        )
        embed.add_field(
            name="Consequências da Derrota",
            value=consequencias_texto,
            inline=False
        )

        embed.set_footer(text="Mais sorte na próxima vez, aventureiro.")
        
        # --- 3. Edita a mensagem original com o novo embed, removendo os botões ---
        await self.message.edit(embed=embed, view=None)
        
    async def on_backpack_use(self, interaction: discord.Interaction):
        await interaction.response.send_message("O uso de itens em batalha será implementado em breve!", ephemeral=True)
        
# --- CLASSE CoopBattleView COM A TELA DE VITÓRIA FUNCIONAL ---
class CoopBattleView(discord.ui.View):
    def __init__(self, bot: commands.Bot, jogadores_data: list, monstros_data: list, tier: int):
        super().__init__(timeout=300)
        self.bot = bot
        self.jogadores = jogadores_data
        self.monstros = monstros_data
        self.tier = tier
        
        # --- ADIÇÃO IMPORTANTE ---
        # Guarda uma cópia da lista original de monstros para calcular as recompensas no final
        self.monstros_originais = monstros_data.copy()
        
        self.ordem_de_turno = []
        self.combatente_atual_index = -1 
        self.combatente_atual = None
        self.estado = "INICIANDO"
        self.habilidade_selecionada = None
        self.log_batalha = f"Uma batalha de Tier {tier} começou!"
        self.message: discord.Message = None

    async def iniciar_batalha(self):
        """Função chamada externamente para dar o pontapé inicial no ciclo de turnos."""
        await self.avancar_turno()

    async def avancar_turno(self):
        """Gerencia o fluxo de turnos, pulando monstros e parando em jogadores."""
        # Filtra os mortos no início de cada avanço
        self.jogadores = [p for p in self.jogadores if p['vida_atual'] > 0]
        self.monstros = [m for m in self.monstros if m['vida_atual'] > 0]
        
        if not self.monstros: return await self.vitoria()
        if not self.jogadores: return await self.derrota()

        self.ordem_de_turno = self.jogadores + self.monstros
        
        # Avança para o próximo combatente
        self.combatente_atual_index = (self.combatente_atual_index + 1) % len(self.ordem_de_turno)
        self.combatente_atual = self.ordem_de_turno[self.combatente_atual_index]

        # Atualiza o log para o novo turno
        novo_log = f"É a vez de **{self.combatente_atual.get('nick', self.combatente_atual.get('nome'))}**."
        log_antigo = self.log_batalha.split('---')[-1].strip()
        self.log_batalha = f"{log_antigo}\n---\n{novo_log}"

        # --- LÓGICA PRINCIPAL CORRIGIDA ---
        # Se for um monstro, resolve o turno dele e chama a si mesmo para avançar de novo.
        if self.combatente_atual in self.monstros:
            self.estado = "TURNO_MONSTRO"
            await self.atualizar_mensagem_batalha() # Mostra o painel (sem botões)
            await asyncio.sleep(2.5) # Pausa para o jogador ler

            resultado_monstro = processar_turno_monstro_em_grupo(self.combatente_atual, self.jogadores)
            self.log_batalha += "\n" + resultado_monstro.get('log', '')
            
            # Chama a si mesmo para passar para o próximo combatente
            await self.avancar_turno()
        
        # Se for um jogador, para e espera a interação.
        else:
            self.estado = "ESCOLHENDO_ACAO"
            await self.atualizar_mensagem_batalha() # Mostra o painel (com botões de ação)

    # Função síncrona apenas para criar os botões
    def _configurar_botoes_para_turno(self):
        self.clear_items()
        
        if self.estado == "ESCOLHENDO_ACAO" and self.combatente_atual in self.jogadores:
            jogador_atual = self.combatente_atual
            ataque_basico = discord.ui.Button(label="Ataque Básico", custom_id="basic_attack", emoji="🗡️")
            ataque_basico.callback = self.on_skill_click
            self.add_item(ataque_basico)
            for skill_id in jogador_atual.get('habilidades_equipadas', []):
                skill_info = HABILIDADES.get(skill_id)
                if skill_info and skill_info.get('tipo') == 'ATIVA':
                    button = discord.ui.Button(label=skill_info['nome'], custom_id=skill_id, emoji=skill_info.get('emoji'))
                    button.callback = self.on_skill_click
                    self.add_item(button)

        elif self.estado == "ESCOLHENDO_ALVO":
            skill_info = HABILIDADES.get(self.habilidade_selecionada, {})
            target_type = skill_info.get("alvo", "inimigo")
            alvos_disponiveis = [m for m in self.monstros if m['vida_atual'] > 0] if target_type == "inimigo" else [p for p in self.jogadores if p['vida_atual'] > 0]
            
            # --- A CORREÇÃO ESTÁ AQUI ---
            # O custom_id agora usa 'i' de enumerate, que é sempre único (0, 1, 2...).
            for i, alvo in enumerate(alvos_disponiveis):
                button = discord.ui.Button(label=alvo.get('nick', alvo.get('nome')), custom_id=f"target_{i}")
                button.callback = self.on_target_click
                self.add_item(button)
            
            cancel_button = discord.ui.Button(label="Cancelar", style=discord.ButtonStyle.danger, custom_id="cancel_action")
            cancel_button.callback = self.on_cancel_click
            self.add_item(cancel_button)

    async def atualizar_mensagem_batalha(self):
        """Prepara os botões e atualiza a mensagem."""
        self._configurar_botoes_para_turno()
        embed = self.create_battle_embed()
        if self.message:
            await self.message.edit(embed=embed, view=self)

    async def avancar_turno(self):
        # Filtra combatentes mortos
        self.jogadores = [p for p in self.jogadores if p['vida_atual'] > 0]
        self.monstros = [m for m in self.monstros if m['vida_atual'] > 0]
        
        if not self.monstros:
            return await self.vitoria()
        if not self.jogadores:
            return await self.derrota()

        self.ordem_de_turno = self.jogadores + self.monstros
        # Lógica para encontrar o próximo combatente na lista de vivos
        try:
            current_true_index = self.ordem_de_turno.index(self.combatente_atual)
            self.combatente_atual_index = (current_true_index + 1) % len(self.ordem_de_turno)
        except ValueError: # Caso o combatente atual tenha morrido
            self.combatente_atual_index = 0

        self.combatente_atual = self.ordem_de_turno[self.combatente_atual_index]
        
        novo_log = f"É a vez de **{self.combatente_atual.get('nick', self.combatente_atual.get('nome'))}**."
        log_antigo = self.log_batalha.split('---')[-1].strip()
        self.log_batalha = f"{log_antigo}\n---\n{novo_log}"
        
        self.estado = "ESCOLHENDO_ACAO"
        
        await self.update_view_para_turno() #

        if self.combatente_atual in self.monstros:
            await asyncio.sleep(2.5)
            
            resultado_monstro = processar_turno_monstro_em_grupo(self.combatente_atual, self.jogadores)
            self.log_batalha += "\n" + resultado_monstro.get('log', '')
            
            await self.avancar_turno()

    async def update_view_para_turno(self):
        self.clear_items()
        
        if self.estado == "ESCOLHENDO_ACAO" and self.combatente_atual in self.jogadores:
            jogador_atual = self.combatente_atual
            ataque_basico = discord.ui.Button(label="Ataque Básico", custom_id="basic_attack", emoji="🗡️")
            ataque_basico.callback = self.on_skill_click
            self.add_item(ataque_basico)

            for skill_id in jogador_atual.get('habilidades_equipadas', []):
                skill_info = HABILIDADES.get(skill_id)
                if skill_info and skill_info.get('tipo') == 'ATIVA':
                    button = discord.ui.Button(label=skill_info['nome'], custom_id=skill_id, emoji=skill_info.get('emoji'))
                    button.callback = self.on_skill_click
                    self.add_item(button)

        elif self.estado == "ESCOLHENDO_ALVO":
            skill_info = HABILIDADES.get(self.habilidade_selecionada, {})
            target_type = skill_info.get("alvo", "inimigo")

            alvos_disponiveis = [m for m in self.monstros if m['vida_atual'] > 0] if target_type == "inimigo" else [p for p in self.jogadores if p['vida_atual'] > 0]
            
            for i, alvo in enumerate(alvos_disponiveis):
                # O custom_id agora guarda o índice original do alvo na lista mestre
                original_index = (self.monstros if target_type == "inimigo" else self.jogadores).index(alvo)
                button = discord.ui.Button(label=alvo.get('nick', alvo.get('nome')), custom_id=f"target_{original_index}")
                button.callback = self.on_target_click
                self.add_item(button)
            
            cancel_button = discord.ui.Button(label="Cancelar", style=discord.ButtonStyle.danger, custom_id="cancel_action")
            cancel_button.callback = self.on_cancel_click
            self.add_item(cancel_button)

        embed = self.create_battle_embed()
        if self.message:
            await self.message.edit(embed=embed, view=self)

    async def on_skill_click(self, interaction: discord.Interaction):
        if interaction.user.id != self.combatente_atual.get('id'):
            return await interaction.response.send_message("Não é o seu turno para agir!", ephemeral=True)
        
        await interaction.response.defer()
        
        skill_id = interaction.data['custom_id']
        skill_info = HABILIDADES.get(skill_id, {})
        target_type = skill_info.get("alvo", "inimigo")
        
        self.habilidade_selecionada = skill_id
        
        if target_type in ["self", "todos_inimigos", "grupo_aliado", "outros_aliados", "aleatorio_inimigo"]:
            alvos = []
            if target_type == "self": alvos = [self.combatente_atual]
            elif target_type == "todos_inimigos": alvos = [m for m in self.monstros if m['vida_atual'] > 0]
            elif target_type == "grupo_aliado": alvos = [p for p in self.jogadores if p['vida_atual'] > 0]
            elif target_type == "outros_aliados": alvos = [p for p in self.jogadores if p is not self.combatente_atual and p['vida_atual'] > 0]
            elif target_type == "aleatorio_inimigo": alvos = [random.choice([m for m in self.monstros if m['vida_atual'] > 0])] if any(m['vida_atual'] > 0 for m in self.monstros) else []
            
            if alvos:
                resultado = processar_acao_em_grupo(self.combatente_atual, alvos, skill_id)
                self.log_batalha += "\n" + resultado.get('log', '')
            
            await self.avancar_turno()
        else:
            self.estado = "ESCOLHENDO_ALVO"
            await self.update_view_para_turno()

    async def on_target_click(self, interaction: discord.Interaction):
        if interaction.user.id != self.combatente_atual.get('id'):
            return await interaction.response.send_message("Não é o seu turno para agir!", ephemeral=True)
        await interaction.response.defer()
        target_index = int(interaction.data['custom_id'].split('_')[-1])
        skill_info = HABILIDADES.get(self.habilidade_selecionada, {})
        target_type = skill_info.get("alvo", "inimigo")

        # --- PONTO PRINCIPAL DA CORREÇÃO ---
        # Recria a lista de alvos para garantir que o índice seja o correto.
        alvos_disponiveis = [m for m in self.monstros if m['vida_atual'] > 0] if target_type == "inimigo" else [p for p in self.jogadores if p['vida_atual'] > 0]
        
        try:
            alvo = alvos_disponiveis[target_index]
        except IndexError:
            self.estado = "ESCOLHENDO_ACAO"
            await self.atualizar_mensagem_batalha()
            return

        resultado = processar_acao_em_grupo(self.combatente_atual, [alvo], self.habilidade_selecionada)
        self.log_batalha += "\n" + resultado.get('log', '')
        
        self.habilidade_selecionada = None
        await self.avancar_turno()

    async def on_cancel_click(self, interaction: discord.Interaction):
        if interaction.user.id != self.combatente_atual.get('id'):
            return await interaction.response.send_message("Não é o seu turno para agir!", ephemeral=True)
        
        await interaction.response.defer()
        self.estado = "ESCOLHENDO_ACAO"
        self.habilidade_selecionada = None
        await self.update_view_para_turno()

    def create_battle_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title=f"⚔️ Fenda Abissal - Tier {self.tier} ⚔️", 
            color=discord.Color.dark_orange()
        )
        
        if image_url := self.combatente_atual.get('imagem_url'):
            embed.set_image(url=image_url)
        
        jogadores_str = ""
        for p in self.jogadores:
            indicador_turno = "🎯" if p is self.combatente_atual else ""
            vida_atual_p = p['vida_atual']
            vida_maxima_p = p['stats']['VIDA_MAXIMA']
            mana_atual = p['mana_atual']
            mana_maxima = p['stats']['MANA_MAXIMA']
            hp_bar_p = criar_barra_status(vida_atual_p, vida_maxima_p, '🟥')
            mp_bar = criar_barra_status(mana_atual, mana_maxima, '🟦')
            status_emoji_p = "✅" if vida_atual_p > 0 else "💀"
            jogadores_str += (
                f"{status_emoji_p} **{p['nick']}** ({p['classe']}) {indicador_turno}\n"
                f"`HP: {vida_atual_p}/{vida_maxima_p}`\n{hp_bar_p}\n"
                f"`MP: {mana_atual}/{mana_maxima}`\n{mp_bar}\n\n"
            )
        embed.add_field(name="Aventureiros", value=jogadores_str.strip(), inline=True)
        
        monstros_str = ""
        for m in self.monstros:
            indicador_turno = "🎯" if m is self.combatente_atual else ""
            vida_atual_m = m['vida_atual']
            vida_maxima_m = m['stats']['VIDA_MAXIMA']
            hp_bar_m = criar_barra_status(vida_atual_m, vida_maxima_m, '🟪')
            status_emoji_m = "👹" if vida_atual_m > 0 else "☠️"
            monstros_str += (
                f"{status_emoji_m} **{m['nome']}** {indicador_turno}\n"
                f"`HP: {vida_atual_m}/{vida_maxima_m}`\n{hp_bar_m}\n\n"
            )
        embed.add_field(name="Monstros", value=monstros_str.strip(), inline=True)
        
        embed.add_field(name="Log de Batalha", value=f">>> {self.log_batalha}", inline=False)
        embed.set_footer(text=f"Turno de: {self.combatente_atual.get('nick', self.combatente_atual.get('nome'))}")
        return embed
    
    # --- MÉTODO DE VITÓRIA TOTALMENTE IMPLEMENTADO ---
    async def vitoria(self):
        self.stop()
        jogadores_vivos = self.jogadores # A lista já contém apenas os sobreviventes

        if not jogadores_vivos:
            embed = discord.Embed(title="Batalha Concluída", description="Todos os combatentes pereceram, não há vencedores.", color=discord.Color.dark_grey())
            return await self.message.edit(embed=embed, view=None)

        # 1. CALCULAR RECOMPENSAS COMPARTILHADAS (XP & MOEDAS)
        total_xp = 0
        total_moedas = 0
        for monstro in self.monstros_originais:
            total_xp += monstro.get('xp_recompensa', 0)
            moedas_info = monstro.get('moedas_recompensa', {})
            if moedas_info:
                total_moedas += random.randint(moedas_info.get('min', 0), moedas_info.get('max', 0))

        xp_por_jogador = total_xp // len(jogadores_vivos)
        moedas_por_jogador = total_moedas // len(jogadores_vivos)

        # 2. CALCULAR ITENS (LOOT POOL)
        loot_pool = []
        for monstro in self.monstros_originais:
            for item_drop_info in monstro.get('loot_table', []):
                if random.random() < item_drop_info.get('chance', 0):
                    loot_pool.append(item_drop_info['item_template_id'])

        # 3. DISTRIBUIR ITENS E APLICAR RECOMPENSAS
        recompensas_individuais = {p['id']: [] for p in jogadores_vivos}
        if loot_pool:
            for item_template_id in loot_pool:
                jogador_sorteado = random.choice(jogadores_vivos)
                user_id_str = str(jogador_sorteado['id'])
                
                template_doc = db.collection('item_templates').document(item_template_id).get()
                if not template_doc.exists: continue
                template_data = template_doc.to_dict()
                
                # Cria a instância do item
                transaction = db.transaction()
                item_id = get_and_increment_item_id(transaction)
                stats_gerados = {s: random.randint(v['min'], v['max']) for s, v in template_data.get('stats_base', {}).items()}
                item_data = {"template_id": item_template_id, "owner_id": user_id_str, "stats_gerados": stats_gerados, "encantamentos_aplicados": []}
                db.collection('items').document(str(item_id)).set(item_data)
                
                # Adiciona ao inventário do jogador sorteado
                db.collection('characters').document(user_id_str).collection('inventario').document(str(item_id)).set({'equipado': False})
                recompensas_individuais[jogador_sorteado['id']].append(template_data['nome'])

        # 4. MONTAR O EMBED FINAL
        embed = discord.Embed(title="🎉 VITÓRIA! 🎉", description=f"O grupo conquistou os desafios da Fenda Abissal de **Tier {self.tier}**!", color=discord.Color.gold())

        shared_rewards_str = ""
        if xp_por_jogador > 0: shared_rewards_str += f"🌟 `{xp_por_jogador}` Pontos de Experiência\n"
        if moedas_por_jogador > 0: shared_rewards_str += f"🪙 `{moedas_por_jogador}` Moedas"
        embed.add_field(name="Recompensas para Cada Aventureiro", value=shared_rewards_str or "Nenhuma recompensa compartilhada.", inline=False)
        
        individual_rewards_str = ""
        for jogador in jogadores_vivos:
            user_id_str = str(jogador['id'])
            # Aplica XP e Moedas no banco de dados
            grant_xp(user_id=user_id_str, amount=xp_por_jogador)
            db.collection('characters').document(user_id_str).update({"moedas": firestore.Increment(moedas_por_jogador)})
            
            # Monta a string para o embed
            itens_recebidos = recompensas_individuais.get(jogador['id'], [])
            individual_rewards_str += f"**{jogador['nick']}** recebeu:\n"
            if itens_recebidos:
                individual_rewards_str += "\n".join([f" > 🎁 `{nome}`" for nome in itens_recebidos]) + "\n\n"
            else:
                individual_rewards_str += " > *Nenhum item*\n\n"
        
        if loot_pool:
            embed.add_field(name="Tesouros Distribuídos", value=individual_rewards_str.strip(), inline=False)
            
        await self.message.edit(embed=embed, view=None)

    async def derrota(self):
        # (Placeholder)
        self.stop()
        embed = self.create_battle_embed()
        embed.title = "☠️ DERROTA ☠️"
        await self.message.edit(embed=embed, view=None)
    

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
        
        classe_info = CLASSES_DATA.get(char_data.get('classe'), {})
        combat_path = classe_info.get('combat_image_path')
        combat_url = get_signed_url(combat_path) if combat_path else None
        
        jogador_para_batalha = {
            "stats": stats_completos,
            "vida_atual": vida_atual_corrigida,
            "mana_atual": mana_atual_corrigida,
            "habilidades_equipadas": char_data.get('habilidades_equipadas', []),
            "classe": char_data.get('classe'),
            "imagem_url": combat_url,
            "nick": player_data.get('nick', interaction.user.display_name),
            "nome": player_data.get('nick', interaction.user.display_name), # Adicionado para consistência
            "efeitos_ativos": [] # NOVO: Inicializa a lista de efeitos
        }
        monster_id = random.choice(list(MONSTROS.keys()))
        monstro_template = MONSTROS[monster_id]
        
        # --- BLOCO CORRIGIDO ABAIXO ---

        # 1. Faz uma cópia COMPLETA do template do monstro.
        #    Isso garante que loot_table, moedas_recompensa, e tudo mais seja incluído.
        monstro_para_batalha = monstro_template.copy()
        
        # 2. Adiciona os dados específicos da instância da batalha.
        monstro_para_batalha['id'] = monster_id
        monstro_para_batalha['vida_atual'] = monstro_template['stats']['VIDA_MAXIMA']
        monstro_para_batalha['efeitos_ativos'] = []
        
        
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
        
    # --- COMANDO /CIDADE COM CATEGORIAS LADO A LADO ---
    @app_commands.command(name="cidade", description="Mostra as informações da cidade atual.")
    async def cidade(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        cidade_id = str(interaction.guild.id)
        cidade_ref = db.collection('cidades').document(cidade_id)
        cidade_doc = cidade_ref.get()

        if not cidade_doc.exists:
            await interaction.followup.send(
                "Este lugar parece selvagem e não civilizado...\n"
                "*Um administrador do servidor precisa usar o comando `/governar` para fundar a cidade.*",
                ephemeral=True
            )
            return

        cidade_data = cidade_doc.to_dict()
        
        embed = discord.Embed(
            title=f"📍 {cidade_data.get('nome', 'Cidade Desconhecida')}",
            description=f"*{cidade_data.get('descricao', 'Um lugar com muito a se explorar.')}*",
            color=discord.Color.from_rgb(128, 174, 184)
        )

        # --- SEÇÃO DE GOVERNANÇA ---
        governador_nome = "Ninguém"
        if governador_id := cidade_data.get('governador_id'):
            player_query = db.collection('players').where('game_id', '==', governador_id).limit(1).stream()
            for player_doc in player_query:
                governador_nome = player_doc.to_dict().get('nick', 'Líder Desconhecido')
        
        vices_str = "Nenhum"
        if vice_ids := cidade_data.get('vice_governadores_ids', []):
            vices_query = db.collection('players').where('game_id', 'in', vice_ids).stream()
            vices_data = {p.to_dict()['game_id']: p.to_dict()['nick'] for p in vices_query}
            vices_nicks = [f"**{vices_data.get(gid, '*desconhecido*')}**" for gid in vice_ids]
            if vices_nicks:
                vices_str = ", ".join(vices_nicks)

        governanca_str = f"👑 **Governador(a):** {governador_nome}\n👥 **Vices:** {vices_str}"
        embed.add_field(name="------", value=governanca_str, inline=False)
        
        construcao_andamento = cidade_data.get('construcao_em_andamento')
                
        # --- DESTAQUE PARA O CENTRO DA VILA ---
        construcoes_data = cidade_data.get('construcoes', {})
        cv_data = construcoes_data.get("CENTRO_VILA")
        if cv_data:
            cv_info = CONSTRUCOES["CENTRO_VILA"]
            cv_nivel = cv_data.get("nivel", 0)
            status_str = f"Nível {cv_nivel}"
            if construcao_andamento and construcao_andamento['id_construcao'] == 'CENTRO_VILA':
                status_str = "*(Melhorando...)*"
            
            cv_str = (
                f"{cv_info['emoji']} **{cv_info['nome']} - {status_str}**\n"
                f"*{cv_info['descricao']}*"
            )
            embed.add_field(name="------", value=cv_str, inline=False)

        # --- SEÇÕES DE CONSTRUÇÕES POR CATEGORIA ---
        recursos_str, criacao_str, servicos_str = "", "", ""
        recursos_ids = ["MINA", "FLORESTA"]
        criacao_ids = ["FORJA", "MESA_TRABALHO", "MESA_POCOES"]

        for building_id, building_info in CONSTRUCOES.items():
            if building_id == "CENTRO_VILA": continue

            if building_id in construcoes_data:
                nivel = construcoes_data[building_id].get('nivel', 0)
                status_str = f"Nível {nivel}" if nivel > 0 else "*(Não Construído)*"
                if construcao_andamento and construcao_andamento['id_construcao'] == building_id:
                    status_str = "*(Melhorando...)*"
                
                linha = f"{building_info['emoji']} **{building_info['nome']}** - {status_str}\n"

                if building_id in recursos_ids:
                    recursos_str += linha
                elif building_id in criacao_ids:
                    criacao_str += linha
                else: 
                    servicos_str += linha
        
        # --- ALTERAÇÃO APLICADA AQUI ---
        # Alterado para inline=True para colocar os campos lado a lado.
        if recursos_str: embed.add_field(name="--- ⛏️ Recursos ---", value=recursos_str.strip(), inline=True)
        if criacao_str: embed.add_field(name="--- 🛠️ Criação ---", value=criacao_str.strip(), inline=True)
        if servicos_str: embed.add_field(name="--- ⚖️ Serviços ---", value=servicos_str.strip(), inline=True)

        # --- SEÇÃO DE MELHORIA NO FINAL ---
        if construcao_andamento:
            building_id = construcao_andamento['id_construcao']
            building_info = CONSTRUCOES.get(building_id)
            if building_info:
                nivel_alvo = construcao_andamento['nivel_alvo']
                termina_em = construcao_andamento['termina_em']
                timestamp = int(termina_em.timestamp())
                melhoria_str = (
                    f"{building_info['emoji']} **{building_info['nome']}** para o **Nível {nivel_alvo}**\n"
                    f"**Conclusão:** <t:{timestamp}:R>"
                )
                embed.add_field(name="--- 🏗️ MELHORIA EM ANDAMENTO 🏗️ ---", value=melhoria_str, inline=False)
        
        await interaction.followup.send(embed=embed, ephemeral=True)
        
        
    @app_commands.command(name="governar", description="Funde a cidade ou abre o painel de governo.")
    async def governar(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        cidade_id = str(interaction.guild.id)
        cidade_ref = db.collection('cidades').document(cidade_id)
        cidade_doc = cidade_ref.get()

        if not cidade_doc.exists:
            if not interaction.user.guild_permissions.administrator:
                await interaction.followup.send("❌ Apenas um Administrador do servidor pode fundar uma nova cidade.", ephemeral=True)
                return
            
            user_game_id = get_player_game_id(str(interaction.user.id))
            if not user_game_id:
                await interaction.followup.send("❌ Você precisa se registrar com `/registrar` primeiro para fundar uma cidade.", ephemeral=True)
                return

            construcoes_iniciais = {}
            for building_id in CONSTRUCOES.keys():
                if building_id in ["CENTRO_VILA", "MINA", "FLORESTA"]:
                    construcoes_iniciais[building_id] = {"nivel": 1}
                else:
                    construcoes_iniciais[building_id] = {"nivel": 0}
            
            cidade_data = {
                "nome": interaction.guild.name, "descricao": "Uma cidade pronta para crescer.",
                "construcoes": construcoes_iniciais, "governador_id": user_game_id,
                "tesouro": {"MOEDAS": 1000}, "vice_governadores_ids": []
            }
            cidade_ref.set(cidade_data)
            await interaction.followup.send(f"✅ A cidade de **{interaction.guild.name}** foi fundada! Você é o(a) novo(a) Governador(a)!", ephemeral=True)
        else:
            user_game_id = get_player_game_id(str(interaction.user.id))
            if not user_game_id:
                await interaction.followup.send("❌ Você precisa estar registrado no jogo para governar.", ephemeral=True)
                return

            cidade_data = cidade_doc.to_dict()
            governador_id = cidade_data.get('governador_id')
            vice_ids = cidade_data.get('vice_governadores_ids', [])
            is_governor = user_game_id == governador_id
            is_vice = user_game_id in vice_ids

            if is_governor or is_vice:
                # --- CORREÇÃO APLICADA AQUI ---
                # O embed agora é criado com a lista de construções.
                embed = discord.Embed(
                    title=f"Painel de Governo de {cidade_data['nome']}", 
                    description="Visão geral da cidade e ações de governo.", 
                    color=discord.Color.gold()
                )
                
                # Lógica para mostrar as construções (igual ao /cidade)
                construcoes_str = ""
                construcoes_data = cidade_data.get('construcoes', {})
                for building_id, building_info in CONSTRUCOES.items():
                    if building_id in construcoes_data:
                        nivel = construcoes_data[building_id].get('nivel', 0)
                        emoji = building_info.get('emoji', '')
                        nome = building_info.get('nome', building_id)
                        nivel_str = f"Nível {nivel}" if nivel > 0 else "*(Não Construído)*"
                        construcoes_str += f"{emoji} **{nome}** - {nivel_str}\n"
                
                if not construcoes_str:
                    construcoes_str = "Nenhuma construção registrada."

                embed.add_field(name="Status das Construções", value=construcoes_str, inline=False)
                
                view = GovernarPanelView(author=interaction.user, bot=self.bot, cidade_data=cidade_data, is_governor=is_governor)
                await interaction.followup.send(embed=embed, view=view, ephemeral=True)
            else:
                await interaction.followup.send("❌ Apenas o governador ou um vice-governador pode usar este painel.", ephemeral=True)
                
    # --- NOVO TRATADOR DE ERROS AQUI ---
    @governar.error
    async def governar_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        # Verifica se o erro foi especificamente por falta de permissão
        if isinstance(error, app_commands.errors.MissingPermissions):
            # A interação ainda não foi respondida, então usamos response.send_message
            await interaction.response.send_message(
                "❌ Você precisa ser um **Administrador** do servidor para usar este comando.", 
                ephemeral=True
            )
        else:
            # Para outros erros inesperados
            # Se a interação já foi 'deferida', tentamos 'followup', senão 'response'
            content = f"Ocorreu um erro inesperado: {error}"
            if interaction.response.is_done():
                await interaction.followup.send(content, ephemeral=True)
            else:
                await interaction.response.send_message(content, ephemeral=True)
            # Também é uma boa ideia logar o erro completo no console para você ver
            print(f"Erro no comando /governar: {error}")
        

async def setup(bot: commands.Bot):
    await bot.add_cog(MundoCog(bot))