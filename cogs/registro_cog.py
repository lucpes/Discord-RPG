# cogs/registro_cog.py
import discord
from discord import app_commands
from discord.ext import commands
from firebase_admin import firestore

from firebase_config import db

class RegistroCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="registrar", description="Registre-se no jogo para começar sua aventura.")
    @app_commands.describe(nick="O nome de usuário que você usará no jogo.")
    async def registrar(self, interaction: discord.Interaction, nick: str):
        # (Cole aqui o código do comando /registrar, sem alterações)
        user_id_str = str(interaction.user.id)
        player_ref = db.collection('players').document(user_id_str)
        if player_ref.get().exists:
            await interaction.response.send_message("Você já está registrado!", ephemeral=True)
            return
        counter_ref = db.collection('game_counters').document('player_id')
        @firestore.transactional
        def get_and_increment_id(transaction):
            snapshot = counter_ref.get(transaction=transaction)
            if not snapshot.exists:
                new_id = 1000
                transaction.set(counter_ref, {'last_id': new_id})
            else:
                last_id = snapshot.to_dict().get('last_id', 999)
                new_id = last_id + 1
                transaction.update(counter_ref, {'last_id': new_id})
            return new_id
        transaction = db.transaction()
        game_id = get_and_increment_id(transaction)
        player_ref.set({'nick': nick, 'game_id': game_id})
        await interaction.response.send_message(
            f"🎉 Bem-vindo(a) ao jogo, **{nick}**! Seu registro foi concluído.\n"
            f"Seu ID de jogador único é: `{game_id}`.\n"
            "Agora use `/perfil` para criar seu primeiro personagem!",
            ephemeral=True
        )

async def setup(bot: commands.Bot):
    await bot.add_cog(RegistroCog(bot))