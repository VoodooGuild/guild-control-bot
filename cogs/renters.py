import discord
from discord.ext import commands
from discord import app_commands
from database import supabase
from datetime import datetime

class AddRenterModal(discord.ui.Modal, title="Add Renter"):
    ingame_name = discord.ui.TextInput(
        label="In-Game Name",
        placeholder="Ex: PlayerXYZ",
        required=True,
        max_length=100
    )
    discord_id = discord.ui.TextInput(
        label="Discord ID",
        placeholder="Ex: 123456789012345678",
        required=False,
        max_length=30
    )
    weekly_fee = discord.ui.TextInput(
        label="Weekly Fee",
        placeholder="Ex: 5000000",
        required=True,
        max_length=20
    )
    due_day = discord.ui.TextInput(
        label="Due Day (1-7, where 1=Monday)",
        placeholder="Ex: 1",
        required=True,
        max_length=1
    )
    notes = discord.ui.TextInput(
        label="Notes (optional)",
        placeholder="Any notes about this renter",
        required=False,
        max_length=500,
        style=discord.TextStyle.paragraph
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        # 1. Validação do dia da semana
        try:
            due_day_int = int(self.due_day.value)
            if not 1 <= due_day_int <= 7:
                await interaction.followup.send("❌ Due day must be between 1 and 7.", ephemeral=True)
                return
        except ValueError:
            await interaction.followup.send("❌ Due day must be a number.", ephemeral=True)
            return

        # Conversão de Número (1-7) para Texto (Monday-Sunday) igual ao Painel Web
        days_map = {1: "Monday", 2: "Tuesday", 3: "Wednesday", 4: "Thursday", 5: "Friday", 6: "Saturday", 7: "Sunday"}
        due_day_str = days_map[due_day_int]

        # 2. Validação da taxa semanal (Prata não tem centavos, usar int)
        try:
            weekly_fee_int = int(self.weekly_fee.value)
        except ValueError:
            await interaction.followup.send("❌ Weekly fee must be a whole number (no decimals).", ephemeral=True)
            return

        # 3. Montando os dados para o Supabase
        data = {
            "ingame_name": self.ingame_name.value,
            "weekly_fee": weekly_fee_int,
            "due_day": due_day_str,
            "is_active": True,
            "notes": self.notes.value if self.notes.value else None,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }

        if self.discord_id.value:
            data["discord_id"] = self.discord_id.value

        # 4. Inserindo no Banco COM tratamento de erro (Proteção contra crashes)
        try:
            result = supabase.table("renters").insert(data).execute()
            
            # Se deu certo, monta o Embed
            embed = discord.Embed(
                title="✅ Renter Added!",
                color=discord.Color.green()
            )
            embed.add_field(name="In-Game Name", value=self.ingame_name.value, inline=True)
            embed.add_field(name="Weekly Fee", value=f"{weekly_fee_int:,}", inline=True)
            embed.add_field(name="Due Day", value=due_day_str, inline=True)
            if self.discord_id.value:
                embed.add_field(name="Discord ID", value=self.discord_id.value, inline=True)
            if self.notes.value:
                embed.add_field(name="Notes", value=self.notes.value, inline=False)
            embed.set_footer(text=f"Added by {interaction.user.display_name}")
            
            await interaction.followup.send(embed=embed, ephemeral=False)

        except Exception as e:
            # Se o Supabase recusar, o bot não morre em silêncio. Ele te avisa o porquê!
            await interaction.followup.send(f"❌ Erro do Supabase: `{str(e)}`", ephemeral=True)


class Renters(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="add-renter", description="Add a new renter to the system")
    @app_commands.checks.has_permissions(administrator=True)
    async def add_renter(self, interaction: discord.Interaction):
        await interaction.response.send_modal(AddRenterModal())

    @app_commands.command(name="list-renters", description="List all active renters")
    @app_commands.checks.has_permissions(administrator=True)
    async def list_renters(self, interaction: discord.Interaction):
        await interaction.response.defer()

        try:
            result = supabase.table("renters").select("*").eq("is_active", True).order("ingame_name").execute()

            if not result.data:
                await interaction.followup.send("📭 No active renters found.")
                return

            embed = discord.Embed(
                title="📋 Active Renters",
                color=discord.Color.blue(),
                description=f"Total: **{len(result.data)}** renters"
            )

            for renter in result.data[:25]:
                # Como já salvamos o dia em string no add_renter, podemos pegar direto
                day_name = renter.get("due_day", "Unknown")
                fee = renter.get('weekly_fee')
                value = f"💰 Fee: {fee:,} | 📅 Due: {day_name}" if fee is not None else f"📅 Due: {day_name}"
                
                if renter.get("notes"):
                    value += f"\n📝 {renter.get('notes')}"
                embed.add_field(
                    name=renter.get("ingame_name", "Unknown"),
                    value=value,
                    inline=False
                )

            await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(f"❌ Erro ao listar renters: `{str(e)}`")

    @app_commands.command(name="remove-renter", description="Deactivate a renter by in-game name")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(ingame_name="In-game name of the renter to deactivate")
    async def remove_renter(self, interaction: discord.Interaction, ingame_name: str):
        await interaction.response.defer()

        try:
            result = supabase.table("renters")\
                .update({"is_active": False, "updated_at": datetime.utcnow().isoformat()})\
                .eq("ingame_name", ingame_name)\
                .execute()

            if result.data:
                await interaction.followup.send(f"✅ Renter **{ingame_name}** has been deactivated.")
            else:
                await interaction.followup.send(f"❌ Renter **{ingame_name}** not found.")
        except Exception as e:
            await interaction.followup.send(f"❌ Erro ao remover renter: `{str(e)}`")

    @add_renter.error
    @list_renters.error
    @remove_renter.error
    async def permission_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Renters(bot))
