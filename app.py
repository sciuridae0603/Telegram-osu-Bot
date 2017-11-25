#!/usr/bin/env python
# -*- coding: utf-8 -*-
from telegram.ext import  Updater, CommandHandler, CallbackQueryHandler, RegexHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from uuid import uuid4
from enum import Enum
import logging
import json
import http.client
import urllib.parse
import requests
import math
from telegram.ext.dispatcher import run_async

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        level=logging.INFO)
logger = logging.getLogger(__name__)

cache = {}

#Config
token = "Telegram_Token_Here"
osu_api_token = "OSU_API_Token_Here"

#keyboards
menu_keyboard = InlineKeyboardMarkup([  [InlineKeyboardButton("Player info", callback_data='userinfo')],
                                        [InlineKeyboardButton("Player best score", callback_data='userbest')],
                                        [InlineKeyboardButton("Recent play", callback_data='userrecent')]])

back_keyboard = InlineKeyboardMarkup([  [InlineKeyboardButton("Go back", callback_data='back_to_mod')]])

back_to_query = InlineKeyboardMarkup([  [InlineKeyboardButton("Go back", callback_data='back_to_query')]])

select_keyboard = InlineKeyboardMarkup([  [InlineKeyboardButton("<", callback_data='prev'),
                                        InlineKeyboardButton(">", callback_data='next')],
                                        [InlineKeyboardButton("Beatmap", callback_data='getmap')],
                                        [InlineKeyboardButton("Go back", callback_data='back_to_mod')]])

mode_keyboard = InlineKeyboardMarkup([  [InlineKeyboardButton("Standard", callback_data='std')],
                                        [InlineKeyboardButton("Taiko", callback_data='tak')],
                                        [InlineKeyboardButton("CtB", callback_data='ctb')],
                                        [InlineKeyboardButton("Mania", callback_data='man')],
                                        [InlineKeyboardButton("Go back", callback_data='menu')]])

mod = {"Key2":268435456,"Key3":134217728,"Key1":67108864,"Key10":33554432,"Key9":16777216,"LastMod":4194304,"Random":2097152,"FadeIn":1048576,"Key8":524288,"Key7":262144,"Key6":131072,"Key5":65536,"Key4":32768,"Perfect":16384,"Relax2":8192,"SpunOut":4096,"Autoplay":2048,"Flashlight":1024,"Nightcore":512,"HalfTime":256,"Relax":128,"DoubleTime":64,"SuddenDeath":32,"HardRock":16,"Hidden":8,"NoVideo":4,"Easy":2,"NoFail":1}
    
def get_use_mod(num):
    usemod = []
    use = False
    if num == 0:
        return("No")
    else:
        while True:
            for key , value in mod.items():
                temp = num - value
                if temp >= 0 :
                    num = num - value
                    usemod.append(key)
                    use = True
                elif num == 0 :
                    return(",".join(usemod))
                    break
                    

def score_data(decoded_json): #成績訊息

    if decoded_json['perfect'] == "1":
        perfect = "Yes"
    else:
        perfect = "No"

    msg =( "<b>Beatmap ID</b> : " + decoded_json['beatmap_id'] + "\n" +
            "<b>Score</b> : " + decoded_json['score'] + "\n" +
            "<b>Max Combo</b> : " + decoded_json['maxcombo'] + "\n" +
            "<b>50</b> : " + decoded_json['count50'] + "\n" +
            "<b>100</b> : " + decoded_json['count100'] + "\n" +
            "<b>300</b> : " + decoded_json['count300'] + "\n" +
            "<b>Miss</b> : " + decoded_json['countmiss'] + "\n" +
            "<b>Katu</b> : " + decoded_json['countkatu'] + "\n" +
            "<b>Geki</b> : " + decoded_json['countgeki'] + "\n" +
            "<b>Perfect</b> : " + perfect + "\n" +
            "<b>Use Mod</b> : " + get_use_mod(int(decoded_json['enabled_mods'])) + "\n" +
            "<b>Date</b> : " + decoded_json['date'] + "\n" +
            "<b>Rank</b> : " + decoded_json['rank'] + "\n" )
    if "pp" in decoded_json:
        msg = msg + "<b>PP</b> : " + decoded_json['pp']
    return(msg)

def map_msg(decoded_json,num): #圖訊息
    if decoded_json[num]['approved'] == '3':
        approved="Qualified"
    elif decoded_json[num]['approved'] == '2':
        approved="Approved"
    elif decoded_json[num]['approved'] == '1':
        approved="Ranked"
    elif decoded_json[num]['approved'] == '0':
        approved="Ppending"
    elif decoded_json[num]['approved'] == '-1':
        approved="WIP"
    elif decoded_json[num]['approved'] == '-2':
        approved="Graveyard"

    if decoded_json[num]['max_combo'] is None:
        decoded_json[num]['max_combo']="Taiko Map"

    msg = ( "<b>Beatmap Name</b> : " + decoded_json[num]['title'] + "\n" +
            "<b>Beatmap Artist</b> : " + decoded_json[num]['artist'] + "\n" +
            "<b>Beatmap Creator</b> : " + decoded_json[num]['creator'] + "\n" +
            "<b>Version</b> : " + decoded_json[num]['version'] + "\n" +
            "<b>FC Combo</b> : " + decoded_json[num]['max_combo'] + "\n" +
            "<b>BPM</b> : " + decoded_json[num]['bpm'] +  "\n" +
            "<b>Time</b> : " + decoded_json[num]['approved_date']+"\n" +
            "<b>Star</b> : " + str(round(float(decoded_json[num]['difficultyrating']),2))+"\n" +
            "<b>CS</b> : " + decoded_json[num]['diff_size']+ "\n" +
            "<b>OD</b> : " + decoded_json[num]['diff_overall']+ "\n" +
            "<b>AR</b> : " + decoded_json[num]['diff_approach']+ "\n" +
            "<b>HP</b> : " + decoded_json[num]['diff_drain']+ "\n" +
            "<b>Mode</b> : " + modetext(str(decoded_json[0]['mode'])) + "\n" +
            "<b>Link</b> : https://osu.ppy.sh/b/" + decoded_json[num]['beatmap_id'])

    return(msg)

def user_msg(decoded_json,mode): #玩家訊息
    msg = ("<b>User</b> : " + decoded_json[0]['username'] + "\n" +
        "<b>Mode</b> : " + modetext(mode) + "\n" +
        "<b>Plays Count</b> : " + decoded_json[0]['playcount'] + "\n" +
        "<b>SS Rank Count</b> : " + decoded_json[0]['count_rank_ss'] + "\n" +
        "<b>S Rank Count</b> : " + decoded_json[0]['count_rank_s'] + "\n" +
        "<b>A Rank Count</b> : " + decoded_json[0]['count_rank_a'] + "\n" +
        "<b>Total Score</b> : " + decoded_json[0]['total_score'] + "\n" +
        "<b>ACC</b> : " + str(round(float(decoded_json[0]['accuracy']), 2)) + "\n" +
        "<b>PP</b> : " + decoded_json[0]['pp_raw'] + "\n" +
        "<b>Rank</b> : " + decoded_json[0]['pp_rank'] + "\n" +
        "<b>Level</b> : " + str(round(float(decoded_json[0]['level']), 2))  + "\n" +
        "<b>Country Rank</b> : " + decoded_json[0]['pp_country_rank'] + "\n" )
    if "country" in decoded_json[0]:
        msg = msg + "<b>Country</b> : " + decoded_json[0]['country'] 

    return(msg)

def start(bot, update):
    bot.sendMessage(update.message.chat_id, text='OSU info bot!\n Usage : \n/userinfo <PlayerName>\n/beatmap <beatmapID>')

def modetext(mode):
    if mode == "0":
        return 'Standard'
    elif mode == "1":
        return 'Taiko'
    elif mode == "2":
        return 'CtB'
    elif mode == "3":
        return 'Mania'

def num_to_mode(mode):
    if mode=="0": mode="std"
    if mode=="1": mode="tak"
    if mode=="2": mode="ctb"
    if mode=="3": mode="man"
    return(mode)

def mode_to_num(mode):
    if mode=="std": mode="0"
    if mode=="tak": mode="1"
    if mode=="ctb": mode="2"
    if mode=="man": mode="3"
    return(mode)

def getdata(user,method,mode=0,list=0,chat_id=None,message_id=None):

    mode = mode_to_num(mode)

    if mode != cache[chat_id][message_id]['mode']:
        if "userrecentjson" in cache[chat_id][message_id]:
            del cache[chat_id][message_id]['userrecentjson']
        if "userbestjson" in cache[chat_id][message_id]:
            del cache[chat_id][message_id]['userbestjson']

    if(method == "userinfo"):

        url = 'https://osu.ppy.sh/api/get_user'
        r = requests.post(url, dict(k=osu_api_token,u=user,m=mode))
        if r.text == "[]":
            return("No Data")
        return(user_msg(json.loads(r.text),mode))

    elif(method == "userbest"):

        url = 'https://osu.ppy.sh/api/get_user_best'
        if not "userbestjson" in cache[chat_id][message_id]:
            r = requests.post(url, dict(k=osu_api_token,u=user,m=mode,limit="50"))
            if r.text == "[]":
                return("No Data")
            else:
                cache[chat_id][message_id]["userbestjson"] = json.loads(r.text)
        data = cache[chat_id][message_id]["userbestjson"]
        return("<b>"+str(list + 1)+"</b>\n"+score_data(data[list]))

    elif(method == "userrecent"):

        url = 'https://osu.ppy.sh/api/get_user_recent'
        if not "userrecentjson" in cache[chat_id][message_id]:
            r = requests.post(url, dict(k=osu_api_token,u=user,m=mode,limit="50"))
            if r.text == "[]":
                return("No Data")
            else:
                cache[chat_id][message_id]["userrecentjson"] = json.loads(r.text)
        data = cache[chat_id][message_id]["userrecentjson"]
        return("<b>"+str(list + 1)+"</b>\n"+score_data(data[list]))

    elif(method == "beatmap"):

        url = 'https://osu.ppy.sh/api/get_beatmaps'
        r = requests.post(url, dict(k=osu_api_token,b=user,m=mode))
        if r.text == "[]":
            return("No Data")
        return(map_msg(json.loads(r.text),0))


@run_async
def callback(bot,update):
    query = update.callback_query
    chat_id = str(query.message.chat.id)
    message_id = str(query.message.message_id)
    if chat_id not in cache:
        try:
            bot.edit_message_text(text="message expire.",chat_id=chat_id,message_id=message_id)
            return
        except:
            return
            pass
    if message_id not in cache[chat_id]:
        try:
            bot.edit_message_text(text="message expire.",chat_id=chat_id,message_id=message_id)
            return
        except:
            return
            pass
    username = cache[chat_id][message_id]['username']
    feature = cache[chat_id][message_id]['feature']
    status = cache[chat_id][message_id]['status']
    function = cache[chat_id][message_id]['query']

    print("Callback User : " + str(query.from_user.first_name) + " (" + str(query.from_user.id) + ") Chat ID : " + chat_id + " Message ID : " + message_id + " Feature : " + feature + " Query : " + function + " Status : "+ status + " Query DATA : " + query.data)
    if str(query.from_user.id) != cache[chat_id][message_id]['user_id']:
        bot.answer_callback_query(query.id,text="You aren't proposer.")
    else:
        if feature == "userinfo":

            if status == "mainmenu":

                if query.data == "userinfo":
                    
                    cache[chat_id][message_id]['query'] = "userinfo"
                    cache[chat_id][message_id]['status'] = "select_mode"
                    bot.edit_message_text(text="Please choose mode: ",reply_markup=mode_keyboard,chat_id=chat_id,message_id=message_id)

                if query.data == "userbest":

                    cache[chat_id][message_id]['query'] = "userbest"
                    cache[chat_id][message_id]['status'] = "select_mode"
                    bot.edit_message_text(text="Please choose mode: ",reply_markup=mode_keyboard,chat_id=chat_id,message_id=message_id)

                if query.data == "userrecent":
                    
                    cache[chat_id][message_id]['query'] = "userrecent"
                    cache[chat_id][message_id]['status'] = "select_mode"
                    bot.edit_message_text(text="Please choose mode: ",reply_markup=mode_keyboard,chat_id=chat_id,message_id=message_id)

            elif status == "select_mode":

                if query.data == "back_to_query":

                    if function == "userinfo":
                        bot.edit_message_text(text=getdata(username,function, cache[chat_id][message_id]['mode'],chat_id=chat_id,message_id=message_id),reply_markup=back_keyboard,chat_id=chat_id,message_id=message_id,parse_mode=ParseMode.HTML)
                    elif function == "userbest":
                        bot.edit_message_text(text=getdata(username,function, cache[chat_id][message_id]['mode'],chat_id=chat_id,message_id=message_id,list=cache[chat_id][message_id]['list']),reply_markup=select_keyboard,chat_id=chat_id,message_id=message_id,parse_mode=ParseMode.HTML)
                    elif function == "userrecent":
                        bot.edit_message_text(text=getdata(username,function, cache[chat_id][message_id]['mode'],chat_id=chat_id,message_id=message_id,list=cache[chat_id][message_id]['list']),reply_markup=select_keyboard,chat_id=chat_id,message_id=message_id,parse_mode=ParseMode.HTML)

                if query.data == "back_to_mod":

                    cache[chat_id][message_id]['list'] = 0
                    bot.edit_message_text(text="Please choose mode: ",reply_markup=mode_keyboard,chat_id=chat_id,message_id=message_id)

                elif query.data == "menu":

                    cache[chat_id][message_id]['list'] = 0
                    cache[chat_id][message_id]['query'] = ""
                    cache[chat_id][message_id]['status'] = "mainmenu"
                    bot.edit_message_text(text="Please choose feature: ",reply_markup=menu_keyboard,chat_id=chat_id,message_id=message_id)

                elif query.data == "next" or query.data == "prev" or query.data == "getmap":

                    if "userrecentjson" not in cache[chat_id][message_id] and "userbestjson" not in cache[chat_id][message_id]:
                        bot.edit_message_text(text="🌚 No Data",reply_markup=back_to_query,chat_id=chat_id,message_id=message_id,parse_mode=ParseMode.HTML)
                        return 

                    if query.data == "getmap" and cache[chat_id][message_id]['query'] == "userbest":
                        bot.edit_message_text(text=getdata(cache[chat_id][message_id]['userbestjson'][cache[chat_id][message_id]['list']]['beatmap_id'],"beatmap",query.data,chat_id=chat_id,message_id=message_id),reply_markup=back_to_query,chat_id=chat_id,message_id=message_id,parse_mode=ParseMode.HTML)
                        bot.answer_callback_query(query.id)
                        return        

                    if query.data == "getmap" and cache[chat_id][message_id]['query'] == "userrecent":
                        bot.edit_message_text(text=getdata(cache[chat_id][message_id]['userrecentjson'][cache[chat_id][message_id]['list']]['beatmap_id'],"beatmap",query.data,chat_id=chat_id,message_id=message_id),reply_markup=back_to_query,chat_id=chat_id,message_id=message_id,parse_mode=ParseMode.HTML)
                        bot.answer_callback_query(query.id)
                        return   
                        
                    if query.data == "next":
                        if (cache[chat_id][message_id]['list'] + 1) >49:
                            bot.answer_callback_query(query.id,text="Out of range.")
                            return
                        else:
                            cache[chat_id][message_id]['list'] +=1
                        
                    if query.data == "prev":
                        if (cache[chat_id][message_id]['list'] - 1) <0:
                            bot.answer_callback_query(query.id,text="Out of range.")
                            return
                        else:
                            cache[chat_id][message_id]['list'] -=1

                    bot.edit_message_text(text=getdata(username,function,cache[chat_id][message_id]['mode'],chat_id=chat_id,message_id=message_id,list=cache[chat_id][message_id]['list']),reply_markup=select_keyboard,chat_id=chat_id,message_id=message_id,parse_mode=ParseMode.HTML)

                else:
                    
                    if function == "userinfo":

                        bot.edit_message_text(text=getdata(username,function,query.data,chat_id=chat_id,message_id=message_id),reply_markup=back_keyboard,chat_id=chat_id,message_id=message_id,parse_mode=ParseMode.HTML)

                    elif function == "userbest":

                        cache[chat_id][message_id]['mode'] = query.data
                        if "list" not in cache[chat_id][message_id]:
                            cache[chat_id][message_id]['list'] = 0
                        bot.edit_message_text(text=getdata(username,function,query.data,chat_id=chat_id,message_id=message_id,list=cache[chat_id][message_id]['list']),reply_markup=select_keyboard,chat_id=chat_id,message_id=message_id,parse_mode=ParseMode.HTML)

                    elif function == "userrecent":

                        cache[chat_id][message_id]['mode'] = query.data
                        if "list" not in cache[chat_id][message_id]:
                            cache[chat_id][message_id]['list'] = 0
                        bot.edit_message_text(text=getdata(username,function,query.data,chat_id=chat_id,message_id=message_id,list=cache[chat_id][message_id]['list']),reply_markup=select_keyboard,chat_id=chat_id,message_id=message_id,parse_mode=ParseMode.HTML)

            elif query.data == "menu":
                cache[chat_id][message_id]['query'] = ""
                cache[chat_id][message_id]['status'] = "mainmenu"
                bot.edit_message_text(text="Please choose feature: ",reply_markup=menu_keyboard,chat_id=chat_id,message_id=message_id)

        bot.answer_callback_query(query.id)

def userinfo(bot,update,args):
    if len(args) == 0:
        bot.sendMessage(update.message.chat_id, text="Usage: /userinfo <Username>")
        return
    else:
        username = " ".join(args)
        message_id = str(update.message.reply_text('Please choose Feature:', reply_markup=menu_keyboard).message_id)
        user_id = str(update.message.from_user.id)
        feature = "userinfo"
        chat_id = str(update.message.chat.id)
        if chat_id not in cache:
            cache[chat_id] = {}
        cache[chat_id][message_id] = { 'list' : 0 ,'mode' : '' , 'query' : '' , 'status' : 'mainmenu' , 'chat_id' : chat_id , 'message_id' : message_id , 'feature' : feature , 'user_id' : user_id , 'username' : username}

def beatmap(bot,update,args):
    if len(args) == 0:
        bot.sendMessage(update.message.chat_id, text="Usage: /beatmap <Beatmap ID>")
        return
    else:
        msg=getdata(args[0],"beatmap",0)
        update.message.reply_text(text=msg,parse_mode=ParseMode.HTML)

def help(bot, update):
    if(update.message.text == "/help@OSU_TG_Bot"):
        bot.sendMessage(update.message.chat_id, text='/userinfo <Mode> <ID> 取得玩家資訊\n/getbest <Mode> <ID> 取得玩家最佳成績\n/recentplay <Mode> <ID> 取得玩家最近遊玩\n<Mode>\n0:OSU\n1:Taiko\n2:Ctb\n3:Mania')

def ping(bot, update):
    bot.sendMessage(update.message.chat_id, text='pong')

def error(bot, update, error):
    logger.warn('Update "%s" caused error "%s"' % (update, error))

def main():
    updater = Updater(token)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("userinfo", userinfo,pass_args=True))
    dp.add_handler(CommandHandler("beatmap", beatmap,pass_args=True))
    dp.add_handler(CallbackQueryHandler(callback))
    dp.add_handler(RegexHandler("^ping$",ping))
    dp.add_error_handler(error)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
