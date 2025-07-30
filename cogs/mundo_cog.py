# cogs/mundo_cog.py
import discord
import random
import asyncio
from discord import app_commands
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