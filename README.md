# BloxyBot

This is a Discord bot designed to manage support tickets within a server. It allows users to create tickets, staff members to claim and close tickets, and provides a form system for users to submit their issues.

## Features

- **Ticket Creation**: Users can create support tickets that are categorized and managed.
- **Ticket Management**: Staff members can claim and close tickets, with appropriate permissions.
- **Form System**: Users can fill out forms to describe their issues, which can be reviewed by staff.
- **Embed Messages**: The bot can send rich embed messages with buttons for interaction.
- **DM Notifications**: Users receive direct messages for form submissions and ticket updates.

## Requirements

- Python 3.8 or higher
- `discord.py` library (version 2.0 or higher)
- A Discord bot (obviously)

## Installation

1. Download the 'main.py,' and 'EDIT_ME.py' files

2. Make sure to install all of the packages

3. Make sure to change all of the variables in 'EDIT_ME.py' or the bot will not work!:
   ```python
   staff_channel_id = 0
   guild_id = 0
   discord_bot_token = 0
   staff_role_ = 'STAFF'
   ticket_channel_category = '#TICKETS'
   ```

## Usage

1. Run the bot:
   ```bash
   python main.py
   ```

2. Invite the bot to your server using the OAuth2 URL with the necessary permissions.

3. Use the following commands in your Discord server:
   - `/form make`: Start recording a new form.
   - `/form finish`: Submit the recorded form.
   - `/form [form_name]`: Fill out an existing form.
   - `/embed [title] | [description] | [color] | [fields/buttons]`: Create and send an embed message.

## Example Command
```python
/embed Tickets 🎟️ | Press the button to make a ticket! | 255, 255, 0 | field=Ban Appeal, We rarely unban people so don't expect anything! | button=Ban Appeal/Staff Application, red, intention=form | button=Make A Ticket, blue, intention=make_priv_channel
```
# Code result:
![EmbedBot](https://github.com/user-attachments/assets/6829a01c-4dcb-442b-854f-7d4e4c7c6bf4)


## Contributing

Contributions would be awesome, unless your name is: 'Derry k. Tutt,' because if that's the case then go away!
