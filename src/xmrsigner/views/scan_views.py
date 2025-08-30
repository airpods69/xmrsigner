import json
import re

from xmrsigner.controller import Controller
from xmrsigner.gui.screens.screen import RET_CODE__BACK_BUTTON
from xmrsigner.models.seed import Seed
from xmrsigner.models.polyseed import PolyseedSeed
from xmrsigner.models.qr_type import QRType
from xmrsigner.models.decode_qr import DecodeQR
from xmrsigner.models.settings import SettingsConstants
from xmrsigner.views.settings_views import SettingsIngestSettingsQRView
from xmrsigner.views.view import (
    BackStackView,
    ErrorView,
    MainMenuView,
    NotYetImplementedView,
    OptionDisabledView,
    View,
    Destination
)
from typing import Optional, List



class ScanView(View):
    """
        The catch-all generic scanning View that will accept any of our supported QR
        formats and will route to the most sensible next step.

        Can also be used as a base class for more specific scanning flows with
        dedicated errors when an unexpected QR type is scanned (e.g. Scan Tx was
        selected but a SeedQR was scanned).
    """

    instructions_text = "Scan a QR code"
    invalid_qr_type_message = "QRCode not recognized or not yet supported."


    def __init__(self):
        super().__init__()
        # Define the decoder here to make it available to child classes' is_valid_qr_type
        # checks and so we can inject data into it in the test suite's `before_run()`.
        self.wordlist_language_code = self.settings.get_value(SettingsConstants.SETTING__MONERO_WORDLIST_LANGUAGE)  # TODO: 2024-08-08, not sure if this is a good idea, refactor one day
        self.decoder: DecodeQR = DecodeQR(wordlist_language_code=self.wordlist_language_code)


    @property
    def is_valid_qr_type(self):
        return True

    def run(self):
        from xmrsigner.gui.screens.scan_screens import ScanScreen
        # Start the live preview and background QR reading
        self.run_screen(
            ScanScreen,
            instructions_text=self.instructions_text,
            decoder=self.decoder
        )
        # Handle the results
        if self.decoder.is_complete:
            if not self.is_valid_qr_type:
                # We recognized the QR type but it was not the type expected for the
                # current flow.
                # Report QR types in more human-readable text (e.g. QRType
                # `seed__compactseedqr` as "seed: compactseedqr").
                return Destination(ErrorView, view_args=dict(
                    title='Error',
                    status_headline='Wrong QR Type',
                    text=self.invalid_qr_type_message + f""", received "{self.decoder.qr_type.replace("__", ": ").replace("_", " ")}\" format""",
                    button_text='Back',
                    next_destination=Destination(BackStackView, skip_current_view=True),
                ))
            if self.decoder.is_seed or (self.decoder.is_wallet and not self.decoder.is_view_only_wallet):
                seed_mnemonic: Optional[List] = self.decoder.get_seed_phrase()
                if not seed_mnemonic:
                    # seed is not valid, Exit if not valid with message
                    raise Exception('Not yet implemented!')
                # Found a valid mnemonic seed! All new seeds should be considered
                #   pending (might set a passphrase, SeedXOR, etc) until finalized.
                from xmrsigner.views.seed_views import SeedFinalizeView
                self.controller.jar.set_pending_seed(
                    Seed(mnemonic=seed_mnemonic, wordlist_language_code=self.wordlist_language_code)
                    if len(seed_mnemonic) != 16 else
                    PolyseedSeed(mnemonic=seed_mnemonic, wordlist_language_code=self.wordlist_language_code)
                )
                if self.settings.get_value(SettingsConstants.SETTING__MONERO_SEED_PASSPHRASE if len(seed_mnemonic) != 16 else SettingsConstants.SETTING__POLYSEED_PASSPHRASE) == SettingsConstants.OPTION__REQUIRED:
                    from xmrsigner.views.seed_views import SeedAddPassphraseView
                    return Destination(SeedAddPassphraseView)
                return Destination(SeedFinalizeView)
            if self.decoder.is_ur:
                if self.decoder.qr_type == QRType.XMR_OUTPUT_UR:
                    self.controller.outputs = self.decoder.get_output()
                    from xmrsigner.views.monero_views import MoneroSelectSeedView
                    return Destination(MoneroSelectSeedView, view_args={'flow': Controller.FLOW__SYNC}, skip_current_view=True)
                if self.decoder.qr_type == QRType.XMR_TX_UNSIGNED_UR:
                    from xmrsigner.views.monero_views import MoneroSelectSeedView
                    tx = self.decoder.get_tx()
                    self.controller.transaction = tx
                    return Destination(MoneroSelectSeedView, view_args={'flow': Controller.FLOW__TX}, skip_current_view=True)
                raise Exception('Not Implemented Yet!')
            if self.decoder.is_settings:
                data = self.decoder.get_settings_data()
                return Destination(SettingsIngestSettingsQRView, view_args=dict(data=data))
            return Destination(NotYetImplementedView)
        if self.decoder.is_invalid:
            # For now, don't even try to re-do the attempted operation, just reset and
            # start everything over.
            self.controller.resume_main_flow = None
            return Destination(ErrorView, view_args=dict(
                title='Error',
                status_headline='Unknown QR Type',
                text='QRCode is invalid or is a data format not yet supported.',
                button_text='Done',
                next_destination=Destination(MainMenuView, clear_history=True),
            ))
        return Destination(MainMenuView)


class ScanUR2View(ScanView):

    instructions_text = "Scan UR"
    invalid_qr_type_message = "Expected a UR"

    @property
    def is_valid_qr_type(self):
        return self.decoder.is_ur


class ScanOutputsView(ScanUR2View):  # TODO: 2024-07-23, implement
    pass


class ScanUnsignedTransactionView(ScanUR2View):
    """
    Scans an unsigned transaction QR code and displays its details.
    """
    
    def __init__(self):
        super().__init__()
        self.instructions_text = "Scan Unsigned Transaction QR"
        self.invalid_qr_type_message = "Expected an unsigned transaction QR"
        
    @property
    def is_valid_qr_type(self):
        # Only accept unsigned transaction QR codes
        return self.decoder.is_ur and self.decoder.qr_type == QRType.XMR_TX_UNSIGNED_UR
        
    def run(self):
        from xmrsigner.gui.screens.scan_screens import ScanScreen
        from xmrsigner.views.monero_views import OverviewView
        
        print("DEBUG: Starting ScanUnsignedTransactionView")
        
        # Start the live preview and background QR reading
        self.run_screen(
            ScanScreen,
            instructions_text=self.instructions_text,
            decoder=self.decoder
        )
        
        print(f"DEBUG: Scan completed - is_complete: {self.decoder.is_complete}, is_invalid: {self.decoder.is_invalid}")
        print(f"DEBUG: QR type: {self.decoder.qr_type}")
        
        # Handle the results
        if self.decoder.is_complete:
            print("DEBUG: Decoder is complete")
            if not self.is_valid_qr_type:
                print("DEBUG: Invalid QR type")
                # We recognized the QR type but it was not the type expected for the
                # current flow.
                return Destination(ErrorView, view_args=dict(
                    title='Error',
                    status_headline='Wrong QR Type',
                    text=self.invalid_qr_type_message + f""", received "{self.decoder.qr_type.replace("__", ": ").replace("_", " ")}" format""",
                    button_text='Back',
                    next_destination=Destination(BackStackView, skip_current_view=True),
                ))
                
            if self.decoder.qr_type == QRType.XMR_TX_UNSIGNED_UR:
                print("DEBUG: Getting transaction data")
                # Get the transaction data
                tx = self.decoder.get_tx()
                if tx:
                    print("DEBUG: Transaction data retrieved successfully")
                    self.controller.transaction = tx
                    
                    # Go to the transaction overview view
                    return Destination(OverviewView)
                else:
                    print("DEBUG: Failed to get transaction data")
                
        if self.decoder.is_invalid:
            print("DEBUG: Decoder is invalid")
            # For now, don't even try to re-do the attempted operation, just reset and
            # start everything over.
            self.controller.resume_main_flow = None
            return Destination(ErrorView, view_args=dict(
                title='Error',
                status_headline='Invalid Transaction',
                text='The scanned QR code is invalid or corrupted.',
                button_text='Done',
                next_destination=Destination(MainMenuView, clear_history=True),
            ))
            
        print("DEBUG: Returning to main menu")
        return Destination(MainMenuView)


class ScanSeedQRView(ScanView):

    instructions_text = "Scan SeedQR"
    invalid_qr_type_message = f"Expected a SeedQR"

    @property
    def is_valid_qr_type(self):
        return self.decoder.is_seed


class ScanAddressView(ScanView):

    instructions_text = "Scan address QR"
    invalid_qr_type_message = "Expected an address QR"
 
    @property
    def is_valid_qr_type(self):
        return self.decoder.is_address
