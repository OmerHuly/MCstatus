import discord
import time
from datetime import datetime
from mcstatus import MinecraftServer
from dotenv import dotenv_values


client = discord.Client()
config = dotenv_values(".env")
minecraft_server = MinecraftServer.lookup(config["SERVER_IP_PORT"])
start_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
players_last_login = {}

@client.event
async def on_ready():
    """An event that will trigger when the bot is ready"""
    log('Logged in as {0.user}'.format(client))
    bot_channel = get_channel(config["BOT_CHANNEL"])
    try:
        messages = await bot_channel.history(limit=100, oldest_first=False).flatten()
        last_message = None
        for msg in messages:
            try:
                last_message = await bot_channel.fetch_message(msg.id)
                break
            except discord.NotFound:
                log("Last message isn't present, checking next message...")

        if last_message == None:
            raise discord.NotFound

        while True:
            await edit_message_and_sleep(last_message, create_status_message(), 5)
    except discord.NotFound:
        log("Didn't find message to edit, sending a new one...")
        await bot_channel.send(content=create_status_message())


@client.event
async def on_message(message):
    """An event that will trigger when a message is sent in any channel on the server"""
    if message.author == client.user and message.content.startswith("Last updated: "):
        while True:
            await edit_message_and_sleep(message, create_status_message(), 5)
    elif message.author != client.user and str(message.channel) == config["BOT_CHANNEL"] and message.content.startswith(config["CMD_CHAR"]):
        if message.content.startswith(config["LAST_CONNECTIONS_CMD"]):
            player_name = get_arguments(message.content)[0]
            log("Got command: \"{0}\", will delete this message soon after after showing when \"{1}\" was last online.".format(message.content, player_name))
            last_connection_replay = ''
            if player_name in players_last_login:
                last_connection_replay = "{0} was last online on {1}.".format(player_name, players_last_login[player_name])
            else:
                last_connection_replay = "{0} wasn't online since {1}.".format(player_name, start_time)

            await message.channel.send(content=last_connection_replay, delete_after=10)
            await message.delete(delay=1)
            log("Replayed to last connection command with \"{0}\".".format(last_connection_replay))
        else:
            log("Deleting message \"{0}\" from {1}".format(message.content, message.author))
            await message.delete(delay=1)
    elif str(message.channel) == config["BOT_CHANNEL"]:
        log("Deleting message \"{0}\" from {1}".format(message.content, message.author))
        await message.delete(delay=1)


def get_channel(name):
    """Get a channel from the Discord server by name"""
    for guild in client.guilds:
        for channel in guild.text_channels:
            if (channel.name == name):
                return channel


def create_status_message():
    """Create the status message with data from the server"""
    now = get_current_date()
    message = "Last updated: " + now + "\n"
    status = None
    try:
        status = minecraft_server.status()
    except:
        message += "Could not get data from the server..."
    else:
        message += "The server has {0}/{1} players and replied in {2} ms".format(status.players.online, status.players.max, status.latency)
        players = status.players.sample
        if players is not None:
            message += "\nThe following players are online: "
            index = 1
            for player in sorted(players, key=lambda p: p.name):
                message += "\n" + str(index) + ") " + player.name
                players_last_login.update({player.name: now})
                index += 1

    print(message)
    return message


async def edit_message_and_sleep(message, new_content, time_to_sleep):
    """Edit the given message to contain the given content and sleep the desired time in seconds"""
    try:
        await message.edit(content=new_content)
    except:
        log("Something went wrong while trying to edit the message...")
    finally:
        time.sleep(time_to_sleep)


def get_arguments(msg):
    return msg.split(' ')[1:]


def get_current_date():
    """Get the current date and time as a string"""
    return datetime.now().strftime("%d/%m/%Y %H:%M:%S")


def log(msg):
    """Print a log to the console"""
    print("[" + get_current_date() + "] " + msg)


def main():
    """Run the client

    Will connect to Discord and activate the on_ready event when finished"""

    client.run(config["BOT_TOKEN"])


if __name__ == "__main__":
    main()
