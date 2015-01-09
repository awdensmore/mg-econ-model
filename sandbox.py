
class bat:
    def __hello(self, x):
        y = 5 * x
        return y

    def go(self, k):
        z = self.__hello(k)
        return z

e = bat()

n = e.go(3)

print(n)

g = e.__hello(6)

print(g)