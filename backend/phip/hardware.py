"""
Protheon Hardware Abstraction
"""
from abc import ABC, abstractmethod

class HardwareInterface(ABC):
    @abstractmethod
    def connect(self, port=None) -> bool:
        pass

    @abstractmethod
    def disconnect(self):
        pass

    @property
    @abstractmethod
    def is_connected(self) -> bool:
        pass

    @property
    @abstractmethod
    def state(self) -> str:
        pass

    @abstractmethod
    def add_callback(self, callback):
        pass

    @abstractmethod
    def add_state_callback(self, callback):
        pass

    @abstractmethod
    def send_command(self, cmd_type: str, arg1: int = 0, arg2: int = 0) -> bool:
        pass

    @abstractmethod
    def send_stop(self) -> bool:
        pass

    @abstractmethod
    def send_ping(self) -> bool:
        pass

    @abstractmethod
    def get_stats(self) -> dict:
        pass

    @staticmethod
    @abstractmethod
    def list_ports() -> list:
        pass
