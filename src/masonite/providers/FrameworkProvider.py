from ..request import Request
from ..response import Response
from ..providers import Provider

from ..presets.PresetsCapsule import PresetsCapsule
from ..presets import Tailwind, Vue, React, Bootstrap


class FrameworkProvider(Provider):
    def __init__(self, application):
        self.application = application

    def register(self):
        pass

    def boot(self):
        request = Request(self.application.make("environ"))
        request.app = self.application
        self.application.bind("request", request)
        self.application.bind("response", Response(self.application))

        # @M5 remove this and add PresetsProvider in default project
        presets = PresetsCapsule()
        presets.add(Bootstrap())
        presets.add(Tailwind())
        presets.add(Vue())
        presets.add(React())
        self.application.bind("presets", presets)
