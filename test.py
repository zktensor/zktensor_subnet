import random
class Axon:
    def __init__(self):
        self.ip = self.generate_random_ip()
        self.coldkey = self.generate_random_coldkey()

    @staticmethod
    def generate_random_ip():
        return ".".join(str(random.randint(0, 255)) for _ in range(4))

    @staticmethod
    def generate_random_coldkey():
        return "".join(random.choice("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789") for _ in range(16))

filtered_axons = [Axon() for _ in range(5)]
ip_array = [axon.ip for axon in filtered_axons]
coldkey_array = [axon.coldkey for axon in filtered_axons]
coldkey_array[4] = coldkey_array[0]
coldkey_array[3] = coldkey_array[0]
coldkey_array[2] = coldkey_array[0]
print("ip_array", ip_array)
print("coldkey_array", coldkey_array)

weight_factors = [1 / ip_array.count(ip) for ip in ip_array]
coldkey_distribution = [1 / (coldkey_array.count(coldkey) - 2 if coldkey_array.count(coldkey) > 2 else 1)  for coldkey in coldkey_array]
total_factors = [ip_factor * coldkey_factor for ip_factor, coldkey_factor in zip(weight_factors, coldkey_distribution)]

print("weight_factors", weight_factors)
print("coldkey_distrbiution", coldkey_distribution)
print("sum_weight", total_factors)
# weight_factors = weight_factors * coldkey_distribution

# Calculate weight_factors
weight_factors = [1 / (ip_array.count(ip) - 2 if ip_array.count(ip) > 2 else 1) for ip in ip_array]

# Calculate coldkey_distribution