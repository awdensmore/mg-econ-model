
class x:
    def yo(self, y):
        x = y * 5
        return x

class r(x):
    def __init__(self, f):
        self.f = f

    def t(self, c):
        z = self.yo(c)
        return z

a = x()
b = r(a)
print(b.t(5))
