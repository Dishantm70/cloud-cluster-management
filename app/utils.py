import random

def get_random_ip():
	return str(random.randint(1,255)) + "." + str(random.randint(1,255)) + "." + str(random.randint(1,255))