from abc import abstractstaticmethod

class Renderer:
    def __init__(self):
        pass
    def name():
        return "Renderer"
    def help():
        return "Render stuff"
    @abstractstaticmethod
    def defaultOptions():
        return {}
    def optionDefaults():
        return {k:v[0] for k,v in Renderer.defaultOptions().items()}