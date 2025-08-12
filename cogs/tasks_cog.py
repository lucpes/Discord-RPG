# cogs/tasks_cog.py
import discord
from discord.ext import commands, tasks
from firebase_config import db
from firebase_admin import firestore
from datetime import datetime, timezone
from data.construcoes_library import CONSTRUCOES
from utils.notification_helper import send_dm

class TasksCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.check_constructions.start()
        self.check_player_actions.start()
        self.processar_renda_cidades.start()

    def cog_unload(self):
        self.check_constructions.cancel()
        self.check_player_actions.cancel()
        self.processar_renda_cidades.cancel()

    @tasks.loop(minutes=1.0)
    async def check_constructions(self):
        """Verifica construções da cidade finalizadas."""
        now = datetime.now(timezone.utc)
        query = db.collection('cidades').where('construcao_em_andamento.termina_em', '<=', now)
        docs_finalizados = query.stream()
        for doc in docs_finalizados:
            try:
                cidade_data = doc.to_dict()
                construcao_info = cidade_data.get('construcao_em_andamento')
                if not construcao_info: continue
                
                cidade_ref = doc.reference
                building_id = construcao_info['id_construcao']
                nivel_alvo = construcao_info['nivel_alvo']
                update_path = f"construcoes.{building_id}.nivel"
                
                cidade_ref.update({
                    update_path: nivel_alvo,
                    'construcao_em_andamento': firestore.DELETE_FIELD 
                })
                print(f"✅ Construção '{building_id}' na cidade '{cidade_data['nome']}' concluída!")
            except Exception as e:
                print(f"❌ Erro ao processar construção finalizada para a cidade {doc.id}: {e}")

    # --- MÉTODO ATUALIZADO PARA NOTIFICAR AMBAS AS PROFISSÕES ---
    @tasks.loop(minutes=1.0)
    async def check_player_actions(self):
        """Verifica se ações de jogadores (mineração, lenha, etc.) terminaram e os notifica."""
        now = datetime.now(timezone.utc)

        # Dicionário para mapear o campo do DB para o nome da profissão e emoji
        acoes_para_verificar = {
            "mineracao_ativa": {"nome": "Mineração", "emoji": "⛏️", "comando": "/mina"},
            "lenhador_ativo": {"nome": "Coleta de Lenha", "emoji": "🪓", "comando": "/floresta"}
        }

        for campo_db, info in acoes_para_verificar.items():
            query = db.collection('characters').where(
                f'{campo_db}.termina_em', '<=', now
            ).where(
                f'{campo_db}.notificado', '==', False
            )
            
            docs_finalizados = query.stream()

            for doc in docs_finalizados:
                try:
                    user_id_int = int(doc.id)
                    
                    embed = discord.Embed(
                        title=f"{info['emoji']} {info['nome']} Concluída!",
                        description=f"Sua extração de recursos foi finalizada!\nUse o comando `{info['comando']}` para coletar suas recompensas.",
                        color=discord.Color.green()
                    )
                    await send_dm(self.bot, user_id_int, embed)
                    
                    # Atualiza o campo de notificação correto
                    doc.reference.update({f'{campo_db}.notificado': True})

                except Exception as e:
                    print(f"❌ Erro ao processar notificação de {info['nome']} para o jogador {doc.id}: {e}")

    # --- TAREFA DE RENDA ATUALIZADA ---
    @tasks.loop(hours=24) # Alterado de 1 para 24 horas
    async def processar_renda_cidades(self):
        """Calcula e adiciona a renda passiva ao tesouro de todas as cidades, uma vez ao dia."""
        print(f"[{datetime.now()}] Iniciando ciclo de processamento de renda das cidades...")
        cidades_ref = db.collection('cidades').stream()
        for cidade_doc in cidades_ref:
            try:
                cidade_data = cidade_doc.to_dict()
                construcoes = cidade_data.get('construcoes', {})
                fazenda_data = construcoes.get('FAZENDA')
                if not fazenda_data or fazenda_data.get('nivel', 0) == 0:
                    continue

                nivel_fazenda = fazenda_data['nivel']
                regras_niveis_fazenda = CONSTRUCOES.get('FAZENDA', {}).get('niveis', [])
                if nivel_fazenda > len(regras_niveis_fazenda):
                    continue

                # Multiplica a renda por hora por 24 para obter a renda diária
                renda_diaria = regras_niveis_fazenda[nivel_fazenda - 1].get('renda', 0)
                
                if renda_diaria > 0:
                    cidade_doc.reference.update({'tesouro.MOEDAS': firestore.Increment(renda_diaria)})
                    print(f"  -> +{renda_diaria} moedas adicionadas ao tesouro de '{cidade_data.get('nome', cidade_doc.id)}'.")
            except Exception as e:
                print(f"❌ Erro ao processar renda da cidade {cidade_doc.id}: {e}")

    @check_constructions.before_loop
    @check_player_actions.before_loop
    @processar_renda_cidades.before_loop
    async def before_tasks(self):
        await self.bot.wait_until_ready()

async def setup(bot: commands.Bot):
    await bot.add_cog(TasksCog(bot))