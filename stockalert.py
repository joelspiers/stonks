import functions as f
option = 1
try:
    f.read_settings()
except:
    print("\033[93mUsing Default Settings\033[0m*")
    f.update_settings()
while True:
    stockCount = f.check_info()
    print("1: Stock Auto Buy and Sell")
    print("2: Update Program")
    print("3: Load Account Info")
    print("4: Set custom triggers")
    print("5: Exit")
    try:
        if option != 1:
            option = int(input("Please enter a value: "))
    except ValueError:
        f.refresh()
        print("Invalid Input*")
        continue
    if option == 1 and stockCount >= 15:
        try:
            f.get_current_stocks()
        except KeyboardInterrupt:
            option = 0
            f.refresh()
            f.reset()
        except TypeError:
            f.refresh()
            f.reset()
            print("Restarting..")
            f.time.sleep(30)
            f.get_current_stocks()
    elif option == 2:
        f.auto_buy__sell__crypto()
    elif option == 3:
        f.get_account_info()
    elif option == 4:
        f.customize_triggers()
    elif option >=5:
        break
    else:
        print("Error Occurred")
        option = 0
        f.refresh()
#  End of file