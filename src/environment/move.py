import json

global MOVES

with open("data/moves.json") as f:
    MOVES = json.load(f)


# These are magic regexes to convert from the .js moves file to working json, when
# combined with some auto-formatting
# ^    "((on.*)|(.*Callback))": function\(.*?\) {\n(.*\n)*?    },\n
# ^      "((on.*)|(.*Callback))": function\(.*?\) {\n(.*\n)*?      },?\n
# ^        "((on.*)|(.*Callback))": function\(.*?\) {\n(.*\n)*?        },?\n
# //.*

class Move:

    SECONDARIES = [
        "par",
        "brn",
        "frz",
        "psn",
        "slp",
        "flinch",
        "confusion",
    ]

    def __init__(self, move) -> None:
        move = ''.join([char for char in move if char not in "-' "])
        if move.startswith('hiddenpower') and move[-1] in '0123456789':
            move = move[:-2] 

        if move not in MOVES and move.startswith('z'):
            raise ZMoveException

        self.name = move
        self.accuracy = (
            MOVES[move]["accuracy"]
            if not isinstance(MOVES[move]["accuracy"], bool)
            else 100
        )
        self.base_power = MOVES[move]["basePower"]
        self.category = MOVES[move]["category"]
        self.max_pp = MOVES[move]["pp"]
        # TODO : add pp management ?
        self.priority = MOVES[move]["priority"]
        # TODO
        self.flags = MOVES[move]["flags"]
        self.boosts = {
            "tox": (0,0),
            "psn": (0,0),
            "slp": (0,0),
            "par": (0,0),
            "brn": (0,0),
            "frz": (0,0),
        }
        self.auto_boosts = {
            "tox": (0,0),
            "psn": (0,0),
            "slp": (0,0),
            "par": (0,0),
            "brn": (0,0),
            "frz": (0,0),            
        }

        self.secondaries = {}
        if 'secondary' in MOVES[move]:
            if MOVES[move]['secondary']:
                self.add_secondary(MOVES[move]['secondary'])
        elif 'secondaries' in MOVES[move]:
            for secondary in MOVES[move]['secondaries']:
                self.add_secondary(secondary)
        
        # TODO
        self.target = MOVES[move]["target"]
        # TODO
        self.type = MOVES[move]["type"].lower()
        # TODO : z moves things

    def __repr__(self) -> str:
        return f"Move object: {self.name}"

    def add_secondary(self, effect):
        self.name
        if 'boosts' in effect:
            for stat, val in effect['boosts'].items():
                self.boosts[stat] = (val, effect['chance'])
        elif 'status' in effect:
            if effect['status'] not in self.SECONDARIES:
                print("UNKNOWN SECONDARY", effect['status'])
            else:
                self.secondaries[effect['status']] = effect['chance']
        elif 'volatileStatus' in effect:
            if effect['volatileStatus'] not in self.SECONDARIES:
                print("UNKNOWN SECONDARY", effect['volatileStatus'])
            else:
                self.secondaries[effect['volatileStatus']] = effect['chance']
        elif 'self' in effect:
            if 'boosts' in effect['self']:
                for stat, val in effect['self']['boosts'].items():
                    self.auto_boosts[stat] = (val, effect['chance'])
            else:
                print('effect self', effect)
        else:
            effect.pop('chance')
            if effect:
                print("effect", effect)

class ZMoveException(Exception):
    pass