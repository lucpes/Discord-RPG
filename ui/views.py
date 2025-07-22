# ui/views.py
import discord

# Importa os dados e a conexão com o banco que as Views precisam
from data.classes_data import CLASSES_DATA, ORDERED_CLASSES
from firebase_config import db

class ClasseSelectionView(discord.ui.View):
    def __init__(self, user: discord.User):
        super().__init__(timeout=300)
        self.user = user
        self.current_class_index = 0

    # (Cole aqui o resto do código da ClasseSelectionView, sem alterações)
    # ...
    def create_embed(self):
        class_name = ORDERED_CLASSES[self.current_class_index]
        classe_atual = CLASSES_DATA[class_name]
        embed = discord.Embed(
            title=f"Escolha sua Classe: {class_name}",
            description=f"**Estilo:** {classe_atual['estilo']}",
            color=discord.Color.blue()
        )
        embed.set_image(url=classe_atual['image_url'])
        embed.add_field(name="⚔️ Habilidades Iniciais", value="- " + "\n- ".join(classe_atual['habilidades']), inline=True)
        embed.add_field(name="🌟 Evoluções Possíveis", value="- " + "\n- ".join(classe_atual['evolucoes']), inline=True)
        embed.set_footer(text=f"Classe {self.current_class_index + 1}/{len(ORDERED_CLASSES)}")
        return embed

    async def update_message(self, interaction: discord.Interaction):
        embed = self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="⬅️ Anterior", style=discord.ButtonStyle.secondary)
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("Você não pode interagir com o menu de outra pessoa!", ephemeral=True)
            return
        self.current_class_index = (self.current_class_index - 1) % len(ORDERED_CLASSES)
        await self.update_message(interaction)

    @discord.ui.button(label="✅ Selecionar", style=discord.ButtonStyle.success)
    async def select_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("Você não pode interagir com o menu de outra pessoa!", ephemeral=True)
            return

        for item in self.children:
            item.disabled = True

        class_name = ORDERED_CLASSES[self.current_class_index]
        selected_class = CLASSES_DATA[class_name]
        
        # Default criação do personagem inicial
        
        char_ref = db.collection('characters').document(str(interaction.user.id))
        char_ref.set({
            'classe': class_name,
            'nivel': 1,
            'xp': 0,
            'moedas': 100,
            'banco': 0,
            'diamantes': 5,
            'habilidades_equipadas': selected_class['habilidades']
        })

        final_embed = self.create_embed()
        final_embed.title = f"✅ Classe Selecionada: {class_name}"
        final_embed.color = discord.Color.green()
        final_embed.description = f"Parabéns, {interaction.user.mention}! Você iniciou sua jornada como um(a) **{class_name}**."
        
        await interaction.response.edit_message(embed=final_embed, view=self)
        self.stop()

    @discord.ui.button(label="Próximo ➡️", style=discord.ButtonStyle.secondary)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("Você não pode interagir com o menu de outra pessoa!", ephemeral=True)
            return
        self.current_class_index = (self.current_class_index + 1) % len(ORDERED_CLASSES)
        await self.update_message(interaction)


class PerfilView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    # (Cole aqui o resto do código da PerfilView, sem alterações)
    @discord.ui.button(label="Inventário", style=discord.ButtonStyle.secondary, emoji="🎒")
    async def inventario(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("O inventário será implementado em breve!", ephemeral=True)

    @discord.ui.button(label="Habilidades", style=discord.ButtonStyle.secondary, emoji="⚔️")
    async def habilidades(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("A árvore de habilidades será implementada em breve!", ephemeral=True)

    @discord.ui.button(label="Talentos", style=discord.ButtonStyle.secondary, emoji="🌟")
    async def talentos(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Os talentos de classe serão implementados em breve!", ephemeral=True)