# @block=setup
data = [1, 2, 3]
print(f"data = {data}")

# @block=oops
print(data[10])

# @block=recover
print("this still runs")
