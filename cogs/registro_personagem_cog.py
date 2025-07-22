# cogs/registro_personagem_cog.py
import discord
from discord import app_commands
from discord.ext import commands
from firebase_admin import firestore

# Importa a nossa instância do banco de dados
from firebase_config import db

# --- DADOS DAS CLASSES (Nossos "Templates") ---
# Colocamos aqui para fácil acesso. No futuro, isso poderia vir de um arquivo JSON.
# IMPORTANTE: Substitua os 'image_url' por links de imagens reais para cada classe.
CLASSES_DATA = [
    {
        "nome": "Guerreiro",
        "estilo": "Combatente corpo a corpo robusto, mestre em defesa e ataque com armas pesadas.",
        "evolucoes": ["Paladino", "Berserker"],
        "habilidades": ["Golpe Poderoso", "Bloqueio com Escudo", "Grito de Guerra"],
        "image_url": "https://i.imgur.com/VYXEo2n.jpeg"
    },
    {
        "nome": "Anão",
        "estilo": "Resistente e forte, especialista em forja e combate com machados e martelos.",
        "evolucoes": ["Guardião da Montanha", "Mestre das Runas"],
        "habilidades": ["Golpe de Martelo", "Pele de Pedra", "Arremesso de Machado"],
        "image_url": "https://i.imgur.com/imuCcO9.jpeg"
    },
    {
        "nome": "Arqueira",
        "estilo": "Atiradora de longa distância, ágil e precisa, que domina o campo de batalha de longe.",
        "evolucoes": ["Caçadora de Feras", "Sombra Silenciosa"],
        "habilidades": ["Flecha Precisa", "Chuva de Flechas", "Salto para Trás"],
        "image_url": "https://i.imgur.com/CgR6gED.png"
    },
    {
        "nome": "Mago",
        "estilo": "Conjurador de poderosas magias arcanas que manipulam os elementos para causar dano em área.",
        "evolucoes": ["Arquimago", "Bruxo"],
        "habilidades": ["Bola de Fogo", "Raio Congelante", "Barreira Mágica"],
        "image_url": "https://i.imgur.com/QJKAQ0u.png"
    },
    {
        "nome": "Curadora",
        "estilo": "Suporte vital para qualquer grupo, capaz de curar ferimentos e conceder bênçãos divinas.",
        "evolucoes": ["Sacerdotisa", "Druida"],
        "habilidades": ["Toque Curativo", "Bênção de Proteção", "Luz Sagrada"],
        "image_url": "https://i.imgur.com/k9408II.jpeg"
    },
    {
        "nome": "Assassino",
        "estilo": "Mestre da furtividade e dos golpes críticos, que elimina alvos importantes rapidamente.",
        "evolucoes": ["Ladrão das Sombras", "Duelista"],
        "habilidades": ["Ataque Furtivo", "Lançar Adaga Envenenada", "Desaparecer"],
        "image_url": "https://i.imgur.com/I8PUtxj.png"
    },
    {
        "nome": "Goblin",
        "estilo": "Engenhoso e caótico, usa truques sujos e invenções instáveis para superar os inimigos.",
        "evolucoes": ["Engenhoqueiro", "Trapaceiro"],
        "habilidades": ["Bomba Improvisada", "Golpe Baixo", "Fingir de Morto"],
        "image_url": "https://i.imgur.com/xHSM29c.png"
    },
]

# --- A VIEW INTERATIVA PARA SELEÇÃO DE CLASSE ---

class ClasseSelectionView(discord.ui.View):
    def __init__(self, user: discord.User):
        super().__init__(timeout=300)  # Timeout de 5 minutos
        self.user = user
        self.current_class_index = 0

    def create_embed(self):
        """Cria o embed com base na classe atual."""
        classe_atual = CLASSES_DATA[self.current_class_index]
        embed = discord.Embed(
            title=f"Escolha sua Classe: {classe_atual['nome']}",
            description=f"**Estilo:** {classe_atual['estilo']}",
            color=discord.Color.blue()
        )
        embed.set_image(url=classe_atual['image_url'])
        embed.add_field(
            name="⚔️ Habilidades Iniciais",
            value="- " + "\n- ".join(classe_atual['habilidades']),
            inline=True
        )
        embed.add_field(
            name="🌟 Evoluções Possíveis",
            value="- " + "\n- ".join(classe_atual['evolucoes']),
            inline=True
        )
        embed.set_footer(text=f"Classe {self.current_class_index + 1}/{len(CLASSES_DATA)}")
        return embed

    async def update_message(self, interaction: discord.Interaction):
        """Atualiza a mensagem original com o novo embed."""
        embed = self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="⬅️ Anterior", style=discord.ButtonStyle.secondary)
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("Você não pode interagir com o menu de outra pessoa!", ephemeral=True)
            return
            
        self.current_class_index = (self.current_class_index - 1) % len(CLASSES_DATA)
        await self.update_message(interaction)

    @discord.ui.button(label="✅ Selecionar", style=discord.ButtonStyle.success)
    async def select_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("Você não pode interagir com o menu de outra pessoa!", ephemeral=True)
            return

        # Desativa todos os botões para mostrar que a escolha foi feita
        for item in self.children:
            item.disabled = True

        selected_class = CLASSES_DATA[self.current_class_index]
        
        # Salva o personagem no Firebase
        char_ref = db.collection('characters').document(str(interaction.user.id))
        char_ref.set({
            'classe': selected_class['nome'],
            'nivel': 1,
            'xp': 0,
            # Adicione outros atributos iniciais aqui
        })

        final_embed = self.create_embed()
        final_embed.title = f"✅ Classe Selecionada: {selected_class['nome']}"
        final_embed.color = discord.Color.green()
        final_embed.description = f"Parabéns, {interaction.user.mention}! Você iniciou sua jornada como um(a) **{selected_class['nome']}**."
        
        await interaction.response.edit_message(embed=final_embed, view=self)
        self.stop()

    @discord.ui.button(label="Próximo ➡️", style=discord.ButtonStyle.secondary)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("Você não pode interagir com o menu de outra pessoa!", ephemeral=True)
            return
            
        self.current_class_index = (self.current_class_index + 1) % len(CLASSES_DATA)
        await self.update_message(interaction)


# --- O COG EM SI ---

class RegistroPersonagemCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="registrar", description="Registre-se no jogo para começar sua aventura.")
    @app_commands.describe(nick="O nome de usuário que você usará no jogo.")
    async def registrar(self, interaction: discord.Interaction, nick: str):
        user_id_str = str(interaction.user.id)
        player_ref = db.collection('players').document(user_id_str)

        if player_ref.get().exists:
            await interaction.response.send_message("Você já está registrado!", ephemeral=True)
            return

        # Transação para garantir que o ID seja único e atômico
        counter_ref = db.collection('game_counters').document('player_id')
        
        @firestore.transactional
        def get_and_increment_id(transaction):
            snapshot = counter_ref.get(transaction=transaction)
            if not snapshot.exists:
                # Se for o primeiro jogador, inicializa o contador
                new_id = 1000
                transaction.set(counter_ref, {'last_id': new_id})
            else:
                last_id = snapshot.to_dict().get('last_id', 999)
                new_id = last_id + 1
                transaction.update(counter_ref, {'last_id': new_id})
            return new_id

        transaction = db.transaction()
        game_id = get_and_increment_id(transaction)

        # Salva os dados do novo jogador
        player_ref.set({
            'nick': nick,
            'game_id': game_id
        })

        await interaction.response.send_message(
            f"🎉 Bem-vindo(a) ao jogo, **{nick}**! Seu registro foi concluído com sucesso.\n"
            f"Seu ID de jogador único é: `{game_id}`.\n"
            "Agora use `/perfil` para criar seu primeiro personagem!",
            ephemeral=True
        )

    @app_commands.command(name="perfil", description="Veja seu perfil ou crie um novo personagem.")
    async def perfil(self, interaction: discord.Interaction):
        user_id_str = str(interaction.user.id)
        
        # 1. Verifica se o jogador está registrado
        player_ref = db.collection('players').document(user_id_str)
        player_doc = player_ref.get()
        if not player_doc.exists:
            await interaction.response.send_message("Você ainda não está registrado. Use `/registrar` primeiro!", ephemeral=True)
            return

        # 2. Verifica se o jogador já tem um personagem
        char_ref = db.collection('characters').document(user_id_str)
        char_doc = char_ref.get()
        if char_doc.exists:
            # Lógica para mostrar o perfil existente (a ser implementada)
            player_data = player_doc.to_dict()
            char_data = char_doc.to_dict()
            await interaction.response.send_message(
                f"**Perfil de {player_data['nick']}**\n"
                f"**Classe:** {char_data['classe']}\n"
                f"**Nível:** {char_data['nivel']}\n"
                f"(Mais detalhes do perfil virão aqui...)",
                ephemeral=True
            )
        else:
            # 3. Se não tiver, inicia o fluxo de criação
            view = ClasseSelectionView(user=interaction.user)
            initial_embed = view.create_embed()
            await interaction.response.send_message(
                "Você ainda não tem um personagem. Vamos criar um agora! Escolha sua classe abaixo:",
                embed=initial_embed,
                view=view,
                ephemeral=True
            )


# Função obrigatória para carregar o Cog
async def setup(bot: commands.Bot):
    await bot.add_cog(RegistroPersonagemCog(bot))