from xmrsigner.helpers.network import Network
from monero.wallet import Wallet
from monero.backends.offline import OfflineWallet
from monero.address import Address
from monero.address import address as parse_address
from requests.exceptions import ConnectionError
from monero.backends.jsonrpc.exceptions import RPCError
from typing import Optional, Union, Dict, List
from binascii import hexlify
from decimal import Decimal
from math import ceil


NORMAL_FEE_PER_KB = 1500000000  # XMR per KB considered conservative(higher) normal fee
HIGH_FEE_THRESHOLD = 10  # Multiple of normal fee to be considered high


class XmrAmount(int):
    
    def decimal(self) -> Decimal:
        return Decimal(self) / 10**12


class Recipient:
    address: Address
    amount: XmrAmount

    def __init__(self, address: str, amount: int):
        self.address = parse_address(address)
        self.amount = XmrAmount(amount)

class EncryptedKeyImages(str):

    def __bytes__(self) -> bytes:
        return unhexlify(self)


class SignedTxResponse(str):
    tx_hash_list: List[str] = []
    tx_raw_list: List[str] = []
    tx_key_list: List[str] =[]

    def __bytes__(self) -> bytes:
        return unhexlify(self)


class NoValidTxException(Exception):
    response: Optional[Dict]

    def __int__(self, text: str, response: Optional[Dict]):
        super().__init__(text)
        response = response


class TxSummary:
    amount_in: XmrAmount
    amount_out: XmrAmount
    recipients: List[Recipient]
    change_address: Optional[Address] = None
    change_amount: XmrAmount
    fee: XmrAmount
    recipients: List[Recipient] = []

    def __init__(self, summary: Dict):
        self.amount_in = XmrAmount(summary['amount_in'])
        self.amount_out = XmrAmount(summary['amount_out'])
        for r in summary['recipients']:
            self.recipients.append(Recipient(r['address'], r['amount']))
        self.change_address = parse_address(summary['change_address']) if summary['change_address'] != '' else None
        self.change_amount = XmrAmount(summary['change_amount'])
        self.fee = XmrAmount(summary['fee'])


class TxDescriptionDetails:
    amount_in: XmrAmount
    amount_out: XmrAmount
    recipients: List[Recipient] = []
    change_address: Optional[Address] = None
    change_amount: XmrAmount
    fee: XmrAmount
    payment_id: Optional[str] = None
    ring_size: int
    unlock_time: int = -1
    dummy_outputs: int
    extra: Optional[str] = None

    def __init__(self, desc: Dict):
        self.amount_in = XmrAmount(desc['amount_in'])
        self.amount_out = XmrAmount(desc['amount_out'])
        for r in desc['recipients']:
            self.recipients.append(Recipient(r['address'], r['amount']))
        self.change_address = parse_address(desc['change_address']) if desc['change_address'] != '' else None
        self.change_amount = XmrAmount(desc['change_amount'])
        self.fee = XmrAmount(desc['fee'])
        if 'payment_id' in desc and desc['payment_id'] != '':
            self.payment_id = desc['payment_id']
        self.ring_size = desc['ring_size']
        self.unlock_time = desc['unlock_time']
        self.dummy_outputs = desc['dummy_outputs']
        if 'extra' in desc and desc['extra'] != '':
            self.extra = desc['extra']


class TxDescription:
    details: List[TxDescriptionDetails] = []
    summary: Optional[TxSummary] = None
    estimated_tx_size_kb: Optional[int] = None
    _recipients: Optional[List[Recipient]] = None
    _recipients_addresses: Optional[List[Recipient]] = None
    _change_addresses: Optional[List[Address]] = None
    _network: Optional[Network] = None

    def __init__(self, response: Dict, estimated_tx_size_kb: Optional[int] = None):
        self.estimated_tx_size_kb = estimated_tx_size_kb
        if 'desc' not in response:
            raise NoValidTxException('No description for transaction, probably not a valid transaction at all!', response)
        for desc in response['desc']:
            self.details.append(TxDescriptionDetails(desc))
        if 'summary' in response:
            self.summary = TxSummary(response['summary'])
        if 'summary' in response:
            self.summary = TxSummary(response['summary'])

    @property
    def amounts_in(self) -> [XmrAmount]:
        return [d.amount_in for d in self.details]

    @property
    def amount_in(self) -> XmrAmount:
        out: int = 0
        for amount in self.amounts_in:
            out += int(amount)
        return XmrAmount(out)

    @property
    def amounts_out(self) -> List[XmrAmount]:
        return [d.amount_out for d in self.details]

    @property
    def amount_out(self) -> XmrAmount:
        out: int = 0
        for amount in self.amounts_out:
            out += int(amount)
        return XmrAmount(out)

    @property
    def network(self) -> Network:
        if self._network is None:
            self._network = Network.ensure(self.details[0].recipients[0].address.net)
        return self._network

    @property
    def recipients(self) -> List[Recipient]:
        if self._recipients is None:
            out: Dict[Address, int] = {}
            for d in self.details:
                for r in d.recipients:
                    if r.address not in out:
                        out[r.address] = Recipient(r.address, int(r.amount))
                    else:
                        out[r.address].amount = XmrAmount(int(out[r.address].amount) + int(r.amount))
            self._recipients = list(out.values())
        return self._recipients

    @property
    def recipients_addresses(self) -> List[Address]:
        if self._recipients_addresses is None:
            self._recipients_addresses = [r.address for r in self.recipients]
        return self._recipients_addresses

    @property
    def change_addresses(self) -> List[Address]:
        if self._change_addresses is not None:
            return self._change_addresses
        out: List[Address] = []
        for d in self.details:
            for r in d.recipients:
                if r.address not in out:
                    out.append(r.address)
        self._change_addresses = out
        return self._change_addresses

    @property
    def change_amounts(self) -> List[XmrAmount]:
        return [d.change_amount for d in self.details]

    @property
    def change_amount(self) -> XmrAmount:
        out: int = 0
        for amount in self.change_amounts:
            out += int(amount)
        return XmrAmount(out)

    @property
    def fees(self) -> List[XmrAmount]:
        return [d.fee for d in self.details]

    @property
    def fee(self) -> XmrAmount:
        out: int = 0
        for amount in self.fees:
            out += int(amount)
        return XmrAmount(out)

    @property
    def inputs(self) -> int:
        return len(self.details)

    @property
    def outputs(self) -> int:
        return len(self.recipients)

    @property
    def change_outputs(self) -> int:
        return len(self.change_addresses)

    @property
    def unlock_time_warning(self) -> bool:
        return self.unlock_time != 0

    @property
    def unusual_high_fee_warning(self) -> bool:
        return self.fees > NORMAL_FEE_PER_KB * HIGH_FEE_THRESHOLD * self.estimated_tx_size_kb

    @property
    def no_change_warning(self) -> bool:  # should there really be warned of? I mean a good address spend selection should minimize or avoid change, not? Will not include this warning in warnings. Also easy to mitigate as an attacker, why don't let a picoXMR in the account???
        return self.change_amount == 0

    @property
    def warning(self) -> bool:
        return self.unlock_time_warning or self.unusual_high_fee_warning  # self.no_change_warning not included


class WalletRpcWrapper:  # TODO: 2024-07-26, this should be in monero-python

    wallet: Optional[Wallet] = None

    def __init__(self, wallet: Wallet):
        self.wallet = wallet

    def export_encrypted_key_images(self, export_raw: Optional[bool] = None, get_tx_keys: Optional[bool] = None) -> Optional[EncryptedKeyImages]:
        try:
            params = {}
            if export_raw:
                params['export_raw'] = export_raw
            if get_tx_keys:
                params['get_tx_keys'] = get_tx_keys
            result = self.wallet._backend.raw_request('export_key_images', params)
            print(f"export_key_images result: {result}")
            # Check if the result contains key images
            if 'key_images' in result:
                if result['key_images']:
                    # Convert the list of key images to a single string
                    key_images_blob = ''.join([ki.get('key_image', '') for ki in result['key_images'] if ki.get('key_image')])
                    if key_images_blob:
                        print(f"Exported {len(result['key_images'])} key images")
                        return EncryptedKeyImages(key_images_blob)
                else:
                    print("No key images to export (empty list)")
                    return None
            else:
                print("No key images field in response")
                return None
        except ConnectionError as ce:
            print(f'WalletRpcWrapper.export_encrypted_key_images(): {ce}')
            raise ce
        except RPCError as re:
            print(f'WalletRpcWrapper.export_encrypted_key_images(): {re}')
            raise re
        except Exception as e:
            print(f'WalletRpcWrapper.export_encrypted_key_images(): Unexpected error: {e}')
            raise e
        except ConnectionError as ce:
            print(f'WalletRpcWrapper.export_encrypted_key_images(): {ce}')
            raise ce
        except RPCError as re:
            print(f'WalletRpcWrapper.export_encrypted_key_images(): {re}')
            raise re
        return None

    def import_outputs(self, outputs: Union[str, bytes]) -> Optional[int]:
        try:
            result = self.wallet._backend.raw_request('import_outputs', {'outputs_data_hex': hexlify(outputs).decode() if type(outputs) == bytes else outputs})
            print(result)
            if 'num_imported' in result:
                return result['num_imported']
        except ConnectionError as ce:
            print(f'WalletRpcWrapper.import_outputs(): {ce}')
            raise ce
        except RPCError as re:
            print(f'WalletRpcWrapper.import_outputs(): {re}')
        return None

    def sign_transfer(self, unsigned_txset: Union[str, bytes]) -> Optional[SignedTxResponse]:
        try:
            result = self.wallet._backend.raw_request('sign_transfer', {'unsigned_txset': hexlify(unsigned_txset).decode() if type(unsigned_txset) == bytes else unsigned_txset})
            print(result)
            if 'signed_txset' in result:
                out = result['signed_txset']
                if 'tx_raw_list' in result:
                    out.tx_raw_list = tx_raw_list
                if 'tx_key_list' in result:
                    out.tx_key_list = tx_key_list
                return out
        except ConnectionError as ce:
            print(f'WalletRpcWrapper.sign_transfer(): {ce}')
            raise ce
        except RPCError as re:
            print(f'WalletRpcWrapper.sign_transfer(): {re}')
        return None

    def describe_transfer(self, unsigned_txset: Union[str, bytes]) -> Optional[TxDescription]:
        try:
            result = self.wallet._backend.raw_request('describe_transfer', {'unsigned_txset': hexlify(unsigned_txset).decode() if type(unsigned_txset) == bytes else unsigned_txset})
            print(result)
            if 'desc' in result:
                return TxDescription(result, self.calculate_tx_size_kb(unsigned_txset))
        except NoValidTxException as ntxe:
            print(f'WalletRpcWrapper.sign_transfer(): {ntxe}\n\tresponse: {ntxe.response}')
        except ConnectionError as ce:
            print(f'WalletRpcWrapper.sign_transfer(): {ce}')
            raise ce
        except RPCError as re:
            print(f'WalletRpcWrapper.sign_transfer(): {re}')
        return None

    @staticmethod
    def calculate_tx_size_kb(unsigned_txset: Union[str, bytes]) -> int:
        return ceil(len(binascii.unhexlify(unsigned_txset) if type(unsigned_txset) != bytes else unsigned_txset) / 1024)
