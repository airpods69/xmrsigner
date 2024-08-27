from re import search, IGNORECASE
from numpy import array as NumpyArray
from logging import getLogger
from binascii import hexlify
from typing import List, Dict, Optional, Union

from binascii import a2b_base64, b2a_base64
from monero.address import address as monero_address
from monero.address import Address
from pyzbar import pyzbar
from pyzbar.pyzbar import ZBarSymbol
from xmrsigner.urtypes.xmr import XmrOutput, XmrTxUnsigned

from xmrsigner.helpers.ur2.ur_decoder import URDecoder

from xmrsigner.models.base_decoder import DecodeQRStatus
from xmrsigner.models.seed_decoder import SeedQrDecoder
from xmrsigner.models.monero_decoder import MoneroWalletQrDecoder, MoneroAddressQrDecoder
from xmrsigner.models.qr_type import QRType
from xmrsigner.models.seed import Seed
from xmrsigner.models.settings import SettingsConstants


logger = getLogger(__name__)


class DecodeQR:
    """
    Used to process images or string data from animated qr codes.
    """

    def __init__(self, wordlist_language_code: str = SettingsConstants.WORDLIST_LANGUAGE__ENGLISH):
        self.wordlist_language_code = wordlist_language_code
        self.complete = False
        self.qr_type = None
        self.decoder = None

    def add_image(self, image):
        data = DecodeQR.extract_qr_data(image, is_binary=True)
        if data == None:
            return DecodeQRStatus.FALSE
        return self.add_data(data)

    def add_data(self, data) -> DecodeQRStatus:
        if data == None:
            return DecodeQRStatus.FALSE

        qr_type = DecodeQR.detect_segment_type(data, wordlist_language_code=self.wordlist_language_code)
        print(f'qr type: {qr_type}')

        if self.qr_type == None:
            self.qr_type = qr_type
            print(f'self.qr_type: {self.qr_type}')

            if self.qr_type in [
                QRType.XMR_OUTPUT_UR,
                QRType.XMR_TX_UNSIGNED_UR
                ]:
                print('UR')
                self.decoder = URDecoder()  # BCUR Decoder

            elif self.qr_type in [
                    QRType.SEED__SEEDQR,
                    QRType.SEED__COMPACTSEEDQR,
                    QRType.SEED__MNEMONIC,
                    QRType.SEED__FOUR_LETTER_MNEMONIC
                    ]:
                self.decoder = SeedQrDecoder(wordlist_language_code=self.wordlist_language_code)          

            elif self.qr_type == QRType.SETTINGS:
                self.decoder = SettingsQrDecoder()  # Settings config

            elif self.qr_type == QRType.MONERO_ADDRESS:
                self.decoder = MoneroAddressQrDecoder() # Single Segment monero address

            elif self.qr_type == QRType.MONERO_WALLET:
                self.decoder = MoneroWalletQrDecoder() # Single Segment monero address

        elif self.qr_type != qr_type:
            raise Exception('QR Fragment Unexpected Type Change')

        print(f'decoder: {str(self.decoder)}')
        
        if not self.decoder:
            # Did not find any recognizable format
            return DecodeQRStatus.INVALID
        # Process the binary formats first
        if self.qr_type == QRType.SEED__COMPACTSEEDQR:
            rt = self.decoder.add(data, QRType.SEED__COMPACTSEEDQR)
            if rt == DecodeQRStatus.COMPLETE:
                self.complete = True
            return rt
        # Convert to string data
        # Should always be bytes, but the test suite has some manual datasets that
        # are strings.
        qr_str = data.decode() if type(data) == bytes else data
        if self.qr_type == QRType.SEED__SEEDQR:
            rt = self.decoder.add(data, QRType.SEED__SEEDQR)
            print(f'rt: {rt}')
            if rt == DecodeQRStatus.COMPLETE:
                self.complete = True
            return rt
        if self.qr_type in [
                QRType.XMR_OUTPUT_UR,
                QRType.XMR_KEYIMAGE_UR,
                QRType.XMR_TX_UNSIGNED_UR,
                QRType.XMR_TX_SIGNED_UR,
                QRType.BYTES__UR
                ]:
            self.decoder.receive_part(qr_str)
            if self.decoder.is_complete():
                self.complete = True
                return DecodeQRStatus.COMPLETE
            return DecodeQRStatus.PART_COMPLETE # segment added to ur2 decoder
        else:
            # All other formats use the same method signature
            rt = self.decoder.add(qr_str, self.qr_type)
            if rt == DecodeQRStatus.COMPLETE:
                self.complete = True
            return rt

    def get_output(self):
        if self.complete:
            if self.qr_type == QRType.XMR_OUTPUT_UR:
                cbor = self.decoder.result_message().cbor
                return XmrOutput.from_cbor(cbor).data
        return None

    def get_tx(self):
        if self.complete:
            if self.qr_type == QRType.XMR_TX_UNSIGNED_UR:
                cbor = self.decoder.result_message().cbor
                print(XmrTxUnsigned)
                return XmrTxUnsigned.from_cbor(cbor).data
        return None

    def get_seed_phrase(self):
        if self.is_seed:
            return self.decoder.get_seed_phrase()
        if self.is_wallet:
            return self.decoder.seed

    def get_settings_data(self):
        if self.is_settings:
            return self.decoder.data

    def get_address(self):
        if self.is_address:
            return self.decoder.get_address()

    def get_qr_data(self) -> dict:
        """
        This provides a single access point for external code to retrieve the QR data,
        regardless of which decoder is actually instantiated.
        """
        return self.decoder.get_qr_data()

    def get_address_type(self):
        if self.is_address:
            return self.decoder.get_address_type()

    def get_percent_complete(self) -> int:
        if not self.decoder:
            return 0
        if self.qr_type in [
                QRType.XMR_OUTPUT_UR,
                QRType.XMR_TX_UNSIGNED_UR
                ]:
            return int(self.decoder.estimated_percent_complete() * 100)
        if self.decoder.total_segments == 1:
            # The single frame QR formats are all or nothing
            return 100 if self.decoder.complete else 0
        return 0

    @property
    def is_complete(self) -> bool:
        return self.complete

    @property
    def is_invalid(self) -> bool:
        return self.qr_type == QRType.INVALID

    @property
    def is_ur(self) -> bool:
        return self.qr_type in [
            QRType.XMR_OUTPUT_UR,
            QRType.XMR_TX_UNSIGNED_UR
        ]

    @property
    def is_seed(self):
        print(f'DecodeQR.is_seed(): qr_type: {self.qr_type}')
        return self.qr_type in [
            QRType.SEED__SEEDQR,
            QRType.SEED__COMPACTSEEDQR,
            QRType.SEED__MNEMONIC, 
            QRType.SEED__FOUR_LETTER_MNEMONIC
        ]

    @property
    def is_wallet(self):
        print(f'DecodeQR.is_seed(): qr_type: {self.qr_type}')
        return self.qr_type == QRType.MONERO_WALLET

    @property
    def is_view_only_wallet(self):
        return self.is_wallet and self.decoder.is_view_only

    @property
    def is_json(self):
        return self.qr_type in [QRType.SETTINGS, QRType.JSON]

    @property
    def is_address(self):
        return self.qr_type == QRType.MONERO_ADDRESS

    @property
    def is_settings(self):
        return self.qr_type == QRType.SETTINGS

    @staticmethod
    def extract_qr_data(image: NumpyArray, is_binary:bool = False) -> str:
        if image is None:
            return None
        barcodes = pyzbar.decode(image, symbols=[ZBarSymbol.QRCODE], binary=is_binary)
        # if barcodes:
            # print("--------------- extract_qr_data ---------------")
            # print(barcodes)
        for barcode in barcodes:
            # Only pull and return the first barcode
            return barcode.data

    @staticmethod
    def detect_segment_type(segment: Union[bytes, str], wordlist_language_code: Optional[str] = None):
        # print("-------------- DecodeQR.detect_segment_type --------------")
        # print(type(s))
        # print(len(s))
        try:
            s = segment if type(segment) == str else segment.decode()

            UR_XMR_OUTPUT = 'xmr-output'
            UR_XMR_KEY_IMAGE = 'xmr-keyimage'
            UR_XMR_TX_UNSIGNED = 'xmr-txunsigned'
            UR_XMR_TX_SIGNED = 'xmr-txsigned'
            # XMR UR
            if search(f"^UR:{UR_XMR_OUTPUT}/", s, IGNORECASE):
                return QRType.XMR_OUTPUT_UR
            if search(f'^UR:{UR_XMR_KEY_IMAGE}/', s, IGNORECASE):
                return QRType.XMR_KEYIMAGE_UR
            if search(f'^UR:{UR_XMR_TX_UNSIGNED}/', s, IGNORECASE):
                return QRType.XMR_TX_UNSIGNED_UR
            if search(f'^UR:{UR_XMR_TX_SIGNED}/', s, IGNORECASE):
                return QRType.XMR_TX_SIGNED_UR
            if s.startswith('monero_wallet:'):
                return QRType.MONERO_WALLET
            # Seed
            print(f'search: ({len(s)}){s}')
            if (decimals := search(r'(\d{52,100})', s)) and len(decimals.group(1)) in (52, 64, 100):
                return QRType.SEED__SEEDQR
            # Monero Address
            if MoneroAddressQrDecoder.is_monero_address(s):
                return QRType.MONERO_ADDRESS
            # config data
            if s.startswith("settings::"):
                return QRType.SETTINGS
            # Seed
            # create 4 letter wordlist only if not PSBT (performance gain)
            wordlist = Seed.get_wordlist(wordlist_language_code)
            if all(x in wordlist for x in s.strip().split(" ")):
                # checks if all words in list are in bip39 word list
                return QRType.SEED__MNEMONIC
            try:
                _4LETTER_WORDLIST = [word[:4].strip() for word in wordlist]
            except:
                _4LETTER_WORDLIST = []
            if all(x in _4LETTER_WORDLIST for x in s.strip().split(" ")):
                # checks if all 4 letter words are in list are in 4 letter bip39 word list
                return QRType.SEED__FOUR_LETTER_MNEMONIC
        except UnicodeDecodeError:
            # Probably this isn't meant to be string data; check if it's valid byte data
            # below.
            pass
        # TODO: 2024-08-26, check and write tests
        print(f'byte({len(s)})<{type(s)}>? {s}')
        # Is it byte data?
        # 32 bytes for 24-word CompactSeedQR; 16 bytes for 12-word CompactSeedQR, 22 for polyseed
        if len(s) in (33, 17, 22):
            try:
                bitstream = ''
                for b in s:
                    bitstream += bin(b).lstrip('0b').zfill(8)
                return QRType.SEED__COMPACTSEEDQR
            except Exception as e:
                # Couldn't extract byte data; assume it's not a byte format
                print(f'exception: {e}')
        return QRType.INVALID
