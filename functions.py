import robin_stocks as r
import time
import os
import platform
import requests
import pygame as s

s.mixer.init()


class Var:
    stocks = []
    option = []
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
    log_in = False
    autoStart = 0
    crazyCrypto = 1
    buyPower = 0.0
    init_hold = {}
    init_crypto = []
    options_data = []
    updatedHolds = False
    system = ""
    favorite = "CZR"
    price = []
    stock_iterator = 0
    total_owned = 0
    buy_points = 0
    flag_points = 0
    owned_flags = 0
    fav_flags = 0
    num_stocks = 0
    len_price = 0
    tick = []
    tickers = {}
    clock = time.ctime().split()[3]
    flagType = {"flag": False, "type": 0}
    buyFlagType = {"flag": False, "type": 0}


v = Var()


def refresh():
    if v.system == "":
        v.system = platform.system()
    if v.system == "Windows":
        return os.system("CLS")
    elif v.system == "Linux":
        return os.system("clear")
    else:
        print("Error - System Unknown")


refresh()


def login():
    username = ""
    password = ""
    content = ""
    if v.log_in is False:
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
        v.buyPower = float(r.profiles.load_account_profile(info="portfolio_cash"))
        update_holdings()
        print("Success!")
        v.log_in = True


def update_holdings():
    v.init_hold = r.account.build_holdings(with_dividends=False)
    v.init_crypto = r.crypto.get_crypto_positions(info=None)
    v.buyPower = float(r.profiles.load_account_profile(info="portfolio_cash"))
    v.options_data = r.options.get_open_option_positions(info=None)


def clocks():
    v.clock = time.ctime().split()[3]
    seconds = int(v.clock.split(":")[0])*3600
    seconds = seconds + int(v.clock.split(":")[1])*60
    seconds = seconds + int(v.clock.split(":")[2])
    return seconds


class Options:
    def __init__(self, open_option):
        print(" * adding " + open_option["chain_symbol"] + " option")
        self.options_data = r.options.get_option_market_data_by_id(open_option["option_id"], info=None)
        self.mark_price = float(self.options_data["adjusted_mark_price"])
        self.break_even = float(self.options_data["break_even_price"])
        self.high_price = float(self.options_data["high_price"])
        self.low_price = float(self.options_data["low_price"])
        self.name = open_option["chain_symbol"]
        self.total_cost = float(open_option["average_price"])
        self.quantity = float(open_option["quantity"])
        self.build_data = open_option

    def update(self):
        self.mark_price = float(self.options_data["adjusted_mark_price"])
        self.break_even = float(self.options_data["break_even_price"])
        self.high_price = float(self.options_data["high_price"])
        self.low_price = float(self.options_data["low_price"])
        self.total_cost = float(self.build_data["average_price"])
        self.quantity = float(self.build_data["quantity"])


class Stock:
    def __init__(self, name):
        print(" * adding " + name)
        h_total, l_total = [], []
        self.earnPercent = None
        self.nextActual = None
        self.name = name
        if name == "BTC" or name == "LTC":
            if v.crazyCrypto == 1:
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
                        self.buy_price = self.low*v.baseLowCrypto
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
                self.quantity = float(v.init_hold[name]["quantity"])
                self.buy_price = float(v.init_hold[name]["average_buy_price"])
                self.sell_price = float(v.init_hold[name]["average_buy_price"])*v.baseHigh
                self.invested = True
                
            except KeyError:
                self.quantity = 0
                if v.buyMode == 0:
                    self.buy_price = self.low*v.baseLow
                if v.buyMode == 1:
                    self.buy_price = self.high*v.baseLow
                self.sell_price = self.buy_price*v.baseHigh
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
        self.sector = r.stocks.get_fundamentals(name, info="sector")[0]
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

    def update(self, data):
        self.set_last_price()
        self.set_gain()
        self.stop_watch()
        if v.len_price == v.num_stocks:
            self.set_price(float(data))
        if self.lastPrice != 0:
            self.set_change()
        self.set_equity()


def sell_high(a_stock):
    i = 0
    for data in v.stocks:
        if data.name == a_stock:
            break
        i = i + 1
    confirmation = "Nothing Happened"
    last_price = v.stocks[i].price
    start_time = clocks()
    check = False
    check_rate = v.slowCheck
    first, end_c = "\033[0m", "\033[0m"
    green, red, cyan = "\033[32m", "\033[31m", "\033[36m"
    eq1 = "\033[0m"
    while v.stocks[i].invested is True:
        if v.stocks[i].price > v.stocks[i].sell_price or check is False:
            refresh()
            print("{f}#####################{endL}".format(f=first, endL=end_c))
            print("{f}#         #{g}+{:7.2f}{f} #{endL}".format(v.stocks[i].high, endL=end_c, f=first, g=green))
            print("{f}#  {endL}{:^5}{f}  ###########{endL}".format(v.stocks[i].name, endL=end_c, f=first))
            print("{f}#         #{r}-{:7.2f}{f} #{endL}".format(v.stocks[i].low, endL=end_c, r=red, f=first))
            print("{f}#####################{endL}".format(f=first, endL=end_c))
            print("{f}# {c}{:7.2f}{endL} # {endL}{:7.2f}{f} #{endL}".format(v.stocks[i].price, v.stocks[i].sell_price, endL=end_c, c=cyan, f=first))
            print("{f}#####################{endL}".format(f=first, endL=end_c))
            print("{f}# {endL}{:7.2f}{endL} # {e1}{:7.2f}{f} #{endL}".format(v.stocks[i].buy_price, v.stocks[i].equityChange, endL=end_c,f=first, e1=eq1))
            print("{f}#####################{endL}".format(f=first, endL=end_c))
            print("")
            print("Last price: " + str(last_price))
            print("Time till next check: " + str(check_rate-((clocks()+1)-start_time) % check_rate))
            if ((clocks()+1)-start_time) % check_rate != 0:
                check = False
                print(str(((clocks()+1)-start_time) % check_rate))
            if ((clocks()+1)-start_time) % check_rate == 0 and check is False:
                check_rate = v.slowCheck
                if v.stocks[i].price > v.stocks[i].sell_price*v.percentage[0]:
                    check_rate = v.medCheck
                    print("medCheck wait time: " + str(v.medCheck) + " seconds")
                else:
                    print("slowCheck wait time: " + str(v.slowCheck) + " seconds")
                if v.stocks[i].price > v.stocks[i].sell_price*v.percentage[1]:
                    check_rate = v.fastCheck
                check = True
                if last_price > v.tocks[i].price:
                    if v.stocks[i].crypto is False:
                        confirmation = r.order_sell_market(v.stocks[i].name, v.stocks[i].quantity, timeInForce="gfd", extendedHours=True)
                    else:
                        if v.stocks[i].price-15 < v.stocks[i].sell_price:
                            return confirmation
                        confirmation = r.order_sell_crypto_limit(v.stocks[i].name, float("{:.8f}".format(v.stocks[i].quantity)), float("{:.2f}".format(v.stocks[i].price-15)), timeInForce="gtc")
                    v.stocks[i].set_invested(False)
                    minus_watchlist(a_stock)
                    add_watchlist(a_stock)
                    read_settings()
                    return confirmation
                last_price = v.stocks[i].price
                s.mixer.music.load("alarm.mp3")
                s.mixer.music.play()
            elif v.stocks[i].price < v.stocks[i].sell_price and check is True:
                return confirmation
        update_stocks()


# def manBuy(a_stock):
#     todo

def quick_sell_all():
    refresh()
    confirmation = "Nothing Happened"
    for data in v.stocks:
        if data.quantity > 0 and data.price > data.buy_price:
            confirmation = r.order_sell_market(data.name, data.quantity, timeInForce="gfd", extendedHours=True)
            data.quantity = 0
       # elif data.quantity < 0:
          #  for contract in v.options:
            #    if contract.name == data.name and contract.mark_price > contract.break_even:
                    ##r.order_sell_option_limit("close", "debit", contract.mark_price, contract.quantity, expiredate, contract.mark_price, optionType="call", timeInForce="gtc")

    reset()
    update_holdings()
    return confirmation


def man_sell_all():
    refresh()
    success = 0
    failed = 0
    confirmation = "Nothing Happened"
    for data in v.stocks:
        if v.flagType[data.sector] <= 0:
            continue
        if data.invested is True and data.price >= data.buy_price:  # re-add price >= buy price
            confirmation = r.order_sell_market(data.name, data.quantity, timeInForce="gfd", extendedHours=True)
            data.quantity = 0
            v.crazyCrypto = 1  # stop buying of stocks while market crash
        if confirmation != "Nothing Happened":
            success = success + 1
        else:
            failed = failed + 1
        if failed > 0:
            v.flagType["flag"] = True
        else:
            v.flagType["flag"] = False
    print(str(success)+" sold successfully!")
    print(str(failed)+" attempt failed")
    print("")
    time.sleep(5)
    reset()
    update_holdings()
    return confirmation


def man_buy_all():  # todo create a function that will buy on up trend day
    refresh()
    success = 0
    failed = 0
    confirmation = "Nothing Happened"
    diverse = v.totalEquity * v.risk
    for data in v.stocks:
        if v.buyFlagType[data.sector] <= 0:
            continue
        if data.invested is False and data.name == v.favorite:  # re-add price >= buy price
            qty = int(diverse / data.price)
            confirmation = r.order_buy_market(data.name, data.quantity, timeInForce="gfd", extendedHours=True)
        if confirmation != "Nothing Happened":
            success = success + 1
        else:
            failed = failed + 1
        if failed > 0:
            v.buyFlagType["flag"] = True
        else:
            v.buyFlagType["flag"] = False
    print(str(success)+" sold successfully!")
    print(str(failed)+" attempt failed")
    print("")
    time.sleep(15)
    reset()
    update_holdings()
    return confirmation


def buy_low(a_stock):
    i = 0
    if v.crazyCrypto == 1:
        r.cancel_all_crypto_orders()
    for data in v.stocks:
        if data.name == a_stock:
            break
        i = i + 1
    confirmation = "Nothing Happened"
    diverse = v.totalEquity*v.risk
    check = False
    check_rate = v.slowCheck
    start_time = clocks()
    last_price = v.stocks[i].price
    first, end_c, green, red, cyan, eq1 = "\033[0m", "\033[0m", "\033[32m", "\033[31m", "\033[36m", "\033[0m"
    while v.stocks[i].invested is False:
        refresh()
        if v.stocks[i].price <= v.stocks[i].buy_price:
            print("{f}#####################{endL}".format(f=first, endL=end_c))
            print("{f}#         #{g}+{:8.2f}{f}#{endL}".format(v.stocks[i].high, endL=end_c, f=first, g=green))
            print("{f}#  {endL}{:^5}{f}  ###########{endL}".format(v.stocks[i].name, endL=end_c, f=first))
            print("{f}#         #{r}-{:8.2f}{f}#{endL}".format(v.stocks[i].low, endL=end_c, r=red, f=first))
            print("{f}#####################{endL}".format(f=first, endL=end_c))
            print("{f}# {c}{:7.2f}{endL} # {endL}{:8.2f}{f}#{endL}".format(v.stocks[i].price, v.stocks[i].sell_price, endL=end_c, c=cyan, f=first))
            print("{f}#####################{endL}".format(f=first, endL=end_c))
            print("{f}# {endL}{:7.2f}{endL} # {e1}{:8.2f}{f}#{endL}".format(v.stocks[i].buy_price, v.stocks[i].equityChange, endL=end_c, f=first, e1=eq1))
            print("{f}#####################{endL}".format(f=first,endL=end_c))
            print("")
            first = "\033[0m"
            print("Time till next check: " + str(check_rate - (clocks()-start_time) % check_rate))
            print("Wait time: " + str(check_rate) + " seconds")
            if (clocks()-start_time) % check_rate != 0:
                check = False
            if (clocks()-start_time) % check_rate == 0 and check is False:
                check_rate = v.slowCheck
                if v.stocks[i].price < v.stocks[i].buy_price*v.lowPercentage[0]:
                    check_rate = v.medCheck
                if v.stocks[i].price < v.stocks[i].buy_price*v.lowPercentage[1]:
                    check_rate = v.fastCheck
                check = True
                if last_price < v.stocks[i].price:
                    if v.stocks[i].crypto is False:
                        qty = int(diverse/v.stocks[i].price)
                        confirmation = r.order_buy_market(v.stocks[i].name, qty, timeInForce="gtc", extendedHours=True)
                        read_settings()
                    else:
                        if v.stocks[i].price+15 > v.stocks[i].buy_price:
                            return confirmation
                        f_qty = float(diverse/(v.stocks[i].price*1.01))
                        confirmation = r.order_buy_crypto_limit(v.stocks[i].name, float("{:.8f}".format(f_qty)), float("{:.2f}".format(v.stocks[i].price+15)), timeInForce="gtc")
                        read_settings()
                    v.stocks[i].set_invested(True)
                    update_holdings()
                    return confirmation
                last_price = v.stocks[i].price
                s.mixer.music.load("alarm.mp3")
                s.mixer.music.play()
            elif v.stocks[i].price > v.stocks[i].buy_price and check is True:
                v.stocks[i].set_invested(False)
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
    i = 0
    for data in v.stocks:
        if data.name == ticker:
            break
        else:
            i = i+1
    news = r.stocks.get_news(ticker, info=None)
    if len(news) > v.stocks[i].news:
        s.mixer.music.load("mail.mp3")
        s.mixer.music.play()
        v.infoBar.insert(0, news[0]["title"])
        v.stocks[i].news = len(news)


def get_account_info():
    login()
    while True:
        print("Getting Options Info")
        account = r.profiles.load_account_profile(info=None)
        port = r.profiles.load_portfolio_profile(info=None)
        ##print(account)
        ##print(port)
        id = r.options.get_open_option_positions(info="option_id")[0]
        print(r.options.get_open_option_positions(info=None)[0])
        print()
        print(r.options.get_option_market_data_by_id(id,info=None))
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


def sort():
    if v.adjust == 1:  # Need a setting for this
        i = 0
        for data in v.stocks:
            if i == len(v.stocks)-2:
                break
            if data.crypto is True:
                i = i+1
                continue
            elif v.stocks[i+1].quantity > 0:
                v.stocks[i], v.stocks[i+1] = v.stocks[i+1], v.stocks[i]
                v.tick[i], v.tick[i + 1] = v.tick[i + 1], v.tick[i]
                i = i+1
            elif v.stocks[i].gain < v.stocks[i+1].gain:
                if v.stocks[i].quantity > 0:
                    i = i+1
                    continue
                v.stocks[i], v.stocks[i+1] = v.stocks[i+1], v.stocks[i]
                v.tick[i], v.tick[i + 1] = v.tick[i + 1], v.tick[i]
                i = i+1
            else:
                i = i+1


def initialize():
    for data in v.options_data:
        v.option.append(Options(data))
    v.stocks.clear()
    for data in v.tickers:
        if data == "BTC" or data == "LTC":
            v.stocks.insert(0, Stock(data))
        else:  # making list while separating crypto for price
            v.stocks.append(Stock(data))
            v.tick.append(data)


def check_invested():
    for data in v.stocks:
        if data.crypto is False:
            for invested in v.tickers:
                if invested != data.name:
                    data.quantity = 0
                    data.equity = 0


def sort_price():
    stock_type = []
    temp = None
    c = 0
    for data in v.stocks:
        if data.crypto is True:
            for x in v.init_crypto:
                if x["currency"]["code"] == data.name:
                    data.set_quantity(float(x["cost_bases"][0]["direct_quantity"]))
                if data.quantity > 0:
                    temp = float(r.crypto.get_crypto_quote(data.name, info="bid_price"))
                else:
                    temp = float(r.crypto.get_crypto_quote(data.name, info="ask_price"))
                    data.invested = False
            if temp is None:
                temp = data.price
            v.price.insert(c, temp)
            stock_type.insert(c, "Crypto Currency")
            c = c + 1
        else:
            break


def threat_buy(data):
    x = 0
    v.flagType[data.sector] = 0
    v.buyFlagType[data.sector] = 0
    if data.x_down >= 2:
        v.flagType[data.sector] = v.flagType[data.sector] + 1
        v.flag_points = v.flag_points + 1
        if data.invested is True:
            v.owned_flags = v.owned_flags + 1
    else:
        v.flagType[data.sector] = v.flagType[data.sector] - 1
        if data.invested is True:
            x = x + 1
            v.total_owned = x + v.owned_flags
    if data.x_up >= 1:
        v.buyFlagType[data.sector] = v.buyFlagType[data.sector] + 1
        v.buy_points = v.buy_points + 1
        if data.name == v.favorite:
            v.fav_flags = v.fav_flags + 1

    return data


def variable_reset():
    v.stock_iterator = 0
    v.total_owned = 0
    v.buy_points = 0
    v.flag_points = 0
    v.owned_flags = 0
    v.fav_flags = 0
    v.totalEquity = 0
    v.num_stocks = len(v.stocks)
    v.len_price = len(v.price)


def update_info_bar():
    if v.flag_points >= int(v.num_stocks/2):
        if v.owned_flags >= v.total_owned:
            v.flagType["flag"] = True
    if v.buy_points >= int(v.num_stocks/2):
        if v.fav_flags >= 1:
            v.buyFlagType["flag"] = True
    if v.flag_points >= v.buy_points:
        v.infoBar.insert(0, "Threat level: " + str(v.flag_points) + "/" + str(int(v.num_stocks/2)))
    else:
        v.infoBar.insert(0, "Buy level:    " + str(v.buy_points) + "/" + str(int(v.num_stocks/2)))


def update_stocks():
    for data in v.init_crypto:  # Grabs invested Crypto tickers
        if float(data["cost_bases"][0]["direct_quantity"]) > 0:
            v.tickers[data["currency"]["code"]] = ""
    for data in v.init_hold:  # Grabs invested Stocks
        v.tickers[data] = ""
    w_list = watch_list()
    for data in w_list:  # fills list with watchlist
        v.tickers[data] = ""
    if len(v.stocks) == len(v.tickers):  # if already initialized
        check_invested()
    else:  # remake stocks list
        initialize()
    v.price = r.stocks.get_latest_price(v.tick, includeExtendedHours=True)
    sort_price()
    variable_reset()
    for data in v.stocks:
        data.update(v.price[v.stock_iterator])
        data = threat_buy(data)
        if clocks() % 330 == 0:
            fake_news(data.name)
        v.totalEquity = v.totalEquity + data.equity
        v.stock_iterator = v.stock_iterator + 1
    for data in v.option:
        data.update()
        v.totalEquity = v.totalEquity + (data.mark_price*data.quantity*100)
    v.totalEquity = v.totalEquity + v.buyPower
    update_info_bar()
    sort()


def get_current_stocks():
    first, second, third, fourth, fifth, end_c, eq1, eq2, eq3, eq4, eq5 = "\033[0m", "\033[0m", "\033[0m", "\033[0m", "\033[0m", "\033[0m", "\033[0m", "\033[0m", "\033[0m", "\033[0m", "\033[0m"
    green, red, cyan = "\033[32m", "\033[31m", "\033[36m"
    seconds = [0, 0, 0, 0, 0, 0]
    refresh()
    print("Initializing..")
    login()
    update_stocks()
    v.clock = time.ctime().split()[3]
    i = 0
    refresh()
    green = "\033[32m"
    print("                                                   \033[93m$     {g}{:8.2f}      \033[93m$\033[0m                                        {:8}".format(v.totalEquity, v.clock, g=green))
    while True:
        v.clock = time.ctime().split()[3]
        if v.stocks[i].change > v.stocks[i].open*0.01:
            v.stocks[i].set_up()
            if v.stocks[i].crypto is False:
                v.stocks[i].stop_watch()
            if v.stocks[i].quantity > 0:
                s.mixer.music.load("boogoo.mp3")
                s.mixer.music.play()
        if v.stocks[i].seconds > 300 or v.stocks[i].x_down == 0:
            v.stocks[i].x_down = 0
            v.stocks[i].start_time = 0
        if v.stocks[i].change < -(v.stocks[i].open*0.01):
            v.stocks[i].set_down()
            v.stocks[i].start_time = clocks()
            if v.stocks[i].quantity > 0:
                s.mixer.music.load("fuckme.mp3")
                s.mixer.music.play()
                if v.stocks[i].max_up == 1 and v.stocks[i].x_down == 1:
                    quick_sell_all()
                    return get_current_stocks()
        if v.stocks[i].price > v.stocks[i].high:
            v.stocks[i].set_high(v.stocks[i].price)
        if int(v.clock.split(":")[1])%30 == 0 and v.stocks[i].done_once is False and v.stocks[i].crypto is True and v.stocks[i].invested is False:
            v.stocks[i].buy_price = v.stocks[i].hourly_low
            v.stocks[i].sell_price = v.stocks[i].buy_price*1.0005
            v.stocks[i].hourly_low = v.stocks[i].price
            v.stocks[i].done_once = True
        if int(v.clock.split(":")[1])%31 == 0:
            v.stocks[i].done_once = False
        if v.stocks[i].price < v.stocks[i].hourly_low and v.stocks[i].crypto is True and v.stocks[i].invested is False:
            v.stocks[i].hourly_low = v.stocks[i].price
        if int(v.clock.split(":")[0]) >= 7 or (int(v.clock.split(":")[0]) == 6 and int(v.clock.split(":")[1]) >= 30):
            if int(v.clock.split(":")[0]) == 6 and int(v.clock.split(":")[1]) <= 35:
                if v.buyFlagType["flag"] is True:
                    man_buy_all()
                    return get_current_stocks()
            else:
                v.stocks[i].x_up = 0
            if v.flagType["flag"] is True:
                man_sell_all()
                return get_current_stocks()
            if v.stocks[i].price > v.stocks[i].sell_price and v.stocks[i].quantity > 0 and v.stocks[i].change != 0:
                s.mixer.music.load("alarm.mp3")
                s.mixer.music.play()
                print(sell_high(v.stocks[i].name))  # Sell
                if v.stocks[i].invested is False and v.stocks[i].hourly_low != 0 and v.stocks[i].crypto is True:
                    if v.stocks[i].sell_price-20 > v.stocks[i].hourly_low:
                        v.stocks[i].hourly_low = v.stocks[i].hourly_low*.995
                    v.stocks[i].buy_price = v.stocks[i].hourly_low
                    v.stocks[i].sell_price = v.stocks[i].buy_price*v.baseHigh
            if i >= len(v.stocks) - 1 and v.buyPower > v.totalEquity*v.risk:
                potential_buys = {}
                for data in v.stocks:
                    if v.crazyCrypto == 1:
                        break  # temp turn off all sell activity
                    if v.crazyCrypto == 1 and data.crypto is False:
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
            i = i - 4
            if seconds[1]-seconds[0] > 5 or seconds[1] == 0:
                first = "\033[93m" if v.stocks[i].quantity > 0 else "\033[0m"
                seconds[1] = 0
            if seconds[2]-seconds[0] > 5 or seconds[2] == 0:
                second = "\033[93m" if v.stocks[i+1].quantity > 0 else "\033[0m"
                seconds[2] = 0
            if seconds[3]-seconds[0] > 5 or seconds[3] == 0:
                third = "\033[93m" if v.stocks[i+2].quantity > 0 else "\033[0m"
                seconds[3] = 0
            if seconds[4]-seconds[0] > 5 or seconds[4] == 0:
                fourth = "\033[93m" if v.stocks[i+3].quantity > 0 else "\033[0m"
                seconds[4] = 0
            if seconds[5]-seconds[0] > 5 or seconds[5] == 0:
                fifth = "\033[93m" if v.stocks[i+4].quantity > 0 else "\033[0m"
                seconds[5] = 0
            first = "\033[35m" if v.stocks[i].crypto is True else first
            second = "\033[35m" if v.stocks[i+1].crypto is True else second
            third = "\033[35m" if v.stocks[i+2].crypto is True else third
            fourth = "\033[35m" if v.stocks[i+3].crypto is True else fourth
            fifth = "\033[35m" if v.stocks[i+4].crypto is True else fifth
            eq1 = red if v.stocks[i].equityChange < 0 else "\033[0m"
            eq1 = green if v.stocks[i].equityChange > 0 else eq1
            eq2 = red if v.stocks[i+1].equityChange < 0 else "\033[0m"
            eq2 = green if v.stocks[i+1].equityChange > 0 else eq2
            eq3 = red if v.stocks[i+2].equityChange < 0 else "\033[0m"
            eq3 = green if v.stocks[i+2].equityChange > 0 else eq3
            eq4 = red if v.stocks[i+3].equityChange < 0 else "\033[0m"
            eq4 = green if v.stocks[i+3].equityChange > 0 else eq4
            eq5 = red if v.stocks[i+4].equityChange < 0 else "\033[0m"
            eq5 = green if v.stocks[i+4].equityChange > 0 else eq5
            seconds = [int(v.clock.split(":")[2]), 0, 0, 0, 0, 0]
            if v.stocks[i].up is True:
                seconds[1] = seconds[0]
                first = "\033[32m"
                v.stocks[i].reset()
            if v.stocks[i].down is True:
                seconds[1] = seconds[0]
                first = "\033[31m"
                v.stocks[i].reset()
            if v.stocks[i+1].up is True:
                seconds[1] = seconds[0]
                second = "\033[32m"
                v.stocks[i+1].reset()
            if v.stocks[i+1].down is True:
                seconds[1] = seconds[0]
                second = "\033[31m"
                v.stocks[i+1].reset()
            if v.stocks[i+2].up is True:
                seconds[1] = seconds[0]
                third = "\033[32m"
                v.stocks[i+2].reset()
            if v.stocks[i+2].down is True:
                seconds[1] = seconds[0]
                third = "\033[31m"
                v.stocks[i+2].reset()
            if v.stocks[i+3].up is True:
                seconds[1] = seconds[0]
                fourth = "\033[32m"
                v.stocks[i+3].reset()
            if v.stocks[i+3].down is True:
                seconds[1] = seconds[0]
                fourth = "\033[31m"
                v.stocks[i+3].reset()
            if v.stocks[i+4].up is True:
                seconds[1] = seconds[0]
                fifth = "\033[32m"
                v.stocks[i+4].reset()
            if v.stocks[i+4].down is True:
                seconds[1] = seconds[0]
                fifth = "\033[31m"
                v.stocks[i+4].reset()
            print("")
            print("   {f}#####################{endL}   {s}#####################{endL}   {t}#####################{endL}   {n}#####################{endL}   {n1}#####################{endL}".format(f=first, s=second, t=third, n=fourth, n1=fifth, endL=end_c))
            print("   {f}#         #{g}+{:8.2f}{f}#{endL}   {s}#         #{g}+{:8.2f}{s}#{endL}   {t}#         #{g}+{:8.2f}{t}#{endL}   {n}#         #{g}+{:8.2f}{n}#{endL}   {n1}#         #{g}+{:8.2f}{n1}#{endL}".format(v.stocks[i].high, v.stocks[i+1].high, v.stocks[i+2].high, v.stocks[i+3].high, v.stocks[i+4].high, endL=end_c, f=first, g=green, s=second, t=third, n=fourth, n1=fifth))
            print("   {f}#  {endL}{:^5}{f}  ###########{endL}   {s}#  {endL}{:^5}{s}  ###########{endL}   {t}#  {endL}{:^5}{t}  ###########{endL}   {n}#  {endL}{:^5}{n}  ###########{endL}   {n1}#  {endL}{:^5}{n1}  ###########{endL}".format(v.stocks[i].name, v.stocks[i+1].name, v.stocks[i+2].name, v.stocks[i+3].name, v.stocks[i+4].name, endL=end_c, f=first, s=second, t=third, n=fourth, n1=fifth))
            print("   {f}#         #{r}-{:8.2f}{f}#{endL}   {s}#         #{r}-{:8.2f}{s}#{endL}   {t}#         #{r}-{:8.2f}{t}#{endL}   {n}#         #{r}-{:8.2f}{n}#{endL}   {n1}#         #{r}-{:8.2f}{n1}#{endL}".format(v.stocks[i].low, v.stocks[i+1].low, v.stocks[i+2].low, v.stocks[i+3].low, v.stocks[i+4].low, endL=end_c, r=red, f=first, s=second, t=third, n=fourth, n1=fifth))
            print("   {f}#####################{endL}   {s}#####################{endL}   {t}#####################{endL}   {n}#####################{endL}   {n1}#####################{endL}".format(f=first, s=second, t=third, n=fourth, n1=fifth, endL=end_c))
            print("   {f}# {c}{:8.2f}{f}# {endL}{:8.2f}{f}#{endL}   {s}# {c}{:8.2f}{s}# {endL}{:8.2f}{s}#{endL}   {t}# {c}{:8.2f}{t}# {endL}{:8.2f}{t}#{endL}   {n}# {c}{:8.2f}{n}# {endL}{:8.2f}{n}#{endL}   {n1}# {c}{:8.2f}{n1}# {endL}{:8.2f}{n1}#{endL}".format(v.stocks[i].price, v.stocks[i].sell_price, v.stocks[i+1].price, v.stocks[i+1].sell_price, v.stocks[i+2].price, v.stocks[i+2].sell_price, v.stocks[i+3].price, v.stocks[i+3].sell_price, v.stocks[i+4].price, v.stocks[i+4].sell_price, endL=end_c, c=cyan, f=first, s=second, t=third, n=fourth, n1=fifth))
            print("   {f}#####################{endL}   {s}#####################{endL}   {t}#####################{endL}   {n}#####################{endL}   {n1}#####################{endL}".format(f=first, s=second, t=third, n=fourth, n1=fifth, endL=end_c))
            print("   {f}# {endL}{:8.2f}{f}# {e1}{:8.2f}{f}#{endL}   {s}# {endL}{:8.2f}{s}# {e2}{:8.2f}{s}#{endL}   {t}# {endL}{:8.2f}{t}# {e3}{:8.2f}{t}#{endL}   {n}# {endL}{:8.2f}{n}# {e4}{:8.2f}{n}#{endL}   {n1}# {endL}{:8.2f}{n1}# {e5}{:8.2f}{n1}#{endL}".format(v.stocks[i].buy_price, v.stocks[i].equityChange, v.stocks[i+1].buy_price, v.stocks[i+1].equityChange, v.stocks[i+2].buy_price, v.stocks[i+2].equityChange, v.stocks[i+3].buy_price, v.stocks[i+3].equityChange, v.stocks[i+4].buy_price, v.stocks[i+4].equityChange, endL=end_c, f=first, s=second, t=third, n=fourth, n1=fifth, e1=eq1, e2=eq2, e3=eq3, e4=eq4, e5=eq5))
            print("   {f}#####################{endL}   {s}#####################{endL}   {t}#####################{endL}   {n}#####################{endL}   {n1}#####################{endL}".format(f=first, s=second, t=third, n=fourth, n1=fifth, endL=end_c))
        i = last_eye
        first, second, third, fourth, fifth, end_c, eq1, eq2, eq3, eq4, eq5 = "\033[0m", "\033[0m", "\033[0m", "\033[0m", "\033[0m", "\033[0m", "\033[0m", "\033[0m", "\033[0m", "\033[0m", "\033[0m"
        if i >= len(v.stocks) - 1:
            i = -1
            debug()
            if int(v.clock.split(":")[1]) % 5 == 0 and len(v.infoBar) > 1:
                v.infoBar.pop(0)
            update_stocks()
            refresh()
            print("   {:46.35}  \033[93m$     {g}{:8.2f}      \033[93m$\033[0m                                        {:8}".format(v.infoBar[0], v.totalEquity, v.clock, g=green))
        i = i + 1


def customize_settings():
    print("Welcome to my automated stock trading program!")
    print("This program uses a three check system to let the program know how valuable a stock is")
    print("First check is your sell_price/buy_price and second and third check is a percentage of that")
    print("As the program proceeds through the checks it will refresh the information faster")
    print("Here you can adjust the different specifications on trading stocks")
    print("Here are the current settings:")
    print("baseLow=\033[93m" + str(v.baseLow) + "\033[0m  --this is multiplied by all the stocks week lows to determine their buy_price")
    print("baseHigh=\033[93m" + str(v.baseHigh) + "\033[0m  --this is multiplied by the original buy_price to determine the sell_price")
    print("Percentage1=\033[93m" + str(v.percentage[0]) + "\033[0m  --this is multiplied by your sell_price to activate the 'MediumCheck'")
    print("Percentage2=\033[93m" + str(v.percentage[1]) + "\033[0m  --this is multiplied by your sell_price to activate the 'FastCheck'")
    print("LowPercentage1=\033[93m" + str(v.lowPercentage[0]) + "\033[0m  --this is multiplied by your buy_price to activate the 'MediumCheck'")
    print("LowPercentage2=\033[93m" + str(v.lowPercentage[1]) + "\033[0m  --this is multiplied by your buy_price to activate the 'FastCheck'")
    print("SlowCheck=\033[93m" + str(v.slowCheck) + "\033[0m  --this is the waiting period of the first check in seconds")
    print("MediumCheck=\033[93m" + str(v.medCheck) + "\033[0m  --this is the waiting period of the second check in seconds")
    print("FastCheck=\033[93m" + str(v.fastCheck) + "\033[0m  --this is the waiting period of the third check in seconds")
    print("risk=\033[93m" + str(v.risk) + "\033[0m  --this is the percentage of your capital investment on a single stock")
    print("crazyCrypto=\033[93m" + str(v.crazyCrypto) + "\033[0m  --Experimental Mode: Crypto Currency Only {False : 0}{True : 1}")
    print("baseLowCrypto=\033[93m" + str(v.baseLowCrypto) + "\033[0m  --Determine Cypto buy_price: Multiply by the high")
    print("adjust=\033[93m" + str(v.adjust) + "\033[0m  --Adjusts display dynamically {Manual : 0} {Dynamic : 1} {RevDynamic : 2}")
    print("favorite=\033[93m" + str(v.favorite) + "\033[0m  --Set favorite stock for auto buy")
    print("autoStart=\033[93m" + str(v.autoStart) + "\033[0m  --Set program autostart {On : 1} {Off : 0}")
    option = input("Would you like to adjust these?(y/n)")
    if option.lower() == "n":
        return
    elif option.lower() == "baselow":
        v.baseLow = float(input("baseLow="))
    elif option.lower() == "basehigh":
        v.baseHigh = float(input("baseHigh="))
    elif option.lower() == "percentage1":
        v.percentage[0] = float(input("Percentage1="))
    elif option.lower() == "percentage2":
        v.percentage[1] = float(input("Percentage2="))
    elif option.lower() == "lowpercentage1":
        v.lowPercentage[0] = float(input("LowPercentage1="))
    elif option.lower() == "lowpercentage2":
        v.lowPercentage[1] = float(input("LowPercentage2="))
    elif option.lower() == "slowcheck":
        v.slowCheck = int(input("SlowCheck="))
    elif option.lower() == "mediumcheck":
        v.medCheck = int(input("MediumCheck="))
    elif option.lower() == "fastcheck":
        v.fastCheck = int(input("FastCheck="))
    elif option.lower() == "risk":
        v.risk = float(input("risk="))
    elif option.lower() == "crazycrypto":
        v.crazyCrypto = int(input("crazyCrypto="))
    elif option.lower() == "baselowcrypto":
        v.baseLowCrypto = float(input("baseLowCrypto="))
    elif option.lower() == "adjust":
        v.adjust = int(input("adjust="))
    elif option.lower() == "favorite":
        v.favorite = str(input("favorite="))
    elif option.lower() == "autostart":
        v.autoStart = int(input("autoStart="))
    else:
        print("")
        v.baseLow = float(input("baseLow="))
        v.baseHigh = float(input("baseHigh="))
        v.percentage[0] = float(input("Percentage1="))
        v.percentage[1] = float(input("Percentage2="))
        v.lowPercentage[0] = float(input("LowPercentage1="))
        v.lowPercentage[1] = float(input("LowPercentage2="))
        v.slowCheck = int(input("SlowCheck="))
        v.medCheck = int(input("MediumCheck="))
        v.fastCheck = int(input("FastCheck="))
        v.risk = float(input("risk="))
        v.crazyCrypto = int(input("crazyCryto="))
        v.baseLowCrypto = float(input("baseLowCryto="))
        v.adjust = int(input("adjust="))
        v.favorite = str(input("favorite="))
        v.autoStart = int(input("adjust="))
        print("")
    update_settings()


def read_settings():
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
    v.percentage[0] = setting[0]
    v.percentage[1] = setting[1]
    v.lowPercentage[0] = setting[2]
    v.lowPercentage[1] = setting[3]
    v.slowCheck = int(setting[4])
    v.medCheck = int(setting[5])
    v.fastCheck = int(setting[6])
    v.baseLow = setting[7]
    v.baseHigh = setting[8]
    v.risk = setting[9]
    v.crazyCrypto = int(setting[10])
    v.baseLowCrypto = float(setting[11])
    v.adjust = int(setting[12])
    v.autoStart = int(setting[13])


def check_info():
    try:
        file = open('info.txt', 'r')
    except:
        file = open('info.txt', 'w')
    try:
        content = file.readlines()
    except:
        return 0
    c_len = len(content)
    if c_len < 15:
        print("You need at least 15 stocks in your watchlist")
        print("Stocks in watchlist: " + str(c_len) + "/15")
    return c_len


def update_settings():
    file = open("settings.txt", "w")
    file.write("Percentage1="+ str(v.percentage[0]) + "\n")
    file.write("Percentage2="+ str(v.percentage[1])+ "\n")
    file.write("LowPercentage1="+ str(v.lowPercentage[0]) + "\n")
    file.write("LowPercentage2="+ str(v.lowPercentage[1])+ "\n")
    file.write("SlowCheck="+ str(v.slowCheck) + "\n")
    file.write("MediumCheck="+ str(v.medCheck) + "\n")
    file.write("FastCheck="+ str(v.fastCheck) + "\n")
    file.write("baseLow="+ str(v.baseLow) + "\n")
    file.write("baseHigh="+ str(v.baseHigh) + "\n")
    file.write("risk="+ str(v.risk) + "\n")
    file.write("crazyCrypto="+ str(v.crazyCrypto) + "\n")
    file.write("baseLowCrypto=" + str(v.baseLowCrypto) + "\n")
    file.write("adjust=" + str(v.adjust) + "\n")
    file.write("favorite=" + str(v.favorite) + "\n")
    file.write("autoStart=" + str(v.autoStart) + "\n")
    file.close()


def reset():
    v.stocks.clear()
    v.option.clear()
    v.tick.clear()


def debug():
    file = open("debug.txt", "w")
    for data in v.stocks:
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
    fun_size = 0
    current_fun_size = 0
    current_version = requests.get("https://raw.github.com/joelspiers/stonks/master/stockalert.py")
    functions = requests.get("https://raw.github.com/joelspiers/stonks/master/functions.py")
    stock_alert = open("stockalert.py", "rb")
    functions_file = open("functions.py", "rb")
    content1 = stock_alert.read()
    content2 = functions_file.read()
    current_size = len(current_version.content)
    current_fun_size = len(functions.content)
    total_current_size = current_fun_size + current_size
    for data in content1:
        current_stock = current_stock + 1
    for data in content2:
        fun_size = fun_size + 1
    stock_alert.close()
    functions_file.close()
    total_file_size = current_stock + fun_size
    if total_file_size == total_current_size:
        return False
    else:
        return True


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
