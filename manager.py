import os
from os import path

import utils
from tqdm import tqdm


class Manager:
    all: list[str] = []
    pending: list[str] = []
    processing: list[str] = []
    bar: tqdm = None

    def __init__(self):
        self.all = []
        self.pending = []
        self.processing = []

        for set in os.listdir(utils.keyframes):
            if not path.isdir(path.join(utils.keyframes, set)):
                continue

            for video in os.listdir(path.join(utils.keyframes, set)):
                if not path.isdir(path.join(utils.keyframes, set, video)):
                    continue

                for frame in os.listdir(path.join(utils.keyframes, set, video)):
                    if not path.isfile(path.join(utils.keyframes, set, video, frame)):
                        continue

                    self.all.append(path.join(set, video, frame))

        self.pending = [item for item in self.all if not path.exists(path.join(utils.objects, item))]
        self.pending = sorted(self.pending)
        # self.bar = tqdm(total=len(self.pending), unit="frames", ascii=True, desc="Processing...")

    def process(self):
        item = self.pending.pop(0)
        self.processing.append(item)
        return item

    def interrupt(self, item: str):
        self.pending.insert(0, item)
        self.processing.remove(item)
        # self.bar.n -= 1 if self.bar.last_print_n > 0 else 0
        # self.bar.last_print_n -= 1 if self.bar.last_print_n > 0 else 0
        # self.bar.refresh()
        return

    def finish(self, item: str, result: dict[str, str] | list[dict[str, str]]):
        self.processing.remove(item)
        file = path.join(utils.objects, item.replace(".jpg", ".json"))
        dir = path.dirname(file)
        if not path.exists(dir):
            os.makedirs(dir)
        utils.write_json(file, result)

        # self.bar.update(1)

