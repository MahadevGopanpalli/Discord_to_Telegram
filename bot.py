

import conf as config 
import socks 
import discord
from discord import errors
import requests
import re
import json
import logging
from box import Box as box
from colorama import Back, Fore, init, Style
from aiohttp import client_exceptions as clientExcps

init(autoreset=True)

colorSchemes = {
    'SUCCESS': f"{Back.GREEN}{Fore.BLACK}{Style.NORMAL}",
    'FAILURE': f"{Back.RED}{Fore.WHITE}{Style.BRIGHT}",
    'WARNING': f"{Back.YELLOW}{Fore.BLACK}{Style.BRIGHT}",
    'RESET': f"{Style.RESET_ALL}"
}
colorSchemes = box(colorSchemes)

logging.basicConfig(format=f'{colorSchemes.FAILURE}[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s', level=logging.ERROR)



bot = discord.Client()
baseUrl = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}"


def replaceMentions(mentions, msg, channel):
    if channel:
        for ch in mentions:
            # msg = msg.replace(str(f"#{ch.id}"), '')
            msg = re.sub(f"<#{ch.id}>", '', msg)
            msg = re.sub(f"<{ch.id}>", '', msg)
            msg = re.sub(f"<*{ch.id}>", '', msg)
            msg = re.sub(f"<*{ch.id}*>", '', msg)
            msg = re.sub(f"<{ch.id}*>", '', msg)
    elif not channel:
        for member in mentions:
            msg = re.sub(f"<@{member.id}>", '', msg)
            msg = re.sub(f"<@!{member.id}>", '', msg)
            msg = re.sub(f"<{member.id}>", '', msg)
            msg = re.sub(f"<*{member.id}*>", '', msg)
            msg = re.sub(f"<{member.id}*>", '', msg)
            msg = re.sub(f"<*{member.id}>", '', msg)
    return str(msg)

def removeTags(msg):
    msg = re.sub(r"@\w*", '', msg)
    msg = requests.utils.quote(msg)
    #print(f"{colorSchemes.SUCCESS}Quoted message: {msg}")
    return msg




def isPhoto(url):
    imgExts = ["png", "jpg", "jpeg", "webp"]
    if any(ext in url for ext in imgExts):
        return True
    else:
        return False

def isVideo(url):
    vidExts = ["mp4", "MP4", "mkv"]
    if any(ext in url for ext in vidExts):
        return True
    else:
        return False

def isDoc(url):
    docExts = ["zip", "pdf", "gif"]
    if any(ext in url for ext in docExts):
        return True
    else:
        return False


def sendMsg(url):
    attempts = 0
    while True:
        if attempts < 5:
            try:
                print(f"[+] Sending Message to Telegram ...{url}")
                resp = requests.post(url)
                if resp.status_code == 200:
                    print(f"{colorSchemes.SUCCESS}[+] Message sent!\n")
                    break
                elif resp.status_code != 200:
                    print(str(resp))
                    raise OSError
            except OSError:
                attempts += 1
                print(f"{colorSchemes.FAILURE}[-] Sending failed!\n[+] Trying again ... (Attempt {attempts})")
                continue
            except KeyboardInterrupt:
                print("\n[+] Please wait untill all messages in queue are sent!\n")
        else:
            print(f"{colorSchemes.FAILURE}[-] Message was not sent in 5 attempts. \n[-] Please check your network.")
            break





@bot.event
async def on_message(message):
    try:
        serverName = message.guild.name
        serversList = config.serversList.keys()
        channelName = message.channel.name
    except AttributeError:
        pass
    with open('message.json','w') as f:
        f.write(str(message))
    print(f"Server: {serverName}, Channel : {channelName} , Channel_Id: {message.channel.id}")
    if serverName in serversList:
        channelsList = config.serversList[serverName].keys()
        if channelName in channelsList:
            print(f"\n-------------------------------------------\n[+] Channel: {channelName}")
            if message.content:
                if message.mentions:
                    # print(f"\n----------------\nUser Mentioned\n----------------")
                    message.content = replaceMentions(message.mentions, message.content, channel=False)
                if message.channel_mentions:
                    # print(f"\n----------------\nChannel Mentioned\n----------------")
                    message.content = replaceMentions(message.channel_mentions, message.content, channel=True)
                # toSend = f"{message.guild}/{message.channel}/{message.author.name}: {message.content}"
                toSend = message.content
                print(f"[+] Message: {toSend}")
                toSend = removeTags(toSend)
                url = f"{baseUrl}/sendMessage?text={toSend}&chat_id={config.serversList[serverName][channelName]}"
                sendMsg(url)

            if message.attachments:
                attachmentUrl = message.attachments[0].url
                if isPhoto(attachmentUrl):
                    url = f"{baseUrl}/sendPhoto?photo={attachmentUrl}&chat_id={config.serversList[serverName][channelName]}"
                    sendMsg(url)
                elif isVideo(attachmentUrl):
                    url = f"{baseUrl}/sendVideo?video={attachmentUrl}&chat_id={config.serversList[serverName][channelName]}"
                    sendMsg(url)
                elif isDoc(attachmentUrl):
                    url = f"{baseUrl}/sendDocument?document={attachmentUrl}&chat_id={config.serversList[serverName][channelName]}"
                    sendMsg(url)
                
            if message.embeds:
                embed = message.embeds[0].to_dict()
                print(embed)
                if str(embed['type']) == "rich":
                    if 'title' in embed.keys() and 'description' in embed.keys():
                        toSend = f"{message.guild}/{message.channel}/{message.author.name}: {embed['title']}\n{embed['description']}"
                        toSend = removeTags(toSend)
                    elif 'title' in embed.keys():
                        toSend = f"{message.guild}/{message.channel}/{message.author.name}: {embed['title']}"
                        toSend = removeTags(toSend)
                    elif 'description' in embed.keys():
                        toSend = f"{message.guild}/{message.channel}/{message.author.name}: {embed['description']}"
                        toSend = removeTags(toSend)
                    url = f"{baseUrl}/sendMessage?text={toSend}&chat_id={config.serversList[serverName][channelName]}"
                    sendMsg(url)
                    # print(embed)
                elif str(embed['type']) == "link":
                    toSend = f"{embed['title']}\n{embed['description']}\n{embed['url']}"
                    toSend = removeTags(toSend)
                    url = f"{baseUrl}/sendMessage?text={toSend}&chat_id={config.serversList[serverName][channelName]}"
                    sendMsg(url)



#Run the bot using the user token
try:
    print("Server Started.....")
    bot.run(config.USER_DISCORD_TOKEN, bot=False)
    print("Server Started.....")
except RuntimeError:
    print("\n\nPlease Wait ...\nShutting down the bot ... \n")
    quit()
except errors.HTTPException:
    print(f"{colorSchemes.FAILURE}Invalid discord token or network down!")
    quit()
except errors.LoginFailure:
    print(f"{colorSchemes.FAILURE}Login failed to discord. May be bad token or network down!")
    quit()
except clientExcps.ClientConnectionError:
    print(f"{colorSchemes.FAILURE}[-] Proxy seems to be down or network problem.")
    quit()
