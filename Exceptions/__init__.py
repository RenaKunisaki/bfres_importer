class UnsupportedFileTypeError(Exception):
    def __init__(self, magic):
        super().__init__()
        self.magic = magic


    def __str__(self):
        return "UnsupportedFileTypeError(%s)" % str(self.magic)
