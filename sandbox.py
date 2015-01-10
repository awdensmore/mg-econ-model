
class bat:
    def __init__(self, myvar):
        self.myvar = myvar

    x = 5

    def go(self):
        z = 5 * self.myvar * x
        return z

    self.go()

g = bat(5)
a = g.go()

print(a)