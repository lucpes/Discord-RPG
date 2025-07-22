import discord
from discord import app_commands
from discord.ext import commands

# Importa as classes do nosso jogo
from game.personagem import Personagem 
# Vamos precisar de um gerenciador para salvar e carregar os dados (faremos depois)
# from game.game_manager import GameManager

# game_manager = GameManager() # Instância única do nosso gerenciador

class PersonagemComandos(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # Comando para criar um personagem
    @app_commands.command(name="criar_personagem", description="Cria seu personagem no mundo do RPG.")
    @app_commands.describe(nome="O nome que seu personagem terá.")
    async def criar_personagem(self, interaction: discord.Interaction, nome: str):
        # LÓGICA DO JOGO (aqui é onde a mágica acontece):
        # 1. Verificar se o jogador já tem um personagem (usando o game_manager)
        # 2. Se não tiver, criar um novo objeto Personagem
        #    novo_personagem = Personagem(user_id=interaction.user.id, nome=nome)
        # 3. Salvar o personagem (usando o game_manager)
        
        # Por enquanto, vamos só simular:
        novo_personagem = Personagem(user_id=interaction.user.id, nome=nome)
        
        embed = discord.Embed(
            title="🎉 Personagem Criado com Sucesso! 🎉",
            description=f"Bem-vindo ao nosso mundo, **{nome}**!",
            color=discord.Color.green()
        )
        embed.add_field(name="Seus Atributos Iniciais", value=str(novo_personagem))
        
        await interaction.response.send_message(embed=embed)


    # Comando de perfil
    @app_commands.command(name="perfil", description="Mostra as informações do seu personagem.")
    async def perfil(self, interaction: discord.Interaction):
         # LÓGICA DO JOGO:
         # 1. Buscar o personagem do jogador (usando o game_manager)
         # 2. Se não existir, mandar uma mensagem pedindo para criar um
         # 3. Se existir, criar o embed com as informações
        
         # Simulação:
         personagem_mock = Personagem(user_id=interaction.user.id, nome="Herói de Teste")
         personagem_mock.nivel = 5
         personagem_mock.hp_atual = 30
         personagem_mock.hp_max = 120
         
         embed = discord.Embed(
            title=f"Perfil de {personagem_mock.nome}",
            description="Suas estatísticas atuais.",
            color=interaction.user.color
         )
         embed.set_thumbnail(url=interaction.user.display_avatar.url)
         embed.add_field(name="Atributos", value=str(personagem_mock), inline=False)
         
         await interaction.response.send_message(embed=embed)


# Função obrigatória para que o bot possa carregar este Cog
async def setup(bot: commands.Bot):
    await bot.add_cog(PersonagemComandos(bot))