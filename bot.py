from discord import Intents, Message, Embed, Color, ui, ButtonStyle, PermissionOverwrite, Interaction, utils, TextStyle, DMChannel
from datetime import datetime, timedelta
from typing import Dict, List
from discord.ext import commands
import EDIT_ME

intents: Intents = Intents.default()
intents.message_content = True
client: commands.Bot = commands.Bot(command_prefix='/', intents=intents)

staff_recording: Dict[int, List[str]] = {}
is_recording: Dict[int, bool] = {} 
saved_forms: Dict[str, List[str]] = {} 
pending_forms: Dict[int, List[str]] = {}
user_responses: Dict[int, Dict[str, List[str]]] = {}

class TicketButtons(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="Close Ticket", style=ButtonStyle.red)
    async def close_ticket(self, interaction: Interaction, button: ui.Button):
        try:
            if "ticket-" in interaction.channel.name:
                closed_category = utils.get(interaction.guild.categories, name="closed-tickets")
                if not closed_category:
                    staff_role = utils.get(interaction.guild.roles, name=EDIT_ME.staff_role_)
                    overwrites = {
                        interaction.guild.default_role: PermissionOverwrite(read_messages=False),
                        interaction.guild.me: PermissionOverwrite(read_messages=True, send_messages=True),
                        _role: PermissionOverwrite(read_messages=True, send_messages=True) if _role else None
                    }
                    closed_category = await interaction.guild.create_category("closed-tickets", overwrites=overwrites)

                await interaction.channel.edit(category=closed_category)
                
                for child in self.children:
                    child.disabled = True
                await interaction.message.edit(view=self)

                closed_embed = Embed(
                    title="Ticket Closed",
                    description=f"This ticket has been closed by {interaction.user.mention}",
                    color=Color.red()
                )
                await interaction.response.send_message(embed=closed_embed)

        except Exception as e:
            error_embed = Embed(
                title="Error",
                description=f"Error closing ticket: {str(e)}",
                color=Color.red()
            )
            await interaction.response.send_message(embed=error_embed, ephemeral=True)

    @ui.button(label="Claim Ticket", style=ButtonStyle.green)
    async def claim_ticket(self, interaction: Interaction, button: ui.Button):
        try:
            staff_role = utils.get(interaction.guild.roles, name=EDIT_ME.staff_role_)
            if staff_role not in interaction.user.roles:
                error_embed = Embed(
                    title="Permission Denied",
                    description="Only staff members can claim tickets!",
                    color=Color.red()
                )
                await interaction.response.send_message(embed=error_embed, ephemeral=True)
                return

            claim_embed = Embed(
                title="Ticket Claimed",
                description=f"This ticket has been claimed by {interaction.user.mention}",
                color=Color.green()
            )
            await interaction.response.send_message(embed=claim_embed)
            
            button.disabled = True
            await interaction.message.edit(view=self)
        except Exception as e:
            error_embed = Embed(
                title="Error",
                description=f"Error claiming ticket: {str(e)}",
                color=Color.red()
            )
            await interaction.response.send_message(embed=error_embed, ephemeral=True)

class TicketForm(ui.Modal, title='Support Ticket Form'):
    name = ui.TextInput(label='Name', placeholder='Your name...', required=True)
    issue = ui.TextInput(label='Issue', placeholder='Describe your issue...', style=TextStyle.paragraph, required=True)
    priority = ui.TextInput(label='Priority', placeholder='Low/Medium/High', required=True)

    async def on_submit(self, interaction: Interaction):
        try:
            embed = Embed(
                title="Ticket Form Submission",
                color=Color.blue()
            )
            embed.add_field(name="Name", value=self.name.value, inline=False)
            embed.add_field(name="Issue", value=self.issue.value, inline=False)
            embed.add_field(name="Priority", value=self.priority.value, inline=False)
            embed.set_footer(text=f"Submitted by {interaction.user}")
            
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await interaction.response.send_message(f"Error submitting form: {str(e)}", ephemeral=True)

class Buttons(ui.View):
    ticket_counter = 0
    user_last_ticket = {}

    def __init__(self, components: str):
        super().__init__(timeout=None)
        print(f"Initializing Buttons with components: {components}")
        
        all_components = components.split('|')
        print(f"Split components: {all_components}")
        
        for component in all_components:
            component = component.strip()
            print(f"Processing component: {component}")
            if component.startswith('button='):
                button_info = component[7:].split(',')
                print(f"Button info parts: {button_info}")
                if len(button_info) >= 3:
                    label = button_info[0].strip()
                    color = button_info[1].strip()
                    intention = button_info[2].strip().replace('intention=', '').strip()
                    print(f"Creating button: Label={label}, Color={color}, Intention={intention}")
                    
                    button = ui.Button(
                        label=label,
                        style=self.color_(color)
                    )
                    button.callback = self.button_callback
                    button.custom_id = intention
                    self.add_item(button)

    async def button_callback(self, interaction: Interaction):
        intention = interaction.data.get('custom_id')
        print(f"Button clicked with intention: {intention}")
        
        if 'FORM' in intention.upper():
            try:
                class FormSelectView(ui.View):
                    def __init__(self):
                        super().__init__()
                        print(f"Available forms: {saved_forms.keys()}")
                        for form_name in saved_forms.keys():
                            button = ui.Button(
                                label=form_name.title(),
                                style=ButtonStyle.primary,
                                custom_id=f"form_{form_name}"
                            )
                            button.callback = self.form_button_callback
                            self.add_item(button)

                    async def form_button_callback(self, form_interaction: Interaction):
                        form_name = form_interaction.data['custom_id'][5:]
                        try:
                            print(f"Initializing responses for user {form_interaction.user.id}")
                            user_responses[form_interaction.user.id] = {form_name: []}
                            print(f"Updated user_responses: {user_responses}")
                            
                            dm_channel = await form_interaction.user.create_dm()
                            questions_embed = Embed(
                                title=f"Form: {form_name}",
                                description="Please answer the following questions. Use 1 line per question.",
                                color=Color.blue()
                            )
                            for i, question in enumerate(saved_forms[form_name], 1):
                                questions_embed.add_field(
                                    name=f"Question {i}",
                                    value=question,
                                    inline=False
                                )
                            await dm_channel.send(embed=questions_embed)
                            
                            await form_interaction.response.send_message(
                                f"I've sent you the form questions in DM!", 
                                ephemeral=True
                            )
                        except Exception as e:
                            print(f"Error in form_button_callback: {str(e)}")
                            await form_interaction.response.send_message(
                                "I couldn't send you a DM! Please enable DMs from server members and try again.",
                                ephemeral=True
                            )

                if not saved_forms:
                    error_embed = Embed(
                        title="No Forms Available",
                        description="There are no forms available at this time.",
                        color=Color.red()
                    )
                    await interaction.response.send_message(embed=error_embed, ephemeral=True)
                    return

                select_embed = Embed(
                    title="Select a Form",
                    description="Please select which form you'd like to fill out:",
                    color=Color.blue()
                )
                await interaction.response.send_message(
                    embed=select_embed,
                    view=FormSelectView(),
                    ephemeral=True
                )
            except Exception as e:
                print(f"Error in form handling: {str(e)}")
                await interaction.response.send_message(f"Error selecting form: {str(e)}", ephemeral=True)
                
        elif intention == 'MAKE_PRIV_CHANNEL':
            try:
                user_id = str(interaction.user.id)
                current_time = datetime.now()
                
                if user_id in self.user_last_ticket:
                    time_difference = current_time - self.user_last_ticket[user_id]
                    if time_difference < timedelta(seconds=150):
                        seconds_remaining = 150 - time_difference.total_seconds()
                        cooldown_embed = Embed(
                            title="Cooldown Active",
                            description=f"Please wait {seconds_remaining:.0f} seconds before creating a new ticket.",
                            color=Color.orange()
                        )
                        await interaction.response.send_message(embed=cooldown_embed, ephemeral=True)
                        return

                guild = interaction.guild
                Buttons.ticket_counter += 1
                channel_name = f"ticket-{interaction.user.name}-{Buttons.ticket_counter}"
                
                existing_channel = utils.get(guild.channels, name=channel_name)
                if existing_channel:
                    channel_embed = Embed(
                        title="Existing Ticket",
                        description=f"You already have an open ticket in {existing_channel.mention}. Please close your existing ticket first.",
                        color=Color.red()
                    )
                    await interaction.response.send_message(embed=channel_embed, ephemeral=True)
                    return

                tickets_category = utils.get(guild.categories, name=EDIT_ME.ticket_channel_category)
                if not tickets_category:
                    tickets_category = await guild.create_category(EDIT_ME.ticket_channel_category)

                overwrites = {
                    guild.default_role: PermissionOverwrite(read_messages=False),
                    interaction.user: PermissionOverwrite(read_messages=True),
                    guild.me: PermissionOverwrite(read_messages=True, send_messages=True)
                }
                new_channel = await guild.create_text_channel(
                    channel_name, 
                    overwrites=overwrites,
                    category=tickets_category
                )
                
                staff_role = utils.get(guild.roles, name=EDIT_ME.staff_role_)
                welcome_embed = Embed(
                    title="New Support Ticket",
                    description=f"Welcome {interaction.user.mention}! Please describe your issue and a staff member will assist you shortly.",
                    color=Color.blue()
                )
                welcome_embed.add_field(
                    name="Ticket Owner", 
                    value=interaction.user.mention, 
                    inline=True
                )
                
                ticket_buttons = TicketButtons()
                
                await new_channel.send(
                    content=f"{interaction.user.mention} {staff_role.mention if staff_role else ''}",
                    embed=welcome_embed,
                    view=ticket_buttons
                )
                
                self.user_last_ticket[user_id] = current_time
                
                success_embed = Embed(
                    title="Ticket Created",
                    description=f"Channel '{channel_name}' created just for you!",
                    color=Color.green()
                )
                await interaction.response.send_message(embed=success_embed, ephemeral=True)
            except Exception as e:
                error_embed = Embed(
                    title="Error",
                    description=f"Error creating channel: {str(e)}",
                    color=Color.red()
                )
                await interaction.response.send_message(embed=error_embed, ephemeral=True)
        else:
            await interaction.response.send_message(f"Unhandled intention: {intention}", ephemeral=True)

    def color_(self, color: str):
        color = color.lower().strip()
        match color:
            case 'red':
                return ButtonStyle.red
            case 'blue' | 'blurple':
                return ButtonStyle.blurple
            case 'grey' | 'gray':
                return ButtonStyle.grey
            case 'green':
                return ButtonStyle.green

class FormNameModal(ui.Modal, title='Name Your Form'):
    form_name = ui.TextInput(label='Form Name', placeholder='Enter a name for this form...', required=True)

    def __init__(self, questions: List[str]):
        super().__init__()
        self.questions = questions

    async def on_submit(self, interaction: Interaction):
        name = self.form_name.value.lower()
        if name in saved_forms:
            error_embed = Embed(
                title="Error",
                description="A form with this name already exists. Please choose a different name.",
                color=Color.red()
            )
            await interaction.response.send_message(embed=error_embed, ephemeral=True)
            return

        saved_forms[name] = self.questions
        success_embed = Embed(
            title="Form Saved",
            description=f"Form '{name}' has been saved successfully!\nUsers can access it using `/form {name}`",
            color=Color.green()
        )
        await interaction.response.send_message(embed=success_embed)

class FormButtons(ui.View):
    def __init__(self, user_id: int, form_name: str):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.form_name = form_name

    @ui.button(label="Approve", style=ButtonStyle.green)
    async def approve(self, interaction: Interaction, button: ui.Button):
        try:
            user = await client.fetch_user(self.user_id)
            if not user:
                await interaction.response.send_message("User not found.", ephemeral=True)
                return

            try:
                dm_channel = await user.create_dm()
                approval_embed = Embed(
                    title="Form Approved",
                    description=f"Your responses to form '{self.form_name}' have been approved!",
                    color=Color.green()
                )
                await dm_channel.send(embed=approval_embed)
            except Exception as e:
                await interaction.response.send_message(f"Couldn't DM user: {str(e)}", ephemeral=True)
                return

            success_embed = Embed(
                title="Form Approved",
                description=f"Form '{self.form_name}' from {user.mention} has been approved by {interaction.user.mention}",
                color=Color.green()
            )
            await interaction.response.send_message(embed=success_embed)

            for child in self.children:
                child.disabled = True
            await interaction.message.edit(view=self)

        except Exception as e:
            await interaction.response.send_message(f"Error: {str(e)}", ephemeral=True)

    @ui.button(label="Deny", style=ButtonStyle.red)
    async def deny(self, interaction: Interaction, button: ui.Button):
        try:
            user = await client.fetch_user(self.user_id)
            if not user:
                await interaction.response.send_message("User not found.", ephemeral=True)
                return

            try:
                dm_channel = await user.create_dm()
                denial_embed = Embed(
                    title="Form Denied",
                    description=f"Your responses to form '{self.form_name}' have been denied.",
                    color=Color.red()
                )
                await dm_channel.send(embed=denial_embed)
            except Exception as e:
                await interaction.response.send_message(f"Couldn't DM user: {str(e)}", ephemeral=True)
                return

            deny_embed = Embed(
                title="Form Denied",
                description=f"Form '{self.form_name}' from {user.mention} has been denied by {interaction.user.mention}",
                color=Color.red()
            )
            await interaction.response.send_message(embed=deny_embed)

            for child in self.children:
                child.disabled = True
            await interaction.message.edit(view=self)

        except Exception as e:
            await interaction.response.send_message(f"Error: {str(e)}", ephemeral=True)

async def send_message(message_: Message, user_message: str) -> None:
    if is_private := user_message[0] == '?':
        user_message = user_message[1:]

    if message_.content.startswith('$embed'):
        print("Embed command detected")
        try:
            parts = message_.content.split('|')
            title = ' '.join(parts[0].split()[1:-1]) + ' ' + parts[0].split()[-1]
            description = parts[1].strip()
            color_parts = [int(c.strip()) for c in parts[2].split(',')]
            
            embed = Embed(
                title=title,
                description=description,
                color=Color.from_rgb(*color_parts)
            )
            
            buttons_info = []
            for part in parts[3:]:
                part = part.strip()
                if part.startswith('field='):
                    field_parts = part.replace('field=', '').split(',')
                    embed.add_field(
                        name=field_parts[0].strip(),
                        value=field_parts[1].strip(),
                        inline=True
                    )
                elif part.startswith('button='):
                    buttons_info.append(part)
            
            if buttons_info:
                view = Buttons(' | '.join(buttons_info))
                await message_.channel.send(embed=embed, view=view)
                return
            
            await message_.channel.send(embed=embed)
            return
        except Exception as e:
            print(f"Error in embed command: {str(e)}")
            error_embed = Embed(
                title="Error",
                description=f"Error creating embed: {str(e)}",
                color=Color.red()
            )
            await message_.channel.send(embed=error_embed)
            return

    if message_.author.id in is_recording and is_recording[message_.author.id]:
        if message_.content.lower() == '/form stop':
            is_recording[message_.author.id] = False
            recorded_messages = staff_recording[message_.author.id]
            staff_recording[message_.author.id] = []
            
            preview_embed = Embed(
                title="Form Recording Completed",
                description=f"Recorded questions:\n```\n{chr(10).join(recorded_messages)}\n```\nPlease reply with your desired form name.",
                color=Color.blue()
            )
            await message_.channel.send(embed=preview_embed)
            
            pending_forms[message_.author.id] = recorded_messages
            return
        else:
            staff_recording[message_.author.id].append(message_.content)
            return

    if message_.author.id in pending_forms:
        proposed_name = message_.content.lower()
        if proposed_name in saved_forms:
            error_embed = Embed(
                title="Error",
                description="A form with this name already exists. Please choose a different name.",
                color=Color.red()
            )
            await message_.channel.send(embed=error_embed)
            return

        class ConfirmButton(ui.View):
            def __init__(self):
                super().__init__()

            @ui.button(label="Confirm Name", style=ButtonStyle.green)
            async def confirm(self, interaction: Interaction, button: ui.Button):
                saved_forms[proposed_name] = pending_forms[message_.author.id]
                del pending_forms[message_.author.id]
                
                success_embed = Embed(
                    title="Form Saved",
                    description=f"Form '{proposed_name}' has been saved successfully!",
                    color=Color.green()
                )
                await interaction.response.send_message(embed=success_embed)
                
                button.disabled = True
                await interaction.message.edit(view=self)

        confirm_embed = Embed(
            title="Confirm Form Name",
            description=f"Are you sure you want to name this form '{proposed_name}'?",
            color=Color.blue()
        )
        await message_.channel.send(embed=confirm_embed, view=ConfirmButton())
        return

    if user_message.startswith('/'):
        pass

@client.event
async def on_ready() -> None:
    print(f'{client.user} is now running!')
    print("Commands registered:", [command.name for command in client.commands])

@client.command(name='form')
async def form_command(ctx, action: str, *args):
    if action.lower() == 'make':
        staff_role = utils.get(ctx.guild.roles, name=EDIT_ME.staff_role_)
        if staff_role not in ctx.author.roles:
            error_embed = Embed(
                title="Permission Denied",
                description="Only staff members can create forms!",
                color=Color.red()
            )
            await ctx.send(embed=error_embed)
            return
        
        is_recording[ctx.author.id] = True
        staff_recording[ctx.author.id] = []
        
        instructions_embed = Embed(
            title="Form Recording Started",
            description="I'll record your messages to create a form. Type `/form stop` when you're done.",
            color=Color.blue()
        )
        await ctx.send(embed=instructions_embed)
        return

    elif action.lower() == 'finish':
        user_id = ctx.author.id
        
        if user_id in user_responses:
            try:
                form_name = next(iter(user_responses[user_id].keys()))
                responses = user_responses[user_id][form_name]
                questions = saved_forms[form_name]

                response_embed = Embed(
                    title="Form Submission",
                    description=f"New submission for form '{form_name}'",
                    color=Color.blue()
                )
                response_embed.add_field(
                    name="Submitted By",
                    value=ctx.author.mention,
                    inline=False
                )
                
                for question, answer in zip(questions, responses):
                    response_embed.add_field(
                        name=question,
                        value=answer,
                        inline=False
                    )

                guild = client.get_guild(EDIT_ME.guild_id)
                staff_channel = guild.get_channel(EDIT_ME.staff_channel_id)
                
                if staff_channel:
                    await staff_channel.send(
                        embed=response_embed,
                        view=FormButtons(user_id, form_name)
                    )

                    confirm_embed = Embed(
                        title="Form Submitted",
                        description="Your form has been submitted and is pending staff review.",
                        color=Color.green()
                    )
                    await ctx.send(embed=confirm_embed)

                del user_responses[user_id]
                return

            except Exception as e:
                error_embed = Embed(
                    title="Error",
                    description=f"Error submitting form: {str(e)}",
                    color=Color.red()
                )
                await ctx.send(embed=error_embed)
                return
        else:
            return

    else:
        form_name = action.lower()
        if form_name not in saved_forms:
            error_embed = Embed(
                title="Form Not Found",
                description=f"No form found with name '{form_name}'",
                color=Color.red()
            )
            await ctx.send(embed=error_embed)
            return

        try:
            dm_channel = await ctx.author.create_dm()
            questions_embed = Embed(
                title=f"Form: {form_name}",
                description="Please answer the following questions:",
                color=Color.blue()
            )
            for i, question in enumerate(saved_forms[form_name], 1):
                questions_embed.add_field(
                    name=f"Question {i}",
                    value=question,
                    inline=False
                )
            await dm_channel.send(embed=questions_embed)
            
            confirm_embed = Embed(
                title="Form Sent",
                description=f"I've sent you the form questions in DM, {ctx.author.mention}!",
                color=Color.green()
            )
            await ctx.send(embed=confirm_embed)
        except Exception as e:
            error_embed = Embed(
                title="DM Error",
                description="I couldn't send you a DM! Please enable DMs from server members and try again.",
                color=Color.red()
            )
            await ctx.send(embed=error_embed)

@client.command(name='embed')
async def embed_command(ctx, *, user_message: str):
    try:
        parts = user_message.split('|')
        
        if len(parts) < 3:
            await ctx.send("Please provide a title, description, color, and at least one field or button.")
            return
        
        title = parts[0].strip()
        description = parts[1].strip()
        color_parts = [int(c.strip()) for c in parts[2].strip().split(',')]
        
        embed = Embed(
            title=title,
            description=description,
            color=Color.from_rgb(*color_parts)
        )
        
        buttons_info = []
        for part in parts[3:]:
            part = part.strip()
            if part.startswith('field='):
                field_parts = part.replace('field=', '').split(',')
                embed.add_field(
                    name=field_parts[0].strip(),
                    value=field_parts[1].strip(),
                    inline=True
                )
            elif part.startswith('button='):
                buttons_info.append(part)
        
        if buttons_info:
            view = Buttons(' | '.join(buttons_info))
            await ctx.send(embed=embed, view=view)
            return
        
        await ctx.send(embed=embed)
    except Exception as e:
        error_embed = Embed(
            title="Error",
            description=f"Error creating embed: {str(e)}",
            color=Color.red()
        )
        await ctx.send(embed=error_embed)

@client.command(name='test')
async def test_command(ctx):
    await ctx.send("The bot is working!")

def main() -> None:
    client.run(EDIT_ME.discord_bot_token)

if __name__ == '__main__':
    main()
