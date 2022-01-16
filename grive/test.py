number_list = range(-5, 5)
less_than_zero = list(filter(lambda x: not x > 0 and x < 3, number_list))
print(less_than_zero)

# from time import sleep
# from tqdm import tqdm
# for i in tqdm(range(10)):
#     sleep(3)
# def prRed(skk): print("\033[91m {}\033[00m" .format(skk))
# def prGreen(skk): print("\033[92m {}\033[00m" .format(skk))
# def prYellow(skk): print("\033[93m {}\033[00m" .format(skk))
# def prLightPurple(skk): print("\033[94m {}\033[00m" .format(skk))
# def prPurple(skk): print("\033[95m {}\033[00m" .format(skk))
# def prCyan(skk): print("\033[96m {}\033[00m" .format(skk))
# def prLightGray(skk): print("\033[97m {}\033[00m" .format(skk))
# def prBlack(skk): print("\033[98m {}\033[00m" .format(skk))
 
# prCyan("Hello World, ")
# prYellow("It's")
# prGreen("Geeks")
# prRed("For")
# prGreen("Geeks")