# ui/profissoes_views.py
import discord
from discord import ui
from data.profissoes_library import PROFISSOES, ORDERED_PROFS

# --- FUNÇÃO CORRIGIDA ---
def criar_barra_xp(atual, maximo, tamanho=10):
    """Cria uma barra de progresso, garantindo que não ultrapasse o tamanho máximo."""
    if maximo <= 0: maximo = 1
    
    percentual = atual / maximo
    # Garante que o número de blocos cheios não passe do tamanho total da barra
    cheios = min(tamanho, round(percentual * tamanho))
    vazios = tamanho - cheios
    
    return f"`[{'█' * cheios}{'░' * vazios}]`"


class ProfissoesView(ui.View):
    def __init__(self, author: discord.User, char_data: dict):
        super().__init__(timeout=300)
        self.author = author
        self.char_data = char_data
        self.selected_prof = None
        self.add_item(self.create_prof_select())

    def create_prof_select(self) -> ui.Select:
        options = [discord.SelectOption(label="Todas as Profissões", value="all_profissoes", emoji="📜")]
        for prof_id, prof_info in PROFISSOES.items():
            options.append(discord.SelectOption(
                label=prof_info['nome'],
                value=prof_id,
                emoji=prof_info['emoji']
            ))
        select = ui.Select(placeholder="Selecione uma profissão para ver detalhes...", options=options)
        select.callback = self.on_prof_select
        return select

    async def on_prof_select(self, interaction: discord.Interaction):
        selected_value = interaction.data['values'][0]
        self.selected_prof = None if selected_value == "all_profissoes" else selected_value
        embed = self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    def create_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="🌟 Painel de Profissões",
            color=self.author.color
        )

        if not self.selected_prof:
            # --- TELA PRINCIPAL (VISÃO GERAL) ---
            embed.description = "Aqui você pode ver o progresso de todas as suas profissões.\nSelecione uma no menu abaixo para ver mais detalhes."

            for prof_id, prof_info in PROFISSOES.items():
                prof_data = self.char_data.get('profissoes', {}).get(prof_id, {"nivel": 1, "xp": 0})
                nivel_atual = prof_data['nivel']
                xp_atual = prof_data['xp']
                
                # --- LÓGICA DE EXIBIÇÃO CORRIGIDA PARA O NÍVEL MÁXIMO ---
                # Verifica se o nível atual ultrapassou os níveis definidos na biblioteca
                is_max_level = nivel_atual > len(prof_info['niveis'])
                
                if is_max_level:
                    barra = f"`[{'█' * 10}]`" # Barra sempre cheia
                    xp_str = "`Máximo`"      # Apenas o texto "Máximo"
                else:
                    xp_necessario = prof_info['niveis'][nivel_atual - 1].get('xp_para_upar', 1)
                    barra = criar_barra_xp(xp_atual, xp_necessario)
                    xp_str = f"`{xp_atual:,}/{xp_necessario:,}`"
                
                embed.add_field(
                    name=f"{prof_info['emoji']} {prof_info['nome']} - Nível {nivel_atual}",
                    value=f"{barra} {xp_str}",
                    inline=False
                )
        else:
            # --- TELA DE DETALHES COM O NOVO LAYOUT ---
            prof_info = PROFISSOES.get(self.selected_prof)
            if not prof_info:
                self.selected_prof = None
                return self.create_embed()

            prof_data = self.char_data.get('profissoes', {}).get(self.selected_prof, {"nivel": 1, "xp": 0})
            nivel_atual = prof_data['nivel']
            xp_atual = prof_data['xp']

            embed.title = f"{prof_info['emoji']} Profissão: {prof_info['nome']} - Nível {nivel_atual}"
            embed.description = f"*{prof_info['descricao']}*"

            # Adiciona a barra de XP como um campo próprio
            xp_necessario_str = "Máximo"
            if nivel_atual <= len(prof_info['niveis']):
                xp_necessario_int = prof_info['niveis'][nivel_atual - 1].get('xp_para_upar', 1)
                xp_necessario_str = f'{xp_necessario_int:,}'
                barra = criar_barra_xp(xp_atual, xp_necessario_int)
                embed.add_field(name="Progresso", value=f"{barra} `{xp_atual:,}/{xp_necessario_str}`", inline=False)
                
            # --- CORREÇÃO APLICADA AQUI ---
            def formatar_passivas(passivas_dict):
                """Formata os bónus passivos, convertendo para % quando necessário."""
                linhas = []
                for stat, val in passivas_dict.items():
                    # Verifica se o valor é um float entre 0 e 1 para formatar como percentagem
                    if isinstance(val, float) and 0 < val < 1:
                        val_str = f"+{val:.0%}"
                    else:
                        val_str = f"+{val}"
                    linhas.append(f"• `{stat.replace('_', ' ').capitalize()}: {val_str}`")
                return "\n".join(linhas)

            # --- CORREÇÃO 1: SOMA DOS BÓNUS ATIVOS ---
            if nivel_atual > 1:
                passivas_ativas_total = {}
                # Itera por todos os níveis já concluídos para somar os bónus
                for i in range(nivel_atual - 1):
                    recompensas_nivel = prof_info['niveis'][i].get('recompensas', {})
                    if passivas := recompensas_nivel.get('passivas'):
                        for stat_id, value in passivas.items():
                            passivas_ativas_total[stat_id] = passivas_ativas_total.get(stat_id, 0) + value
                
                if passivas_ativas_total:
                    # --- CORREÇÃO 2: FORMATAÇÃO DA PERCENTAGEM ---
                    passivas_str_list = []
                    for stat, val in passivas_ativas_total.items():
                        # Verifica se o valor é um float para formatar como percentagem
                        if isinstance(val, float) and 0 <= val <= 1:
                            val_str = f"+{val:.0%}"
                        else:
                            val_str = f"+{val}"
                        passivas_str_list.append(f"• `{stat.replace('_', ' ').capitalize()}: {val_str}`")
                    
                    embed.add_field(name="Bónus Passivos Ativos", value="\n".join(passivas_str_list), inline=False)
            
            # Recompensas para o próximo nível
            if nivel_atual <= len(prof_info['niveis']):
                recompensas_futuras = prof_info['niveis'][nivel_atual - 1]['recompensas']
                if passivas := recompensas_futuras.get('passivas'):
                    passivas_str = formatar_passivas(passivas)
                    embed.add_field(name=f"⏫ Recompensas do Próximo Nível ({nivel_atual + 1})", value=passivas_str, inline=False)
                
                #embed.add_field(name=f"⏫ Recompensas do Próximo Nível ({nivel_atual + 1})", value=recompensas_finais_str or "Nenhuma", inline=False)
            else:
                embed.add_field(name="🏆 Nível Máximo Alcançado", value="Você atingiu o nível máximo nesta profissão.", inline=False)

        return embed