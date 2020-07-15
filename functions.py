import robin_stocks as r
import time
import os
import platform
import requests
import pygame as s

s.mixer.init()
stocks = []
infoBar = [""]
totalEquity = 0.0
slowCheck, medCheck, fastCheck = 1800, 900, 450
percentage = [1.02, 1.05]
lowPercentage = [0.99, 0.98]
baseHigh = 1.2
baseLowCrypto = 0.98
baseLow = 1.01
risk = 0.18
adjust = 0
buyMode = 0
login = False
autoStart = 0
crazyCrypto = 1
buyPower = 0.0
init_hold = {}
init_crypto = []
updatedHolds = False
system = ""
favorite = "ERI"
clock = time.ctime().split()[3]
flagType = {"flag": False, "type": 0}
buyFlagType = {"flag": False, "type": 0}


def refresh():
    global system
    if system == "":
        system = platform.system()
    if system == "Windows":
        return os.system("CLS")
    elif system == "Linux":
        return os.system("clear")
    else:
        print("Error - System Unknown")


refresh()


def login():
    global buyPower, init_hold, login
    username = ""
    password = ""
    content = ""
    if login is False:
        try:
            file = open("credentials.txt", "r")
            content = file.readlines()
            username = content[0].strip("\n")
            password = content[1].strip("\n")
        except:
            username = input("Robinhood username: ")
            password = input("Robinhood password: ")
            file = open("credentials.txt", "w")
            file.write(username + "\n")
            file.write(password + "\n")
        r.login(username=username, password=password)
        print("Getting account information..")
        buyPower = float(r.profiles.load_account_profile(info="portfolio_cash"))
        update_holdings()
        print("Success!")
        login = True


def update_holdings():
    global init_hold, init_crypto
    init_hold = r.account.build_holdings(with_dividends=False)
    init_crypto = r.crypto.get_crypto_positions(info=None)


def clocks():
    global clock
    clock = time.ctime().split()[3]
    seconds = int(clock.split(":")[0])*3600
    seconds = seconds + int(clock.split(":")[1])*60
    seconds = seconds + int(clock.split(":")[2])
    return seconds


class Stock:
    global buyMode

    def __init__(self, name):
        print(" * adding " + name)
        h_total, l_total = [], []
        self.earnPercent = None
        self.nextActual = None
        self.name = name
        if name == "BTC" or name == "LTC":
            if crazyCrypto == 1:
                for data in r.crypto.get_crypto_historicals(name, interval="hour", span="day", info=None):
                    h_total.append(float(data["high_price"]))
                    l_total.append(float(data["low_price"]))
            else:
                for data in r.crypto.get_crypto_historicals(name, interval="hour", span="week", info=None):
                    h_total.append(float(data["high_price"]))
                    l_total.append(float(data["low_price"]))
            self.price = float(r.crypto.get_crypto_quote(name, info="mark_price"))
            self.high = max(h_total)
            self.low = min(l_total)
            for data in r.crypto.get_crypto_positions(info=None):
                if data["currency"]["code"] == name:
                    self.quantity = float(data["cost_bases"][0]["direct_quantity"])
                    if self.quantity > 0:
                        self.buy_price = float(data["cost_bases"][0]["direct_cost_basis"])/self.quantity
                        self.invested = True
                    else:
                        self.buy_price = self.low*baseLowCrypto
                        self.invested = False
            self.sell_price = self.buy_price*1.0005
            self.crypto = True
        else:
            self.crypto = False
            last_e = None
            last_a = None
            for data in r.stocks.get_earnings(name, info=None):
                if data["year"] == 2020 and data["eps"]["actual"] is not None and data["eps"]["estimate"] is not None:
                    last_e = float(data["eps"]["estimate"])
                    last_a = float(data["eps"]["actual"])
                elif data["year"] == 2020 and data["report"]["date"] is not None:
                    self.nextActual = data["report"]["date"]
            self.lastEstimate = last_e
            self.lastActual = last_a
            if self.lastActual is None:
                self.earnPercent = None
            else:
                self.earnPercent = self.lastActual/self.lastEstimate
            positions = r.stocks.get_stock_historicals(name, span="week", bounds="regular")
            for x in positions:
                h_total.append(float(x["high_price"]))
                l_total.append(float(x["low_price"]))
            self.high = max(h_total)
            self.low = min(l_total)
            self.price = 0
            try:
                self.quantity = float(init_hold[name]["quantity"])
                self.buy_price = float(init_hold[name]["average_buy_price"])
                self.sell_price = float(init_hold[name]["average_buy_price"])*baseHigh
                self.invested = True
                
            except KeyError:
                self.quantity = 0
                if buyMode == 0:
                    self.buy_price = self.low*baseLow
                if buyMode == 1:
                    self.buy_price = self.high*baseLow
                self.sell_price = self.buy_price*baseHigh
                self.invested = False
        w_list = watch_list()
        try:
            if w_list[name] != 0.0:
                self.sell_price = w_list[name]
        except KeyError:
            pass
        self.lastPrice = self.price
        self.open = float(r.get_fundamentals(name, info="open")[0])
        self.change = 0
        self.points = 0
        self.hourly_low = self.price
        self.sector = ""
        self.news = len(r.stocks.get_news(name, info=None))
        self.equity = self.quantity*self.price
        self.equityChange = self.equity - self.quantity*self.buy_price
        self.up = False
        self.down = False
        self.done_once = False
        self.x_down = 0
        self.x_up = 0
        self.max_up = 0
        if self.price == 0:
            self.gain = 0
        else:
            self.gain = self.high/self.price
        self.seconds = 0
        info = time.ctime().split()
        self.weekDay = info[0]
        self.lastUpdated = info[3]
        self.start_time = 0

    def set_open(self):
        self.open = float(r.get_fundamentals(self.name, info="open")[0])

    def set_gain(self):
        if self.price == 0:
            self.gain = 0
        else:
            self.gain = self.high/self.price
    
    def set_equity(self):
        self.equity = self.quantity*self.price
        self.equityChange = self.equity - self.quantity*self.buy_price

    def set_high(self, x):
        self.high = x
        self.max_up = 1

    def set_quantity(self, x):
        self.quantity = x

    def set_price(self, x):
        self.price = x
        info = time.ctime().split()
        self.weekDay = info[0]
        self.lastUpdated = info[3]

    def set_last_price(self):
        self.lastPrice = self.price

    def set_change(self):
        self.change = self.change + self.price-self.lastPrice

    def set_down(self):
        self.down = True
        self.x_down = self.x_down + 1
        if self.x_up != 0:
            self.x_up = self.x_up - 1

    def set_up(self):
        self.up = True
        self.x_up = self.x_up + 1
        if self.x_down != 0:
            self.x_down = self.x_down - 1

    def set_invested(self, x):
        self.invested = x
        if x is False:
            self.quantity = 0

    def reset(self):
        self.up = False
        self.down = False
        self.change = 0

    def stop_watch(self):
        if self.start_time == 0:
            self.seconds = 0
        else:
            self.seconds = clocks()+1-self.start_time


def sell_high(a_stock):
    global slowCheck, medCheck, fastCheck
    i = 0
    for data in stocks:
        if data.name == a_stock:
            break
        i = i + 1
    confirmation = "Nothing Happened"
    last_price = stocks[i].price
    start_time = clocks()
    check = False
    check_rate = slowCheck
    first, end_c = "\033[0m", "\033[0m"
    green, red, cyan = "\033[32m", "\033[31m", "\033[36m"
    eq1 = "\033[0m"
    while stocks[i].invested is True:
        if stocks[i].price > stocks[i].sell_price or check is False:
            refresh()
            print("{f}#####################{endL}".format(f=first, endL=end_c))
            print("{f}#         #{g}+{:7.2f}{f} #{endL}".format(stocks[i].high, endL=end_c, f=first, g=green))
            print("{f}#  {endL}{:^5}{f}  ###########{endL}".format(stocks[i].name, endL=end_c, f=first))
            print("{f}#         #{r}-{:7.2f}{f} #{endL}".format(stocks[i].low, endL=end_c, r=red, f=first))
            print("{f}#####################{endL}".format(f=first, endL=end_c))
            print("{f}# {c}{:7.2f}{endL} # {endL}{:7.2f}{f} #{endL}".format(stocks[i].price, stocks[i].sell_price, endL=end_c, c=cyan, f=first))
            print("{f}#####################{endL}".format(f=first, endL=end_c))
            print("{f}# {endL}{:7.2f}{endL} # {e1}{:7.2f}{f} #{endL}".format(stocks[i].buy_price, stocks[i].equityChange, endL=end_c,f=first, e1=eq1))
            print("{f}#####################{endL}".format(f=first, endL=end_c))
            print("")
            print("Last price: " + str(last_price))
            print("Time till next check: " + str(check_rate-((clocks()+1)-start_time) % check_rate))
            if ((clocks()+1)-start_time) % check_rate != 0:
                check = False
                print(str(((clocks()+1)-start_time) % check_rate))
            if ((clocks()+1)-start_time) % check_rate == 0 and check is False:
                check_rate = slowCheck
                if stocks[i].price > stocks[i].sell_price*percentage[0]:
                    check_rate = medCheck
                    print("medCheck wait time: " + str(medCheck) + " seconds")
                else:
                    print("slowCheck wait time: " + str(slowCheck) + " seconds")
                if stocks[i].price > stocks[i].sell_price*percentage[1]:
                    check_rate = fastCheck
                check = True
                if last_price > stocks[i].price:
                    if stocks[i].crypto is False:
                        confirmation = r.order_sell_market(stocks[i].name, stocks[i].quantity, timeInForce="gfd", extendedHours=True)
                    else:
                        if stocks[i].price-15 < stocks[i].sell_price:
                            return confirmation
                        confirmation = r.order_sell_crypto_limit(stocks[i].name, float("{:.8f}".format(stocks[i].quantity)), float("{:.2f}".format(stocks[i].price-15)), timeInForce="gtc")
                    stocks[i].set_invested(False)
                    minus_watchlist(a_stock)
                    add_watchlist(a_stock)
                    read_settings()
                    return confirmation
                last_price = stocks[i].price
                s.mixer.music.load("alarm.mp3")
                s.mixer.music.play()
            elif stocks[i].price < stocks[i].sell_price and check is True:
                return confirmation
        update_stocks()


# def manBuy(a_stock):
#     todo

def quick_sell_all():
    refresh()
    global stocks
    for data in stocks:
        if data.quantity > 0:
            confirmation = r.order_sell_market(data.name, data.quantity, timeInForce="gfd", extendedHours=True)
    reset()
    update_holdings()
    return confirmation


def man_sell_all():
    refresh()
    global stocks, flagType, crazyCrypto
    success = 0
    failed = 0
    for data in stocks:
        if flagType[data.sector] <= 0:
            continue
        confirmation = "Nothing Happened"
        if data.invested is True and data.price >= data.buy_price:  # re-add price >= buy price
            confirmation = r.order_sell_market(data.name, data.quantity, timeInForce="gfd", extendedHours=True)
            crazyCrypto = 1  # stop buying of stocks while market crash
        if confirmation != "Nothing Happened":
            success = success + 1
        else:
            failed = failed + 1
        if failed > 0:
            flagType["flag"] = True
        else:
            flagType["flag"] = False
        print(str(success)+" sold successfully!")
        print(str(failed)+" attempt failed")
        print("")
        time.sleep(30)
        reset()
        update_holdings()
        return confirmation


def man_buy_all():  # todo create a function that will buy on up trend day
    refresh()
    global stocks, flagType, crazyCrypto, favorite, risk, totalEquity, buyPower
    success = 0
    failed = 0
    diverse = totalEquity * risk
    for data in stocks:
        if buyFlagType[data.sector] <= 0:
            continue
        confirmation = "Nothing Happened"
        if data.invested is False and data.name == favorite:  # re-add price >= buy price
            qty = int(diverse / data.price)
            confirmation = r.order_buy_market(data.name, data.quantity, timeInForce="gfd", extendedHours=True)
        if confirmation != "Nothing Happened":
            success = success + 1
        else:
            failed = failed + 1
        if failed > 0:
            buyFlagType["flag"] = True
        else:
            buyFlagType["flag"] = False
        print(str(success)+" sold successfully!")
        print(str(failed)+" attempt failed")
        print("")
        time.sleep(15)
        reset()
        update_holdings()
        return confirmation


def buy_low(a_stock):
    global stocks, risk, totalEquity, buyPower, slowCheck, medCheck, fastCheck
    i = 0
    if crazyCrypto == 1:
        r.cancel_all_crypto_orders()
    for data in stocks:
        if data.name == a_stock:
            break
        i = i + 1
    confirmation = "Nothing Happened"
    diverse = totalEquity*risk
    check = False
    check_rate = slowCheck
    start_time = clocks()
    last_price = stocks[i].price
    first, end_c, green, red, cyan, eq1 = "\033[0m", "\033[0m", "\033[32m", "\033[31m", "\033[36m", "\033[0m"
    while stocks[i].invested is False:
        refresh()
        if stocks[i].price <= stocks[i].buy_price:
            print("{f}#####################{endL}".format(f=first, endL=end_c))
            print("{f}#         #{g}+{:8.2f}{f}#{endL}".format(stocks[i].high, endL=end_c, f=first, g=green))
            print("{f}#  {endL}{:^5}{f}  ###########{endL}".format(stocks[i].name, endL=end_c, f=first))
            print("{f}#         #{r}-{:8.2f}{f}#{endL}".format(stocks[i].low, endL=end_c, r=red, f=first))
            print("{f}#####################{endL}".format(f=first, endL=end_c))
            print("{f}# {c}{:7.2f}{endL} # {endL}{:8.2f}{f}#{endL}".format(stocks[i].price, stocks[i].sell_price, endL=end_c, c=cyan, f=first))
            print("{f}#####################{endL}".format(f=first, endL=end_c))
            print("{f}# {endL}{:7.2f}{endL} # {e1}{:8.2f}{f}#{endL}".format(stocks[i].buy_price, stocks[i].equityChange, endL=end_c, f=first, e1=eq1))
            print("{f}#####################{endL}".format(f=first,endL=end_c))
            print("")
            first = "\033[0m"
            print("Time till next check: " + str(check_rate - (clocks()-start_time) % check_rate))
            print("Wait time: " + str(check_rate) + " seconds")
            if (clocks()-start_time) % check_rate != 0:
                check = False
            if (clocks()-start_time) % check_rate == 0 and check is False:
                check_rate = slowCheck
                if stocks[i].price < stocks[i].buy_price*lowPercentage[0]:
                    check_rate = medCheck
                if stocks[i].price < stocks[i].buy_price*lowPercentage[1]:
                    check_rate = fastCheck
                check = True
                if last_price < stocks[i].price:
                    if stocks[i].crypto is False:
                        qty = int(diverse/stocks[i].price)
                        confirmation = r.order_buy_market(stocks[i].name, qty, timeInForce="gtc", extendedHours=True)
                        read_settings()
                    else:
                        if stocks[i].price+15 > stocks[i].buy_price:
                            return confirmation
                        f_qty = float(diverse/(stocks[i].price*1.01))
                        confirmation = r.order_buy_crypto_limit(stocks[i].name, float("{:.8f}".format(f_qty)), float("{:.2f}".format(stocks[i].price+15)), timeInForce="gtc")
                        read_settings()
                    stocks[i].set_invested(True)
                    update_holdings()
                    return confirmation
                last_price = stocks[i].price
                s.mixer.music.load("alarm.mp3")
                s.mixer.music.play()
            elif stocks[i].price > stocks[i].buy_price and check is True:
                stocks[i].set_invested(False)
                return confirmation

        update_stocks()


def watch_list():
    file = open("info.txt", "r")
    w_list = {}
    content = file.readlines()
    file.close()
    for data in content:
        sep = data.split()
        w_list[sep[0].strip()] = float(sep[1].strip())
    return w_list


def add_watchlist(ticker):
    if ticker == "":
        return
    w_list = watch_list()
    w_list[ticker.upper()] = 0.0
    file = open("info.txt", "w")
    for data in w_list:
        file.write(data + " " + str(w_list[data]) + "\n")
    file.close()


def minus_watchlist(ticker):
    if ticker == "":
        return
    w_list = watch_list()
    in_list = False
    for data in w_list:
        if data == ticker.upper():
            in_list = True
    if in_list is False:
        print("Ticker was not found")
    else:
        w_list.pop(ticker.upper())
    file = open("info.txt", "w")
    if len(w_list) == 0:
        file.close()
        return
    for data in w_list:
        file.write(data + " " + str(w_list[data]) + "\n")
    file.close()


def move_watchlist(ticker):
    if ticker == "":
        return
    w_list = watch_list()
    temp = []
    temp2 = []
    in_list = False
    i = 0
    index = 0
    for data in w_list:
        temp.append(data)
        temp2.append(w_list[data])
        if data == ticker.upper():
            in_list = True
            i = index
        index = index + 1
    if in_list is False:
        print("Ticker was not found")
    temp.insert(0, temp.pop(i))
    temp2.insert(0, temp2.pop(i))
    i = 0
    file = open("info.txt", "w")
    for data in temp:
        file.write(data + " " + str(temp2[i]) + "\n")
        i = i + 1
    file.close()


def fake_news(ticker):
    global stocks, infoBar
    i = 0
    for data in stocks:
        if data.name == ticker:
            break
        else:
            i = i+1
    news = r.stocks.get_news(ticker, info=None)
    if len(news) > stocks[i].news:
        s.mixer.music.load("mail.mp3")
        s.mixer.music.play()
        infoBar.insert(0, news[0]["title"])
        stocks[i].news = len(news)


def get_account_info():
    while True:
        print("Load Account balance")
        print("Get order history")
        print("Total Investing")
        account = r.profiles.load_account_profile(info=None)
        port = r.profiles.load_portfolio_profile(info=None)
        print(account)
        print(port)
        input("")


def auto_buy__sell__crypto():
    get_update()
#    update_stocks()
    # point system
    
    # ratings
#    print(r.stocks.get_ratings(stocks[2].name, info="summary")["num_sell_ratings"])
#    # weekday
#    print(stocks[2].weekDay)
#    # abovebuy
#    print(stocks[2].buy_price)
#    # abovesell
#    print(stocks[2].sell_price)
#    # meets quarterly earnings
#    print(stocks[2].earnPercent)
    # uptrend 2 boogoo
    # this is a test
    # downtrend 2 fuckme
#    print(flagType[stocks[2].sector])


def update_stocks():
    global stocks, flagType, clock, updatedHolds, buyPower, init_hold, infoBar, totalEquity, init_crypto, adjust
    tickers = {}
    if clocks() % 300 == 0:
        update_holdings()
    for data in init_crypto:  # Grabs invested Crypto tickers
        if float(data["cost_bases"][0]["direct_quantity"]) > 0:
            tickers[data["currency"]["code"]] = ""
    tick = []
    for data in init_hold:  # Grabs invested Stocks
        tickers[data] = ""
    w_list = watch_list()
    for data in w_list:  # fills list with watchlist
        tickers[data] = ""
    if len(stocks) == len(tickers):  # if already initialized
        for data in stocks:
            if data.crypto is False:
                tick.append(data.name)
    else:  # remake stocks list
        stocks.clear()
        for data in tickers:
            if data == "BTC" or data == "LTC":
                stocks.insert(0, Stock(data))
            else: # making list while separating crypto for price
                stocks.append(Stock(data))
                tick.append(data)
    c=0
    totalEquity = 0
    temp = None
    stock_type = []
    done = False
    price = r.stocks.get_latest_price(tick, includeExtendedHours=True)
    for data in stocks:
        if data.crypto is True:
            for x in init_crypto:
                if x["currency"]["code"] == data.name:
                    data.set_quantity(float(x["cost_bases"][0]["direct_quantity"]))
                if data.quantity > 0:
                    temp = float(r.crypto.get_crypto_quote(data.name, info="bid_price"))
                else:
                    temp = float(r.crypto.get_crypto_quote(data.name, info="ask_price"))
                    data.invested = False
            if temp is None:
                temp = data.price
            price.insert(c, temp)
            stock_type.insert(c, "Crypto Currency")
            c = c+1
        else:
            break
    i = 0
    buy_points = 0
    flag_points = 0
    owned_flags = 0
    fav_flags = 0
    x = 0
    total_owned = 0
    num_stocks = len(stocks)
    len_price = len(price)
    for data in stocks:
        if data.sector == "" and done is False:
            for sec in r.stocks.get_fundamentals(tick, info="sector"):
                stock_type.append(sec)
            done = True
        if done is True:
            data.sector = stock_type[i]
            flagType[data.sector] = 0
            buyFlagType[data.sector] = 0
        if data.x_down >= 2:
            flagType[data.sector] = flagType[data.sector] + 1
            flag_points = flag_points + 1
            if data.invested is True:
                owned_flags = owned_flags + 1
        else:
            flagType[data.sector] = flagType[data.sector] - 1
            if data.invested is True:
                x = x + 1
                total_owned = x + owned_flags
        if data.x_up >= 1:
            buyFlagType[data.sector] = buyFlagType[data.sector] + 1
            buy_points = buy_points + 1
            if data.name == favorite:
                fav_flags = fav_flags + 1
        if clocks() % 330 == 0:
            fake_news(data.name)
        data.set_last_price()
        data.set_gain()
        data.stop_watch()
        if len_price == num_stocks:
            data.set_price(float(price[i]))
        if data.lastPrice != 0:
            data.set_change()
        data.set_equity()
        totalEquity = totalEquity + data.equity
        i = i+1
    if flag_points >= int(num_stocks/2):
        if owned_flags >= total_owned:
            flagType["flag"] = True
    if buy_points >= int(num_stocks/2):
        if fav_flags >= 1:
            buyFlagType["flag"] = True
    if adjust == 1:  # Need a setting for this
        i = 0
        for data in stocks:
            if i == len(stocks)-2:
                break
            if data.crypto is True:
                i = i+1
                continue
            elif stocks[i+1].quantity > 0:
                stocks[i], stocks[i+1] = stocks[i+1], stocks[i]
                i = i+1
            elif stocks[i].gain < stocks[i+1].gain:
                if stocks[i].quantity > 0:
                    i = i+1
                    continue
                stocks[i], stocks[i+1] = stocks[i+1], stocks[i]
                i = i+1
            else:
                i = i+1
    if flag_points >= buy_points:
        infoBar.insert(0, "Threat level: " + str(flag_points)+ "/" + str(int(num_stocks/2)))
    else:
        infoBar.insert(0, "Buy level:    " + str(buy_points) + "/" + str(int(num_stocks / 2)))
    totalEquity = totalEquity + buyPower


def get_current_stocks():
    global stocks, infoBar, flagType, clock, totalEquity
    first, second, third, fourth, fifth, end_c, eq1, eq2, eq3, eq4, eq5 = "\033[0m", "\033[0m", "\033[0m", "\033[0m", "\033[0m", "\033[0m", "\033[0m", "\033[0m", "\033[0m", "\033[0m", "\033[0m"
    green, red, cyan = "\033[32m", "\033[31m", "\033[36m"
    seconds = [0, 0, 0, 0, 0, 0]
    refresh()
    print("Initializing..")
    login()
    update_stocks()
    clock = time.ctime().split()[3]
    i = 0
    refresh()
    green = "\033[32m"
    print("                                                   \033[93m$     {g}{:8.2f}      \033[93m$\033[0m                                        {:8}".format(totalEquity, clock, g=green))
    while True:
        clock = time.ctime().split()[3]
        if stocks[i].change > stocks[i].open*0.01:
            stocks[i].set_up()
            if stocks[i].crypto is False:
                stocks[i].stop_watch()
            if stocks[i].quantity > 0:
                s.mixer.music.load("boogoo.mp3")
                s.mixer.music.play()
        if stocks[i].seconds > 300 or stocks[i].x_down == 0:
            stocks[i].x_down = 0
            stocks[i].start_time = 0
        if stocks[i].change < -(stocks[i].open*0.01):
            stocks[i].set_down()
            stocks[i].start_time = clocks()
            if stocks[i].quantity > 0:
                s.mixer.music.load("fuckme.mp3")
                s.mixer.music.play()
                if stocks[i].max_up == 1 and stocks[i].x_down == 1:
                    quick_sell_all()
                    return get_current_stocks()
        if stocks[i].price > stocks[i].high:
            stocks[i].set_high(stocks[i].price)
        if int(clock.split(":")[1])%30 == 0 and stocks[i].done_once is False and stocks[i].crypto is True and stocks[i].invested is False:
            stocks[i].buy_price = stocks[i].hourly_low
            stocks[i].sell_price = stocks[i].buy_price*1.0005
            stocks[i].hourly_low = stocks[i].price
            stocks[i].done_once = True
        if int(clock.split(":")[1])%31 == 0:
            stocks[i].done_once = False
        if stocks[i].price < stocks[i].hourly_low and stocks[i].crypto is True and stocks[i].invested is False:
            stocks[i].hourly_low = stocks[i].price
        if int(clock.split(":")[0]) >= 7 or (int(clock.split(":")[0]) == 6 and int(clock.split(":")[1]) >= 30):
            if int(clock.split(":")[0]) == 6 and int(clock.split(":")[1]) <= 35:
                if buyFlagType["flag"] is True:
                    man_buy_all()
                    return get_current_stocks()
            else:
                stocks[i].x_up = 0
            if flagType["flag"] is True:
                man_sell_all()
                return get_current_stocks()
            if stocks[i].price > stocks[i].sell_price and stocks[i].quantity > 0 and stocks[i].change != 0:
                s.mixer.music.load("alarm.mp3")
                s.mixer.music.play()
                print(sell_high(stocks[i].name))  # Sell
                if stocks[i].invested is False and stocks[i].hourly_low != 0 and stocks[i].crypto == True:
                    if stocks[i].sell_price-20 > stocks[i].hourly_low:
                        stocks[i].hourly_low = stocks[i].hourly_low*.995
                    stocks[i].buy_price = stocks[i].hourly_low
                    stocks[i].sell_price = stocks[i].buy_price*baseHigh
            if i >= len(stocks) - 1 and buyPower > totalEquity*risk:
                potential_buys = {}
                for data in stocks:
                    if crazyCrypto == 1:
                        break  # temp turn off all sell activity
                    if crazyCrypto == 1 and data.crypto is False:
                        continue
                    if data.price < data.buy_price and data.quantity == 0 and data.invested is False:  # this turns off crypto for now
                        potential_buys[data.name] = data.high/data.price  # get potential gainz
                if len(potential_buys) > 0:
                    best = max(potential_buys, key=potential_buys.get)
                    s.mixer.music.load("alarm.mp3")
                    s.mixer.music.play()
                    print(buy_low(best))  # Buy
        last_eye = i
        if (i+1) % 5 == 0 and i < 16:
            i= i - 4
            if seconds[1]-seconds[0] > 5 or seconds[1] == 0:
                first = "\033[93m" if stocks[i].quantity > 0 else "\033[0m"
                seconds[1] = 0
            if seconds[2]-seconds[0] > 5 or seconds[2] == 0:
                second = "\033[93m" if stocks[i+1].quantity > 0 else "\033[0m"
                seconds[2] = 0
            if seconds[3]-seconds[0] > 5 or seconds[3] == 0:
                third = "\033[93m" if stocks[i+2].quantity > 0 else "\033[0m"
                seconds[3] = 0
            if seconds[4]-seconds[0] > 5 or seconds[4] == 0:
                fourth = "\033[93m" if stocks[i+3].quantity > 0 else "\033[0m"
                seconds[4] = 0
            if seconds[5]-seconds[0] > 5 or seconds[5] == 0:
                fifth = "\033[93m" if stocks[i+4].quantity > 0 else "\033[0m"
                seconds[5] = 0
            first = "\033[35m" if stocks[i].crypto is True else first
            second = "\033[35m" if stocks[i+1].crypto is True else second
            third = "\033[35m" if stocks[i+2].crypto is True else third
            fourth = "\033[35m" if stocks[i+3].crypto is True else fourth
            fifth = "\033[35m" if stocks[i+4].crypto is True else fifth
            eq1 = red if stocks[i].equityChange < 0 else "\033[0m"
            eq1 = green if stocks[i].equityChange > 0 else eq1
            eq2 = red if stocks[i+1].equityChange < 0 else "\033[0m"
            eq2 = green if stocks[i+1].equityChange > 0 else eq2
            eq3 = red if stocks[i+2].equityChange < 0 else "\033[0m"
            eq3 = green if stocks[i+2].equityChange > 0 else eq3
            eq4 = red if stocks[i+3].equityChange < 0 else "\033[0m"
            eq4 = green if stocks[i+3].equityChange > 0 else eq4
            eq5 = red if stocks[i+4].equityChange < 0 else "\033[0m"
            eq5 = green if stocks[i+4].equityChange > 0 else eq5
            seconds = [int(clock.split(":")[2]), 0, 0, 0, 0, 0]
            if stocks[i].up is True:
                seconds[1] = seconds[0]
                first = "\033[32m"
                stocks[i].reset()
            if stocks[i].down is True:
                seconds[1] = seconds[0]
                first = "\033[31m"
                stocks[i].reset()
            if stocks[i+1].up is True:
                seconds[1] = seconds[0]
                second = "\033[32m"
                stocks[i+1].reset()
            if stocks[i+1].down is True:
                seconds[1] = seconds[0]
                second = "\033[31m"
                stocks[i+1].reset()
            if stocks[i+2].up is True:
                seconds[1] = seconds[0]
                third = "\033[32m"
                stocks[i+2].reset()
            if stocks[i+2].down is True:
                seconds[1] = seconds[0]
                third = "\033[31m"
                stocks[i+2].reset()
            if stocks[i+3].up is True:
                seconds[1] = seconds[0]
                fourth = "\033[32m"
                stocks[i+3].reset()
            if stocks[i+3].down is True:
                seconds[1] = seconds[0]
                fourth = "\033[31m"
                stocks[i+3].reset()
            if stocks[i+4].up is True:
                seconds[1] = seconds[0]
                fifth = "\033[32m"
                stocks[i+4].reset()
            if stocks[i+4].down is True:
                seconds[1] = seconds[0]
                fifth = "\033[31m"
                stocks[i+4].reset()
            print("")
            print("   {f}#####################{endL}   {s}#####################{endL}   {t}#####################{endL}   {n}#####################{endL}   {n1}#####################{endL}".format(f=first, s=second, t=third, n=fourth, n1=fifth, endL=end_c))
            print("   {f}#         #{g}+{:8.2f}{f}#{endL}   {s}#         #{g}+{:8.2f}{s}#{endL}   {t}#         #{g}+{:8.2f}{t}#{endL}   {n}#         #{g}+{:8.2f}{n}#{endL}   {n1}#         #{g}+{:8.2f}{n1}#{endL}".format(stocks[i].high, stocks[i+1].high, stocks[i+2].high, stocks[i+3].high, stocks[i+4].high, endL=end_c, f=first, g=green, s=second, t=third, n=fourth, n1=fifth))
            print("   {f}#  {endL}{:^5}{f}  ###########{endL}   {s}#  {endL}{:^5}{s}  ###########{endL}   {t}#  {endL}{:^5}{t}  ###########{endL}   {n}#  {endL}{:^5}{n}  ###########{endL}   {n1}#  {endL}{:^5}{n1}  ###########{endL}".format(stocks[i].name, stocks[i+1].name, stocks[i+2].name, stocks[i+3].name, stocks[i+4].name, endL=end_c, f=first, s=second, t=third, n=fourth, n1=fifth))
            print("   {f}#         #{r}-{:8.2f}{f}#{endL}   {s}#         #{r}-{:8.2f}{s}#{endL}   {t}#         #{r}-{:8.2f}{t}#{endL}   {n}#         #{r}-{:8.2f}{n}#{endL}   {n1}#         #{r}-{:8.2f}{n1}#{endL}".format(stocks[i].low, stocks[i+1].low, stocks[i+2].low, stocks[i+3].low, stocks[i+4].low, endL=end_c, r=red, f=first, s=second, t=third, n = fourth, n1=fifth))
            print("   {f}#####################{endL}   {s}#####################{endL}   {t}#####################{endL}   {n}#####################{endL}   {n1}#####################{endL}".format(f=first, s=second, t=third,n=fourth,n1=fifth, endL=end_c))
            print("   {f}# {c}{:8.2f}{f}# {endL}{:8.2f}{f}#{endL}   {s}# {c}{:8.2f}{s}# {endL}{:8.2f}{s}#{endL}   {t}# {c}{:8.2f}{t}# {endL}{:8.2f}{t}#{endL}   {n}# {c}{:8.2f}{n}# {endL}{:8.2f}{n}#{endL}   {n1}# {c}{:8.2f}{n1}# {endL}{:8.2f}{n1}#{endL}".format(stocks[i].price, stocks[i].sell_price, stocks[i+1].price, stocks[i+1].sell_price, stocks[i+2].price, stocks[i+2].sell_price, stocks[i+3].price, stocks[i+3].sell_price, stocks[i+4].price, stocks[i+4].sell_price, endL=end_c, c=cyan, f=first, s=second, t=third, n=fourth, n1=fifth))
            print("   {f}#####################{endL}   {s}#####################{endL}   {t}#####################{endL}   {n}#####################{endL}   {n1}#####################{endL}".format(f=first, s=second, t=third, n=fourth, n1=fifth, endL=end_c))
            print("   {f}# {endL}{:8.2f}{f}# {e1}{:8.2f}{f}#{endL}   {s}# {endL}{:8.2f}{s}# {e2}{:8.2f}{s}#{endL}   {t}# {endL}{:8.2f}{t}# {e3}{:8.2f}{t}#{endL}   {n}# {endL}{:8.2f}{n}# {e4}{:8.2f}{n}#{endL}   {n1}# {endL}{:8.2f}{n1}# {e5}{:8.2f}{n1}#{endL}".format(stocks[i].buy_price, stocks[i].equityChange, stocks[i+1].buy_price, stocks[i+1].equityChange, stocks[i+2].buy_price, stocks[i+2].equityChange, stocks[i+3].buy_price, stocks[i+3].equityChange, stocks[i+4].buy_price, stocks[i+4].equityChange, endL=end_c, f=first, s=second, t=third, n=fourth, n1=fifth, e1=eq1, e2=eq2, e3=eq3, e4=eq4, e5=eq5))
            print("   {f}#####################{endL}   {s}#####################{endL}   {t}#####################{endL}   {n}#####################{endL}   {n1}#####################{endL}".format(f=first, s=second, t=third, n=fourth, n1=fifth, endL=end_c))
        i = last_eye
        first, second, third, fourth, fifth, end_c, eq1, eq2, eq3, eq4, eq5 = "\033[0m", "\033[0m", "\033[0m", "\033[0m", "\033[0m", "\033[0m", "\033[0m", "\033[0m", "\033[0m", "\033[0m", "\033[0m"
        if i >= len(stocks) - 1:
            i = -1
            debug()
            if int(clock.split(":")[1]) % 5 == 0 and len(infoBar) > 1:
                infoBar.pop(0)
            update_stocks()
            refresh()
            print("   {:46.35}  \033[93m$     {g}{:8.2f}      \033[93m$\033[0m                                        {:8}".format(infoBar[0], totalEquity, clock, g=green))
        i = i + 1


def customize_settings():
    global percentage,lowPercentage,baseHigh,baseLow,slowCheck,medCheck,fastCheck,risk,crazyCrypto,baseLowCrypto,adjust, favorite, autoStart
    print("Welcome to my automated stock trading program!")
    print("This program uses a three check system to let the program know how valuable a stock is")
    print("First check is your sell_price/buy_price and second and third check is a percentage of that")
    print("As the program proceeds through the checks it will refresh the information faster")
    print("Here you can adjust the different specifications on trading stocks")
    print("Here are the current settings:")
    print("baseLow=\033[93m" + str(baseLow) + "\033[0m  --this is multiplied by all the stocks week lows to determine their buy_price")
    print("baseHigh=\033[93m" + str(baseHigh) + "\033[0m  --this is multiplied by the original buy_price to determine the sell_price")
    print("Percentage1=\033[93m" + str(percentage[0]) + "\033[0m  --this is multiplied by your sell_price to activate the 'MediumCheck'")
    print("Percentage2=\033[93m" + str(percentage[1]) + "\033[0m  --this is multiplied by your sell_price to activate the 'FastCheck'")
    print("LowPercentage1=\033[93m" + str(lowPercentage[0]) + "\033[0m  --this is multiplied by your buy_price to activate the 'MediumCheck'")
    print("LowPercentage2=\033[93m" + str(lowPercentage[1]) + "\033[0m  --this is multiplied by your buy_price to activate the 'FastCheck'")
    print("SlowCheck=\033[93m" + str(slowCheck) + "\033[0m  --this is the waiting period of the first check in seconds")
    print("MediumCheck=\033[93m" + str(medCheck) + "\033[0m  --this is the waiting period of the second check in seconds")
    print("FastCheck=\033[93m" + str(fastCheck) + "\033[0m  --this is the waiting period of the third check in seconds")
    print("risk=\033[93m" + str(risk) + "\033[0m  --this is the percentage of your capital investment on a single stock")
    print("crazyCrypto=\033[93m" + str(crazyCrypto) + "\033[0m  --Experimental Mode: Crypto Currency Only {False : 0}{True : 1}")
    print("baseLowCrypto=\033[93m" + str(baseLowCrypto) + "\033[0m  --Determine Cypto buy_price: Multiply by the high")
    print("adjust=\033[93m" + str(adjust) + "\033[0m  --Adjusts display dynamically {Manual : 0} {Dynamic : 1} {RevDynamic : 2}")
    print("favorite=\033[93m" + str(favorite) + "\033[0m  --Set favorite stock for auto buy")
    print("autoStart=\033[93m" + str(autoStart) + "\033[0m  --Set program autostart {On : 1} {Off : 0}")
    option = input("Would you like to adjust these?(y/n)")
    if option.lower() == "n":
        return
    elif option.lower() == "baselow":
        baseLow = float(input("baseLow="))
    elif option.lower() == "basehigh":
        baseHigh = float(input("baseHigh="))
    elif option.lower() == "percentage1":
        percentage[0] = float(input("Percentage1="))
    elif option.lower() == "percentage2":
        percentage[1] = float(input("Percentage2="))
    elif option.lower() == "lowpercentage1":
        lowPercentage[0] = float(input("LowPercentage1="))
    elif option.lower() == "lowpercentage2":
        lowPercentage[1] = float(input("LowPercentage2="))
    elif option.lower() == "slowcheck":
        slowCheck = int(input("SlowCheck="))
    elif option.lower() == "mediumcheck":
        medCheck = int(input("MediumCheck="))
    elif option.lower() == "fastcheck":
        fastCheck = int(input("FastCheck="))
    elif option.lower() == "risk":
        risk = float(input("risk="))
    elif option.lower() == "crazycrypto":
        crazyCrypto = int(input("crazyCrypto="))
    elif option.lower() == "baselowcrypto":
        baseLowCrypto = float(input("baseLowCrypto="))
    elif option.lower() == "adjust":
        adjust = int(input("adjust="))
    elif option.lower() == "favorite":
        favorite = str(input("favorite="))
    elif option.lower() == "autostart":
        autoStart = int(input("autoStart="))
    else:
        print("")
        baseLow = float(input("baseLow="))
        baseHigh = float(input("baseHigh=")) 
        percentage[0] = float(input("Percentage1="))
        percentage[1] = float(input("Percentage2="))
        lowPercentage[0] = float(input("LowPercentage1="))
        lowPercentage[1] = float(input("LowPercentage2="))
        slowCheck = int(input("SlowCheck="))
        medCheck = int(input("MediumCheck="))
        fastCheck = int(input("FastCheck="))
        risk = float(input("risk="))
        crazyCrypto = int(input("crazyCryto="))
        baseLowCrypto = float(input("baseLowCryto="))
        adjust = int(input("adjust="))
        favorite = str(input("favorite="))
        autoStart = int(input("adjust="))
        print("")
    update_settings()


def read_settings():
    global percentage,lowPercentage,baseHigh,baseLow,slowCheck,medCheck,fastCheck,risk,crazyCrypto,baseLowCrypto,adjust, favorite, autoStart
    file = open("settings.txt","r")
    content = file.readlines()
    file.close()
    setting = []
    for data in content:
        pair = data.split("=")
        try:
            setting.append(float(pair[1]))
        except:
            favorite = pair[1].strip("\n")
    if len(content) == 0:
        return
    percentage[0] = setting[0]
    percentage[1] = setting[1]
    lowPercentage[0] = setting[2]
    lowPercentage[1] = setting[3]
    slowCheck = int(setting[4])
    medCheck = int(setting[5])
    fastCheck = int(setting[6])
    baseLow = setting[7]
    baseHigh = setting[8]
    risk = setting[9]
    crazyCrypto = int(setting[10])
    baseLowCrypto = float(setting[11])
    adjust = int(setting[12])
    autoStart = int(setting[13])


def check_info():
    try:
        file = open('info.txt', 'r')
    except:
        file = open('info.txt', 'w')
    try:
        content = file.readlines()
    except:
        return 0
    clen = len(content)
    if clen < 15:
        print("You need at least 15 stocks in your watchlist")
        print("Stocks in watchlist: " + str(clen) + "/15")
    return clen


def update_settings():
    global percentage, lowPercentage, baseHigh, baseLow, slowCheck, medCheck, fastCheck, risk, crazyCrypto, baseLowCrypto,adjust, favorite, autoStart
    file = open("settings.txt", "w")
    file.write("Percentage1="+ str(percentage[0]) + "\n")
    file.write("Percentage2="+ str(percentage[1])+ "\n")
    file.write("LowPercentage1="+ str(lowPercentage[0]) + "\n")
    file.write("LowPercentage2="+ str(lowPercentage[1])+ "\n")
    file.write("SlowCheck="+ str(slowCheck) + "\n")
    file.write("MediumCheck="+ str(medCheck) + "\n")
    file.write("FastCheck="+ str(fastCheck) + "\n")
    file.write("baseLow="+ str(baseLow) + "\n")
    file.write("baseHigh="+ str(baseHigh) + "\n")
    file.write("risk="+ str(risk) + "\n")
    file.write("crazyCrypto="+ str(crazyCrypto) + "\n")
    file.write("baseLowCrypto=" + str(baseLowCrypto) + "\n")
    file.write("adjust=" + str(adjust) + "\n")
    file.write("favorite=" + str(favorite) + "\n")
    file.write("autoStart=" + str(autoStart) + "\n")
    file.close()


def reset():
    global stocks
    stocks.clear()


def debug():
    global stocks
    file = open("debug.txt", "w")
    for data in stocks:
        file.write("-----------------")
        file.write("Stock="+ str(data.name) + "\n")
        file.write("Gain="+ str(data.gain)+ "\n")
        file.write("Seconds="+ str(data.seconds) + "\n")
        file.write("Starttime="+ str(data.start_time)+ "\n")
        file.write("Sector="+ str(data.sector) + "\n")
        file.write("DownCount="+ str(data.x_down) + "\n")
        file.write("done_once="+ str(data.done_once) + "\n")
    file.close()


def customize_triggers():
    while True:
        refresh()
        print("1: Settings")
        print("2: Remove from watchlist")
        print("3: Add to watchlist")
        print("4: Move ticker to top")
        print("5: Exit")
        option = int(input("Please enter a value: "))
        if option == 1:
            refresh()
            customize_settings()
        elif option == 2:
            refresh()
            tick = "value"
            while tick != "":
                print("Watchlist: ")
                for data in watch_list():
                    print(data)   
                tick = input("Enter a ticker: ")
                refresh()
                minus_watchlist(tick)
        elif option == 3:
            refresh()
            tick = "value"
            while tick != "":
                print("Watchlist: ")
                for data in watch_list():
                    print(data)   
                tick = input("Enter a ticker: ")
                refresh()
                add_watchlist(tick)
        elif option == 4:
            refresh()
            tick = "value"
            while tick != "":
                print("Current Watchlist: ")
                for data in watch_list():
                    print(data)
                tick = input("Enter a ticker: ")
                refresh()
                move_watchlist(tick)
        elif option == 5:
            refresh()
            break
        elif option == 6:
            refresh()
            fake_news(input("Ticker: "))
        else:
            print("Unknown Error Occured")


def check_update():
    current_size = 0
    current_stock = 0
    current_version = requests.get("https://raw.github.com/joelspiers/stonks/master/stockalert.py")
    stock_alert = open("stockalert.py", "rb")
    content = stock_alert.read()
    current_size = len(current_version.content)
    for data in content:
        current_stock = current_stock + 1
    print(current_size)
    print(current_stock)
    time.sleep(10)
    stock_alert.close()


def get_update():
    print("*Backing up old files")
    backup1 = open("stockalert.py", "rb")
    backup2 = open("functions.py", "rb")
    back_file1 = open("stockalert-backup.py", "wb")
    back_file2 = open("functions-backup.py", "wb")
    for data in backup1:
        back_file1.write(data)
    for data in backup2:
        back_file2.write(data)
    print("*Getting Update")
    stock_alert = requests.get("https://raw.github.com/joelspiers/stonks/master/stockalert.py")
    file1 = open("stockalert.py", "wb")
    for data in stock_alert:
        file1.write(data)
    functions = requests.get("https://raw.github.com/joelspiers/stonks/master/functions.py")
    file2 = open("functions.py", "wb")
    for data in functions:
        file2.write(data)
    file1.close()
    file2.close()
    backup1.close()
    backup2.close()
    back_file1.close()
    back_file2.close()
    print("*Success")
    print("*Restart Program")
    print("*Exiting in 5 Seconds..")
    time.sleep(5)
    exit()

#  end of file
