# utils/converters.py
import discord
from discord.ext import commands
from firebase_config import db

# --- FUNÇÃO CORRIGIDA ---
# Trocamos 'ctx' por 'interaction' para deixar claro o que a função espera
async def find_player_by_game_id(interaction: discord.Interaction, game_id: int):
    """
    Busca um jogador no Firebase pelo ID do jogo e retorna o objeto User/Member do Discord.
    Retorna (discord.User | discord.Member, discord_id_str) ou (None, None) se não encontrar.
    """
    players_ref = db.collection('players').where('game_id', '==', game_id).limit(1).stream()
    
    player_doc = None
    for doc in players_ref:
        player_doc = doc
        break

    if not player_doc:
        return None, None
        
    discord_id_str = player_doc.id
    user = None

    # Verifica se a interação aconteceu em um servidor para tentar pegar o 'member'
    if interaction.guild:
        user = interaction.guild.get_member(int(discord_id_str))
    
    # Se não encontrou (ou se foi em DM), busca globalmente
    if not user:
        try:
            # Usa interaction.client em vez de ctx.bot
            user = await interaction.client.fetch_user(int(discord_id_str))
        except discord.NotFound:
            return None, None

    return user, discord_id_str

def get_player_game_id(discord_id_str: str) -> int | None:
    """Busca no Firebase e retorna o ID de Jogo de um jogador."""
    player_ref = db.collection('players').document(discord_id_str)
    player_doc = player_ref.get()
    if player_doc.exists:
        return player_doc.to_dict().get('game_id')
    return None