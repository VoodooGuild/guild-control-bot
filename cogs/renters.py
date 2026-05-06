import discord
from discord.ext import commands
from discord import app_commands
from database import supabase
from datetime import datetime

class DaySelectionView(discord.ui.View):
    """View com botões para selecionar o dia APÓS o formulário"""
    def __init__(self, data):
        super().__init__(timeout=60)
        self.data = data
        self.days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        
        # Cria um botão para cada dia
        for day in self.days:
            button = discord.ui.Button(label=day, style=discord.Color.blurple(), custom_id=day)
            button.callback = self.make_callback(day)
            self.add_item(button)

    def make_callback(self, day):
        async def callback(interaction: discord.Interaction):
            self.data["due_day"] = day # Define o dia por último
            
            try:
                result = supabase.table("renters").insert(self.data).execute()
                if result.data:
                    embed = discord.Embed(title="✅ Renter Finalizado!", color=discord.Color.green())
                    embed.add_field(name="Player", value=self.data["ingame_name"])
                    embed.add_field(name="Fee", value=f"{int(self.data['weekly_fee']) // 1_000_000}M")
                    embed.add_field(name="Due Day", value=day)
                    await interaction.response.edit_message(content=None, embed=embed, view=None)
            except Exception as e:
                await interaction.response.send_message(f"❌ Erro ao salvar: {e}", ephemeral=True)
        return callback

class AddRenterModal(discord.ui.Modal, title="Novo Renter"):
    ingame_name = discord.ui.TextInput(label="In-Game Name", required=True)
    discord_id = discord.ui.TextInput(label="Discord ID", required=False)
    weekly_fee_input = discord.ui.TextInput(label="Weekly Fee (em Milhões)", placeholder="Ex: 14 para 14M", required=True)
    webhook_url = discord.ui.TextInput(label="Webhook URL", required=False)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            # Prepara os dados (sem o dia ainda)
            fee_value = int(self.weekly_fee_input.value) * 1_000_000
            data = {
                "ingame_name": self.ingame_name.value,
                "discord_id": self.discord_id.value if self.discord_id.value else None,
                "weekly_fee": fee_value,
                "webhook_url": self.webhook_url.value if self.webhook_url.value else None,
                "is_active": True
            }
            
            # Pergunta o dia APÓS preencher o modal
            view = DaySelectionView(data)
            await interaction.response.send_message(
                f"✅ Dados do **{self.ingame_name.value}** recebidos! \n📅 **Agora, selecione o dia de pagamento abaixo:**",
                view=view,
                ephemeral=True
            )
        except ValueError:
            await interaction.response.send_message("❌ A taxa deve ser um número inteiro.", ephemeral=True)

class Renters(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="add-renter", description="Adiciona um novo renter")
    async def add_renter(self, interaction: discord.Interaction):
        # Abre direto o modal sem pedir nada antes
        await interaction.response.send_modal(AddRenterModal())

async def setup(bot):
    await bot.add_cog(Renters(bot))
