class Move:

    def __init__(self, xfrom, yfrom, xto, yto):
        self.xfrom = xfrom
        self.yfrom = yfrom
        self.xto   = xto
        self.yto   = yto

    # Returns true if this move goes to the same squares as the other move.
    def equals(self, other_move):
        return (self.xfrom == other_move.xfrom and
                self.yfrom == other_move.yfrom and
                self.xto   == other_move.xto   and
                self.yto   == other_move.yto)

    def to_string(self):
        cols = 'ABCDEFGH'
        return f"({cols[self.xfrom]}{8 - self.yfrom}) -> ({cols[self.xto]}{8 - self.yto})"
