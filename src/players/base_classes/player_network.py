import json
import requests
import websockets

from abc import ABC, abstractmethod
from asyncio import Lock
from environment.battle import Battle


class PlayerNetwork(ABC):
    """
    Network interface of a player.
    
    In charge of communicating with the pokemon showdown server.
    """

    def __init__(
        self,
        username: str,
        password: str,
        *,
        authentification_address: str,
        avatar: int,
        log_messages_in_console: bool,
        server_address: str,
    ) -> None:
        """
        Initialises interface.
        """

        if authentification_address is None:
            raise AttributeError(
                "Unspecified authentification address. Please specify an authentification address."
            )

        self._authentification_address = authentification_address
        self._avatar = avatar
        self._log_messages_in_console = log_messages_in_console
        self._logged_in = False
        self._password = password
        self._server_address = server_address
        self._username = username
        self._waiting_start = False

        self._lock = Lock()

    async def _log_in(self, conf_1: str, conf_2: str) -> None:
        """
        Log in player to specified username.
        conf_1 and conf_2 are confirmation strings received upon server access.
        They are needed to log in.
        """
        log_in_request = requests.post(
            self._authentification_address,
            data={
                "act": "login",
                "name": self._username,
                "pass": self._password,
                "challstr": conf_1 + "%7C" + conf_2,
            },
        )
        await self.send_message(
            f"/trn {self._username},0,{json.loads(log_in_request.text[1:])['assertion']}"
        )

        # If there is an avatar to select, let's select it !
        if self._avatar:
            self.change_avatar(self._avatar)

    async def accept_challenge(self, user: str) -> None:
        if self.can_accept_challenge:
            self._waiting_start = True
            await self.send_message(f"/accept {user}")

    async def leave_battle(self, battle: Battle):
        await self.send_message("/leave", room=battle.battle_tag)

    async def challenge(self, player=None, format=None):
        if not self.logged_in:
            return

        if player and format:
            await self.send_message(f"/challenge {player}, {format}")
        else:
            print(
                f"No player or format specified in call to 'challenge' from {self}\nplayer: {player}\nformat: {format}"
            )
            raise ValueError(
                f"No player or format specified in call to 'challenge' from {self}\nplayer: {player}\nformat: {format}"
            )

    async def change_avatar(self, avatar_id: str) -> None:
        await self.send_message(f"/avatar {avatar_id}")

    async def listen(self) -> None:
        async with websockets.connect(self.websocket_address) as websocket:
            self._websocket = websocket
            while not self.should_die:
                message = await websocket.recv()
                if self._log_messages_in_console:
                    print(f"\n{self.username} << {message}")
                await self.manage_message(message)

    async def manage_message(self, message: str) -> None:
        """
        Parse and manage responses to incoming messages.
        """
        split_message = message.split("|")
        # challstr confirms that we are connected to the server
        # we can therefore login
        if split_message[1] == "challstr":
            conf_1, conf_2 = split_message[2], split_message[3]
            await self._log_in(conf_1, conf_2)

        # TODO challenge sent
        # updatechallenges means that we received a challenge
        elif split_message[1] == 'updateuser' and split_message[2] == self.username:
            self._logged_in = True
        elif "updatechallenges" in split_message[1]:
            response = json.loads(split_message[2])
            for user, format in (
                json.loads(split_message[2]).get("challengesFrom", {}).items()
            ):
                if format == self.format:
                    await self.accept_challenge(user)

        elif split_message[0].startswith('>battle'):
            await self.battle(message)
        elif split_message[1] in ["updatesearch", "popup", "updateuser"]:
            pass
        else:
            print(f"UNMANAGED MESSAGE : {message}")

    async def send_message(
        self, message: str, room: str = "", message_2: str = None
    ) -> None:
        if message_2:
            to_send = "|".join([room, message, message_2])
        else:
            to_send = "|".join([room, message])
        if self._log_messages_in_console:
            print(f"\n{self.username} >> {to_send}")
        async with self._lock:
            await self._websocket.send(to_send)

    @property
    @abstractmethod
    def can_accept_challenge(self) -> bool:
        pass

    @property
    def logged_in(self) -> bool:
        return self._logged_in

    @property
    @abstractmethod
    def should_die(self) -> bool:
        pass

    @property
    def username(self) -> str:
        return self._username

    @property
    def websocket_address(self) -> str:
        return f"ws://{self._server_address}/showdown/websocket"
