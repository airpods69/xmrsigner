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
import numpy as np


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
        print("DEBUG: add_image called")
        data = DecodeQR.extract_qr_data(image, is_binary=True)
        if data == None:
            print("DEBUG: No QR data found in image")
            return DecodeQRStatus.FALSE
        print(f"DEBUG: Found QR data: {data[:50]}..." if len(data) > 50 else f"DEBUG: Found QR data: {data}")
        print(f"DEBUG: QR data type: {type(data)}")
        print(f"DEBUG: QR data length: {len(data)}")

        # Additional check for empty or invalid data
        if isinstance(data, bytes) and len(data) == 0:
            print("DEBUG: QR data is empty bytes")
            return DecodeQRStatus.FALSE

        return self.add_data(data)

    def add_data(self, data) -> DecodeQRStatus:
        if data == None:
            print("DEBUG: No data to process")
            return DecodeQRStatus.FALSE

        qr_type = DecodeQR.detect_segment_type(data, wordlist_language_code=self.wordlist_language_code)
        print(f'DEBUG: Detected QR type: {qr_type}')

        if self.qr_type == None:
            self.qr_type = qr_type
            print(f'DEBUG: Setting QR type to: {self.qr_type}')

            if self.qr_type in [
                QRType.XMR_OUTPUT_UR,
                QRType.XMR_TX_UNSIGNED_UR
                ]:
                print('DEBUG: Initializing UR decoder')
                self.decoder = URDecoder()  # BCUR Decoder

            elif self.qr_type in [
                    QRType.SEED__SEEDQR,
                    QRType.SEED__COMPACTSEEDQR,
                    QRType.SEED__MNEMONIC,
                    QRType.SEED__FOUR_LETTER_MNEMONIC
                    ]:
                print('DEBUG: Initializing Seed QR decoder')
                self.decoder = SeedQrDecoder(wordlist_language_code=self.wordlist_language_code)

            elif self.qr_type == QRType.SETTINGS:
                print('DEBUG: Initializing Settings QR decoder')
                # self.decoder = SettingsQrDecoder()  # Settings config

            elif self.qr_type == QRType.MONERO_ADDRESS:
                print('DEBUG: Initializing Monero Address QR decoder')
                self.decoder = MoneroAddressQrDecoder() # Single Segment monero address

            elif self.qr_type == QRType.MONERO_WALLET:
                print('DEBUG: Initializing Monero Wallet QR decoder')
                self.decoder = MoneroWalletQrDecoder() # Single Segment monero address

        elif self.qr_type != qr_type:
            print(f"DEBUG: QR type mismatch - expected {self.qr_type}, got {qr_type}")
            raise Exception('QR Fragment Unexpected Type Change')

        print(f'DEBUG: Using decoder: {str(self.decoder)}')

        if not self.decoder:
            # Did not find any recognizable format
            print("DEBUG: No decoder found for QR type")
            return DecodeQRStatus.INVALID

        # Process the binary formats first
        if self.qr_type == QRType.SEED__COMPACTSEEDQR:
            print("DEBUG: Processing CompactSeedQR")
            rt = self.decoder.add(data, QRType.SEED__COMPACTSEEDQR)
            if rt == DecodeQRStatus.COMPLETE:
                self.complete = True
                print("DEBUG: CompactSeedQR decoding complete")
            return rt

        # Convert to string data
        # Should always be bytes, but the test suite has some manual datasets that
        # are strings.
        qr_str = data.decode() if type(data) == bytes else data
        print(f"DEBUG: QR string data: {qr_str}")

        if self.qr_type == QRType.SEED__SEEDQR:
            print("DEBUG: Processing SeedQR")
            rt = self.decoder.add(data, QRType.SEED__SEEDQR)
            print(f'DEBUG: SeedQR decoder result: {rt}')
            if rt == DecodeQRStatus.COMPLETE:
                self.complete = True
                print("DEBUG: SeedQR decoding complete")
            return rt

        if self.qr_type in [
                QRType.XMR_OUTPUT_UR,
                QRType.XMR_KEYIMAGE_UR,
                QRType.XMR_TX_UNSIGNED_UR,
                QRType.XMR_TX_SIGNED_UR,
                QRType.BYTES__UR
                ]:
            print(f"DEBUG: Processing UR type: {self.qr_type}")
            print(f"DEBUG: Adding part to UR decoder: {qr_str}")
            self.decoder.receive_part(qr_str)
            print(f"DEBUG: UR decoder is_complete: {self.decoder.is_complete()}")
            if self.decoder.is_complete():
                self.complete = True
                print("DEBUG: UR decoding complete")
                return DecodeQRStatus.COMPLETE
            print("DEBUG: UR part added, waiting for more parts")
            return DecodeQRStatus.PART_COMPLETE # segment added to ur2 decoder

        else:
            # All other formats use the same method signature
            print(f"DEBUG: Processing other QR type: {self.qr_type}")
            rt = self.decoder.add(qr_str, self.qr_type)
            if rt == DecodeQRStatus.COMPLETE:
                self.complete = True
                print("DEBUG: Other QR type decoding complete")
            return rt

    def get_output(self):
        if self.complete:
            if self.qr_type == QRType.XMR_OUTPUT_UR:
                cbor = self.decoder.result_message().cbor
                return XmrOutput.from_cbor(cbor).data
        return None

    def get_tx(self):
        print(f"DEBUG: get_tx called - complete: {self.complete}, qr_type: {self.qr_type}")
        if self.complete:
            if self.qr_type == QRType.XMR_TX_UNSIGNED_UR:
                cbor = self.decoder.result_message().cbor
                print(f"DEBUG: CBOR data: {cbor}")
                print(XmrTxUnsigned)
                return XmrTxUnsigned.from_cbor(cbor).data
        print("DEBUG: get_tx returning None")
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
            print("DEBUG: get_percent_complete - no decoder")
            return 0
        if self.qr_type in [
                QRType.XMR_OUTPUT_UR,
                QRType.XMR_TX_UNSIGNED_UR
                ]:
            percent = int(self.decoder.estimated_percent_complete() * 100)
            print(f"DEBUG: UR percent complete: {percent}%")
            return percent
        if self.decoder.total_segments == 1:
            # The single frame QR formats are all or nothing
            percent = 100 if self.decoder.complete else 0
            print(f"DEBUG: Single frame QR percent complete: {percent}%")
            return percent
        print("DEBUG: get_percent_complete returning 0")
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
            print("DEBUG: No image data to process")
            return None

        print(f"DEBUG: Extracting QR data from image - shape: {image.shape if hasattr(image, 'shape') else 'unknown'}")

        # List of decoding approaches to try, in order of likelihood to succeed
        decoding_approaches = [
            ("default", {"symbols": [ZBarSymbol.QRCODE], "binary": is_binary}),
            ("density=2", {"symbols": [ZBarSymbol.QRCODE], "binary": is_binary, "x_density": 2, "y_density": 2}),
            ("density=3", {"symbols": [ZBarSymbol.QRCODE], "binary": is_binary, "x_density": 3, "y_density": 3}),
            ("binary=False", {"symbols": [ZBarSymbol.QRCODE], "binary": False}),
            ("binary=False, density=2", {"symbols": [ZBarSymbol.QRCODE], "binary": False, "x_density": 2, "y_density": 2}),
            ("no symbols", {"binary": is_binary}),
        ]

        # Try each approach
        for approach_name, params in decoding_approaches:
            try:
                print(f"DEBUG: Trying decoding approach: {approach_name}")
                barcodes = pyzbar.decode(image, **params)
                print(f"DEBUG: Found {len(barcodes)} barcodes with {approach_name}")

                if barcodes:
                    # Check each barcode
                    for i, barcode in enumerate(barcodes):
                        print(f"DEBUG: Barcode {i} data type: {type(barcode.data)}")
                        print(f"DEBUG: Barcode {i} data length: {len(barcode.data)}")
                        print(f"DEBUG: Barcode {i} data repr: {repr(barcode.data)}")

                        # Check if data is valid
                        if barcode.data is None:
                            print(f"DEBUG: Barcode {i} has None data")
                            continue

                        if len(barcode.data) == 0:
                            print(f"DEBUG: Barcode {i} has empty data")
                            continue

                        # Successfully decoded at least one barcode with valid data
                        print(f"DEBUG: Successfully decoded QR code with approach: {approach_name}")
                        return barcode.data
            except Exception as e:
                print(f"DEBUG: Error with {approach_name}: {e}")
                import traceback
                traceback.print_exc()
                continue

        # Try OpenCV as a fallback
        print("DEBUG: Trying OpenCV as fallback")
        try:
            import cv2
            # Convert PIL image to OpenCV format if needed
            if hasattr(image, 'shape'):
                # Already a numpy array
                cv_image = image
            else:
                # Convert PIL Image to numpy array
                cv_image = np.array(image)
                # Convert RGB to BGR
                cv_image = cv2.cvtColor(cv_image, cv2.COLOR_RGB2BGR)

            # Create QR detector
            qr_detector = cv2.QRCodeDetector()

            # Detect and decode
            data, bbox, straight_qrcode = qr_detector.detectAndDecode(cv_image)

            if data:
                print(f"DEBUG: OpenCV successfully decoded QR code: {data}")
                return data.encode('utf-8')
            else:
                print("DEBUG: OpenCV failed to decode QR code")
        except Exception as e:
            print(f"DEBUG: Error with OpenCV approach: {e}")
            import traceback
            traceback.print_exc()

        print("DEBUG: No QR codes found with any approach")
        return None

    @staticmethod
    def detect_segment_type(segment: Union[bytes, str], wordlist_language_code: Optional[str] = None):
        print("-------------- DecodeQR.detect_segment_type --------------")
        print(f"Input type: {type(segment)}")
        print(f"Input length: {len(segment) if segment else 0}")
        print(f"Input value: {repr(segment)[:100]}{'...' if segment and len(repr(segment)) > 100 else ''}")

        # Handle empty or None input
        if not segment:
            print("DEBUG: Empty or None segment, returning INVALID")
            return QRType.INVALID

        if len(segment) == 0:
            print("DEBUG: Empty segment, returning INVALID")
            return QRType.INVALID

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
        except Exception as e:
            print(f"DEBUG: Exception in detect_segment_type: {e}")
            return QRType.INVALID

        # Handle the case where s might not be defined due to early return
        if 's' not in locals():
            print("DEBUG: s not defined, returning INVALID")
            return QRType.INVALID

        # TODO: 2024-08-26, check and write tests
        print(f'byte({len(s)})<{type(s)}>? {s}')
        # Is it byte data?
        # 32 bytes for 24-word CompactSeedQR; 16 bytes for 12-word CompactSeedQR, 22 for polyseed
        if len(s) in (33, 17, 22):
            # TODO: Fix this return statmenmets because you can't really structurally reach the bottom part. Something might be wrong
            try:
                bitstream = ''
                for b in s:
                    bitstream += bin(b).lstrip('0b').zfill(8)
                return QRType.SEED__COMPACTSEEDQR
            except Exception as e:
                # Couldn't extract byte data; assume it's not a byte format
                print(f'exception: {e}')
                return QRType.INVALID
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

        # TODO: 2024-08-26, check and write tests
        print(f'byte({len(s)})<{type(s)}>? {s}')
        # Is it byte data?
        # 32 bytes for 24-word CompactSeedQR; 16 bytes for 12-word CompactSeedQR, 22 for polyseed
        if type(segment) == bytes and len(segment) in (33, 17, 22):
            try:
                bitstream = ''
                for b in segment:
                    bitstream += bin(b).lstrip('0b').zfill(8)
                return QRType.SEED__COMPACTSEEDQR
            except Exception as e:
                # Couldn't extract byte data; assume it's not a byte format
                print(f'exception: {e}')
        return QRType.INVALID
