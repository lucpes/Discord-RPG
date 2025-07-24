# utils/converters.py
import discord
from discord.ext import commands
from firebase_config import db

async def find_player_by_game_id(ctx: commands.Context, game_id: int):
    """
    Busca um jogador no Firebase pelo ID do jogo e retorna o objeto Member do Discord.
    Retorna (discord.Member, discord_id_str) ou (None, None) se não encontrar.
    """
    players_ref = db.collection('players').where('game_id', '==', game_id).limit(1).stream()
    
    player_doc = None
    for doc in players_ref:
        player_doc = doc
        break

    if not player_doc:
        return None, None
        
    discord_id_str = player_doc.id
    member = None # Inicia a variável como None

    # --- CORREÇÃO AQUI ---
    # Primeiro, verifica se o comando foi usado em um servidor (guild).
    if ctx.guild:
        # Se sim, tenta encontrar o membro no cache do servidor (operação rápida).
        member = ctx.guild.get_member(int(discord_id_str))
    
    # Se não encontrou o membro no servidor (ou se o comando foi em DM),
    # usa o método fetch_user, que faz uma busca global na API do Discord.
    if not member:
        try:
            member = await ctx.bot.fetch_user(int(discord_id_str))
        except discord.NotFound:
            return None, None

    return member, discord_id_str