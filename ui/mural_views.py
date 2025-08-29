# ui/mural_views.py
import discord
from discord import ui
import math
from datetime import datetime, timedelta, timezone

from firebase_config import db
from firebase_admin import firestore

from data.mural_library import CONTRATOS
from data.monstros_library import MONSTROS
from cogs.mundo_cog import BattleView # Importamos a BattleView
from utils.character_helpers import load_player_sheet
from game.stat_calculator import calcular_stats_completos
from data.classes_data import CLASSES_DATA
from utils.storage_helper import get_signed_url

class MuralView(ui.View):
    def __init__(self, author: discord.User, bot, char_data: dict, contratos_disponiveis: list):
        super().__init__(timeout=300)
        self.author = author
        self.bot = bot
        self.char_data = char_data
        self.contratos_disponiveis = contratos_disponiveis
        
        self.items_per_page = 3
        self.current_page = 1
        self.total_pages = max(1, math.ceil(len(self.contratos_disponiveis) / self.items_per_page))
        
        self.update_view()

    def update_view(self):
        """Reconstrói os botões e o embed para a página atual."""
        self.clear_items()
        
        start_index = (self.current_page - 1) * self.items_per_page
        end_index = start_index + self.items_per_page
        contratos_na_pagina = self.contratos_disponiveis[start_index:end_index]

        for contrato_id, contrato_data in contratos_na_pagina:
            monstro_info = MONSTROS.get(contrato_data['monstro_id'], {})
            label = f"Caçar {monstro_info.get('nome', 'Monstro Desconhecido')}"
            
            botao = ui.Button(label=label, style=discord.ButtonStyle.secondary, custom_id=contrato_id, emoji=monstro_info.get('emoji'))
            botao.callback = self.on_accept_contract
            self.add_item(botao)
            
        # Botões de paginação
        prev_button = ui.Button(label="⬅️", custom_id="prev_page", disabled=(self.current_page == 1), row=2)
        next_button = ui.Button(label="➡️", custom_id="next_page", disabled=(self.current_page >= self.total_pages), row=2)
        
        prev_button.callback = self.on_page_change
        next_button.callback = self.on_page_change
        
        self.add_item(prev_button)
        self.add_item(next_button)

    async def on_page_change(self, interaction: discord.Interaction):
        custom_id = interaction.data['custom_id']
        if custom_id == "prev_page": self.current_page -= 1
        else: self.current_page += 1
        
        self.update_view()
        await interaction.response.edit_message(embed=self.create_embed(), view=self)

    def create_embed(self) -> discord.Embed:
        """Cria o embed com a lista de contratos da página atual."""
        # --- CORREÇÃO APLICADA AQUI ---
        embed = discord.Embed(title="📜 Mural de Contratos da Cidade", description="Escolha uma caçada para iniciar.", color=discord.Color.dark_green())
        
        start_index = (self.current_page - 1) * self.items_per_page
        end_index = start_index + self.items_per_page
        contratos_na_pagina = self.contratos_disponiveis[start_index:end_index]
        
        if not contratos_na_pagina:
            embed.description = "Não há contratos disponíveis para o seu nível no momento."
            
        for contrato_id, contrato_data in contratos_na_pagina:
            monstro_info = MONSTROS.get(contrato_data['monstro_id'], {})
            recompensas = contrato_data['recompensas_extras']
            custo = contrato_data.get('custo', 0)
            
            valor_field = (
                f"**Recompensa Extra:** {recompensas.get('moedas', 0)}🪙 e {recompensas.get('xp', 0)} XP\n"
                f"**Custo:** {'GRÁTIS' if custo == 0 else f'{custo}🪙'}\n"
                f"**Espera:** {int(contrato_data['cooldown_s'] / 60)} minutos"
            )
            embed.add_field(
                name=f"{monstro_info.get('emoji', '❓')} {monstro_info.get('nome')} - (Nível {contrato_data['nivel_requerido']})",
                value=valor_field,
                inline=False
            )
        
        embed.set_footer(text=f"Página {self.current_page}/{self.total_pages}")
        return embed

    async def on_accept_contract(self, interaction: discord.Interaction):
        """Callback para quando o jogador aceita um contrato."""
        await interaction.response.defer()
        user_id_str = str(self.author.id)
        char_ref = db.collection('characters').document(user_id_str)
        char_data_atual = char_ref.get().to_dict()
        
        contrato_id = interaction.data['custom_id']
        contrato_data = CONTRATOS[contrato_id]

        # 1. VERIFICAÇÃO DE TEMPO DE ESPERA (COOLDOWN)
        ultimo_contrato = char_data_atual.get('ultimo_contrato_mural', {}).get('timestamp')
        if ultimo_contrato:
            tempo_passado = datetime.now(timezone.utc) - ultimo_contrato
            cooldown = timedelta(seconds=contrato_data['cooldown_s'])
            if tempo_passado < cooldown:
                tempo_restante = cooldown - tempo_passado
                return await interaction.followup.send(f"❌ Você precisa esperar mais `{str(tempo_restante).split('.')[0]}` para aceitar um novo contrato.", ephemeral=True)

        # 2. VERIFICAÇÃO DE CUSTO
        custo = contrato_data.get('custo', 0)
        if char_data_atual.get('moedas', 0) < custo:
            return await interaction.followup.send(f"❌ Você não tem moedas suficientes! Custa {custo}🪙 para aceitar.", ephemeral=True)
            
        # 3. ATUALIZA O ESTADO DO JOGADOR
        batch = db.batch()
        if custo > 0:
            batch.update(char_ref, {'moedas': firestore.Increment(-custo)})
        batch.update(char_ref, {'ultimo_contrato_mural': {'timestamp': firestore.SERVER_TIMESTAMP}})
        batch.commit()

        # --- 4. PREPARA E INICIA A BATALHA (LÓGICA CORRIGIDA) ---
        
        # Carrega a ficha completa do jogador, incluindo itens e dados do player
        sheet = load_player_sheet(user_id_str)
        
        # Calcula os status finais com base nos equipamentos
        stats_completos = calcular_stats_completos(sheet['char_data'], sheet['equipped_items'])
        
        # Garante que a vida e mana atuais não ultrapassem o máximo
        vida_maxima_final = stats_completos.get('VIDA_MAXIMA', 100)
        mana_maxima_final = stats_completos.get('MANA_MAXIMA', 100)
        vida_atual_corrigida = min(sheet['char_data'].get('vida_atual', vida_maxima_final), vida_maxima_final)
        mana_atual_corrigida = min(sheet['char_data'].get('mana_atual', mana_maxima_final), mana_maxima_final)
        
        # Pega a imagem de combate da classe
        classe_info = CLASSES_DATA.get(sheet['char_data'].get('classe'), {})
        combat_path = classe_info.get('combat_image_path')
        combat_url = get_signed_url(combat_path) if combat_path else None
        
        # Monta o dicionário completo do jogador, no formato que a BattleView espera
        jogadores_para_batalha = [{
            "id": self.author.id,
            "nick": sheet['player_data'].get('nick'),
            "stats": stats_completos,
            "vida_atual": vida_atual_corrigida,
            "mana_atual": mana_atual_corrigida,
            "habilidades_equipadas": sheet['char_data'].get('habilidades_equipadas', []),
            "classe": sheet['char_data'].get('classe'),
            "imagem_url": combat_url,
            "efeitos_ativos": []
        }]
        
        monstro_template = MONSTROS[contrato_data['monstro_id']].copy()
        monstros_para_batalha = [{**monstro_template, "id": contrato_data['monstro_id'], "vida_atual": monstro_template['stats']['VIDA_MAXIMA'], "efeitos_ativos": []}]
        
        battle_view = BattleView(
            bot=self.bot,
            jogadores_data=jogadores_para_batalha,
            monstros_data=monstros_para_batalha,
            recompensas_extras=contrato_data['recompensas_extras']
        )

        await interaction.edit_original_response(content="⚔️ Batalha iniciada!", view=None, embed=None)
        battle_view.message = await interaction.original_response()
        await battle_view.iniciar_batalha()