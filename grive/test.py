# number_list = range(-5, 5)
# less_than_zero = list(filter(lambda x: x > 10, number_list))[0]
# print(less_than_zero)

from time import sleep
from tqdm import tqdm
for i in tqdm(range(10)):
    sleep(3)