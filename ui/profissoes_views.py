# ui/profissoes_views.py
import discord
from discord import ui
from data.profissoes_library import PROFISSOES, ORDERED_PROFS

def criar_barra_xp(atual, maximo, tamanho=10):
    if maximo <= 0: maximo = 1
    percentual = atual / maximo
    cheios = round(percentual * tamanho)
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
                
                xp_necessario = "Máximo"
                if nivel_atual <= len(prof_info['niveis']):
                    xp_necessario = prof_info['niveis'][nivel_atual - 1].get('xp_para_upar', float('inf'))
                
                barra = criar_barra_xp(xp_atual, xp_necessario if isinstance(xp_necessario, int) else 1)
                xp_str = f"`{xp_atual:,}/{xp_necessario if isinstance(xp_necessario, str) else f'{xp_necessario:,}'}`"
                
                embed.add_field(
                    name=f"{prof_info['emoji']} {prof_info['nome']} - Nível {nivel_atual}",
                    value=f"{barra} {xp_str}",
                    inline=False
                )
        else:
            # --- TELA DE DETALHES COM CAMPOS SEPARADOS ---
            prof_info = PROFISSOES.get(self.selected_prof)
            if not prof_info:
                self.selected_prof = None
                return self.create_embed()

            prof_data = self.char_data.get('profissoes', {}).get(self.selected_prof, {"nivel": 1, "xp": 0})
            nivel_atual = prof_data['nivel']
            xp_atual = prof_data['xp']

            embed.title = f"{prof_info['emoji']} Profissão: {prof_info['nome']} - Nível {nivel_atual}"
            embed.description = f"*{prof_info['descricao']}*"

            # Recompensas já desbloqueadas (apenas bónus)
            if nivel_atual > 1:
                recompensas_passadas = prof_info['niveis'][nivel_atual - 2]['recompensas']
                if passivas := recompensas_passadas.get('passivas'):
                    passivas_str = "\n".join([f"• `{stat.replace('_', ' ').capitalize()}: +{val}`" for stat, val in passivas.items()])
                    embed.add_field(name="Bónus Passivos Ativos", value=passivas_str, inline=False)
            
            # Recompensas para o próximo nível
            if nivel_atual <= len(prof_info['niveis']):
                recompensas_futuras = prof_info['niveis'][nivel_atual - 1]['recompensas']
                xp_necessario = prof_info['niveis'][nivel_atual - 1]['xp_para_upar']
                
                if passivas := recompensas_futuras.get('passivas'):
                    passivas_str = "\n".join([f"• `{stat.replace('_', ' ').capitalize()}: +{val}`" for stat, val in passivas.items()])
                    embed.add_field(name=f"⏫ Bónus do Próximo Nível ({nivel_atual + 1})", value=passivas_str, inline=False)

                if desbloqueios := recompensas_futuras.get('desbloqueios'):
                    desbloqueios_str = "\n".join([f"• `{desc}`" for desc in desbloqueios])
                    embed.add_field(name="⏫ Desbloqueios do Próximo Nível", value=desbloqueios_str, inline=False)

                embed.set_footer(text=f"XP para o próximo nível: {xp_atual:,}/{xp_necessario:,}")
            else:
                embed.add_field(name="🏆 Nível Máximo Alcançado", value="Você atingiu o nível máximo nesta profissão.", inline=False)

        return embed