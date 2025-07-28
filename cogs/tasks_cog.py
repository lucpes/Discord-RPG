# cogs/tasks_cog.py
from discord.ext import commands, tasks
from firebase_config import db
from firebase_admin import firestore
from datetime import datetime, timezone
from data.construcoes_library import CONSTRUCOES

class TasksCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Inicia a tarefa assim que o Cog é carregado
        self.check_constructions.start()

    def cog_unload(self):
        # Garante que a tarefa seja cancelada se o Cog for descarregado
        self.check_constructions.cancel()

    @tasks.loop(minutes=1.0) # Define que o loop rodará a cada 1 minuto
    async def check_constructions(self):
        """Verifica no Firebase se alguma construção terminou e atualiza os dados."""
        
        # Pega o horário atual com fuso horário UTC para comparação segura
        now = datetime.now(timezone.utc)
        
        # Esta é a consulta otimizada:
        # 1. Pega cidades que TENHAM uma construção em andamento.
        # 2. Dessas, pega apenas aquelas cujo tempo de término JÁ PASSOU.
        query = db.collection('cidades').where(
            'construcao_em_andamento.termina_em', '<=', now
        )
        
        docs_finalizados = query.stream()

        for doc in docs_finalizados:
            try:
                cidade_data = doc.to_dict()
                construcao_info = cidade_data.get('construcao_em_andamento')
                
                if not construcao_info:
                    continue

                cidade_ref = doc.reference
                building_id = construcao_info['id_construcao']
                nivel_alvo = construcao_info['nivel_alvo']

                # Atualiza o nível da construção no Firebase
                update_path = f"construcoes.{building_id}.nivel"
                cidade_ref.update({
                    update_path: nivel_alvo,
                    # Remove o campo 'construcao_em_andamento', indicando que não há mais nada construindo.
                    'construcao_em_andamento': firestore.DELETE_FIELD 
                })
                
                print(f"✅ Construção '{building_id}' na cidade '{cidade_data['nome']}' (ID: {doc.id}) concluída!")

                # Futuramente, aqui você pode adicionar uma lógica para anunciar a conclusão no Discord.

            except Exception as e:
                print(f"❌ Erro ao processar construção finalizada para a cidade {doc.id}: {e}")

    @check_constructions.before_loop
    async def before_check_constructions(self):
        """Função especial que garante que o loop só comece depois que o bot estiver 100% online."""
        print("Aguardando o bot ficar pronto para iniciar o loop de tarefas...")
        await self.bot.wait_until_ready()
        print("Loop de tarefas iniciado.")

# Função obrigatória para que o bot possa carregar este Cog
async def setup(bot: commands.Bot):
    await bot.add_cog(TasksCog(bot))