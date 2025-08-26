from monero.const import NET_MAIN, NET_TEST, NET_STAGE
from monero.address import Address
from typing import List, Union
from enum import Enum


class Network(Enum):
    MAIN = NET_MAIN
    TEST = NET_TEST
    STAGE = NET_STAGE

    @classmethod
    def list(cls) -> List['Network']:
        return [cls.MAIN, cls.TEST, cls.STAGE]

    @classmethod
    def get_list(cls, selected: List[Union['Network', str]] = [], default: List['Network'] = [NET_MAIN]) -> List['Network']:
        if len(selected) == 0:
            return cls.get_list(default)
        return [cls.ensure(net) for net in selected]

    @classmethod
    def fromString(cls, net: str) -> 'Network':
        if net in (NET_MAIN, 'M'):
            return cls.MAIN
        if net in (NET_TEST, 'T'):
            return cls.TEST
        if net in (NET_STAGE, 'S'):
            return cls.STAGE
        raise ValueError("Invalid network type")

    @classmethod
    def fromAddress(cls, address: Union[str, Address]) -> 'Network':
        net = (Address(address) if not isinstance(address, Address) else address).net
        if net == NET_MAIN:
            return cls.MAIN
        if net == NET_TEST:
            return cls.TEST
        if net == NET_STAGE:
            return cls.STAGE
        raise ValueError("Invalid network type")

    @classmethod
    def ensure(cls, net: Union[str, 'Network']) -> 'Network':
        if type(net) == str:
            return cls.fromString(net)
        return net

    @classmethod
    def valid(cls, net: Union[str, 'Network']) -> bool:
        try:
            if type(net) == str and cls.fromString(net):
                return True
        except ValueError:
            return False
        if net in cls.list():
            return True
        return False

    def __str__(self) -> str:
        return self.value
