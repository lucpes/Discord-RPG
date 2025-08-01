# utils/converters.py

import discord
from firebase_config import db

async def find_player_by_game_id(ctx_or_inter, game_id: int):
    """
    Encontra um jogador pelo seu ID de Jogo.
    Funciona tanto com Context (ctx) de comandos de prefixo
    quanto com Interaction (inter) de comandos de barra.
    """
    # --- LÓGICA CORRIGIDA AQUI ---
    # Pega o bot, seja de um ctx ou de uma interaction
    bot = getattr(ctx_or_inter, 'bot', getattr(ctx_or_inter, 'client', None))
    if not bot:
        # Isso não deve acontecer, mas é uma salvaguarda
        return None, None

    query = db.collection('players').where('game_id', '==', game_id).limit(1).stream()
    
    player_doc = next(query, None)
    if not player_doc:
        return None, None

    discord_id_str = player_doc.id
    try:
        # Usa o bot que encontramos para buscar o usuário
        user = await bot.fetch_user(int(discord_id_str))
        return user, discord_id_str
    except discord.NotFound:
        return None, discord_id_str # Retorna o ID do Discord mesmo se o usuário não for encontrado
    except Exception as e:
        print(f"Erro ao buscar usuário {discord_id_str}: {e}")
        return None, discord_id_str


def get_player_game_id(user_id: str) -> int | None:
    """Busca o game_id de um jogador a partir do seu discord_id."""
    player_ref = db.collection('players').document(user_id)
    player_doc = player_ref.get()
    if player_doc.exists:
        return player_doc.to_dict().get('game_id')
    return None