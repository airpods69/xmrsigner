from xmrsigner.models.qr_type import QRType
from xmrsigner.models.polyseed import PolyseedSeed
from xmrsigner.models.monero_encoder import MoneroKeyImageQrEncoder
from xmrsigner.views.view import NotYetImplementedView, View, Destination, BackStackView, MainMenuView
from xmrsigner.models.monero_encoder import ViewOnlyWalletQrEncoder, ViewOnlyWalletJsonQrEncoder
from xmrsigner.gui.screens import seed_screens, WarningScreen, ButtonListScreen, LargeIconStatusScreen
from xmrsigner.helpers.wallet import MoneroWalletRPCManager, WALLET_PORT
from xmrsigner.helpers.network import Network
from xmrsigner.helpers.monero import WalletRpcWrapper
from xmrsigner.models.settings_definition import SettingsConstants, SettingsDefinition
from xmrsigner.gui.button_data import ButtonData
from xmrsigner.gui.components import IconConstants, FontAwesomeIconConstants, GUIConstants
from xmrsigner.gui.screens.wallet_screens import WalletOptionsScreen
from xmrsigner.gui.screens.screen import RET_CODE__BACK_BUTTON, QRDisplayScreen, EtaLoadingScreenThread

from monero.wallet import Wallet as MoneroWallet
from monero.seed import Seed as MoneroSeed

from hashlib import sha256
from time import sleep
from typing import Union, Optional


class WalletViewKeyQRView(View):

    def __init__(self, seed_num: int, network: Optional[Union[str, Network]] = None):
        super().__init__()
        self.seed_num: int = seed_num
        self.seed = self.controller.get_seed(seed_num)

        # Update the seed's network if a specific network is provided
        if network is not None:
            network = Network.ensure(network)
            if self.seed.network != network.value:
                self.seed.change_network(network.value)

        self.wallet: MoneroWallet = self.seed.wallet
        self.height: int = self.seed.height

    def run(self):
        wallet_qr_format: Optional[str] = None
        if len(self.settings.get_value(SettingsConstants.SETTING__VIEW_WALLET_QR_FORMAT)) > 1:
            ret = self.run_screen(
                    ButtonListScreen,
                    title=SettingsDefinition.get_settings_entry(SettingsConstants.SETTING__VIEW_WALLET_QR_FORMAT).display_name,
                    button_data=[ButtonData(format[1]) for format in self.settings.get_multiselect_value_display_names(SettingsConstants.SETTING__VIEW_WALLET_QR_FORMAT)]
            )
            wallet_qr_format = self.settings.get_value(SettingsConstants.SETTING__VIEW_WALLET_QR_FORMAT)[ret]
        else:
            wallet_qr_format = self.settings.get_value(SettingsConstants.SETTING__VIEW_WALLET_QR_FORMAT)[0]
        if wallet_qr_format == SettingsConstants.VIEW_ONLY_WALLET_FORMAT_URI:
            self.run_screen(
                QRDisplayScreen,
                qr_encoder=ViewOnlyWalletQrEncoder(self.wallet, self.height)
            )
            return Destination(BackStackView)
        if wallet_qr_format == SettingsConstants.VIEW_ONLY_WALLET_FORMAT_JSON:
            self.run_screen(
                QRDisplayScreen,
                qr_encoder=ViewOnlyWalletJsonQrEncoder(self.wallet, self.height)
            )
            return Destination(BackStackView)


class WalletViewKeyJsonQRView(WalletViewKeyQRView):

    def run(self):
        self.run_screen(
            QRDisplayScreen,
            qr_encoder=ViewOnlyWalletJsonQrEncoder(self.wallet, self.height)
        )
        return Destination(BackStackView)


class WalletRpcView(View):
    """
    Get information about WalletRpc
    """

    def run(self):
        from xmrsigner.gui.screens.screen import WalletRpcScreen
        try:
            version = MoneroWalletRPCManager().get_version_string()
            if not version:
                raise Exception('Now wallet rpc found')
            self.run_screen(WalletRpcScreen, version=version)
        except Exception:
            self.run_screen(WarningScreen, title='Wallet RPC', text="Couldn't find Wallet RPC, without device is not working properly!", status_headline='Not found', status_color='red')
        from xmrsigner.views.settings_views import SettingsMenuView
        return Destination(SettingsMenuView)


class WalletMenuView(View):
    """
    Get information about WalletRpc
    """

    def run(self):
        from xmrsigner.gui.screens.screen import WalletRpcScreen
        try:
            open_wallets = []
            button_data = []
            daemons = self.controller.wallet_rpc_manager.get_all_daemon_statuses()
            for network, running in daemons.items():
                if running:
                    open_wallets.append(network)
            if len(open_wallets) == 0:
                self.run_screen(WarningScreen, title='No wallet open!', text='At the moment is no wallet open', status_headline='', status_color='red')
                return Destination(MainMenuView)
            for network in open_wallets:
                fp = self.controller.wallet_rpc_manager.get_fingerprint(network)
                print(f'{str(network)}: {fp}')
                if fp:
                    button_data.append((f'{str(network)}: {fp}', None, None, None, IconConstants.CHEVRON_RIGHT))
            selected_menu_num = self.run_screen(
                ButtonListScreen,
                title='Open Wallets',
                is_button_text_centered=False,
                button_data=button_data
            )
            if len(open_wallets) > 0 and selected_menu_num < len(open_wallets):
                return Destination(WalletOptionsView, view_args={'network': open_wallets[selected_menu_num]})
            if selected_menu_num == RET_CODE__BACK_BUTTON:
                return Destination(BackStackView)
        except Exception as e:
            raise e
            self.run_screen(WarningScreen, title='Wallet RPC', text="Couldn't find Wallet RPC, without device is not working properly!", status_headline='Not found', status_color='red')
        return Destination(MainMenuView)


class ExportKeyImagesView(View):

    def __init__(self, network: Union[str, Network], seed_num: Optional[int] = None):
        super().__init__()
        self.network = Network.ensure(network)
        self.wallet: Optional[MoneroWallet] = self.controller.get_wallet(self.network)
        self.seed_num: Optional[int] = seed_num

    def run(self):
        print(f'wallet: {self.wallet}')
        print(f'seed_num: {self.seed_num}')
        if self.wallet is None and self.seed_num is not None:
            print('load wallet')
            return Destination(LoadWalletView, view_args={'seed_num': self.seed_num})
        if self.seed_num is not None and self.controller.get_seed(self.seed_num) != self.controller.get_wallet_seed(self.network):
            return Destination(LoadWalletView, view_args={'seed_num': self.seed_num})
        print('key images')
        try:
            key_image = WalletRpcWrapper(self.wallet).export_encrypted_key_images()
            print(f"key_image result: {key_image}")
        except Exception as e:
            print(e)
            self.run_screen(WarningScreen, title='Key Images Export', text='Error on exporting key images from the wallet. This feature may not be supported by your wallet version.', status_headline='Failed!', status_color='red')
            return Destination(BackStackView)

        if key_image is None:
            self.run_screen(WarningScreen, title='Key Images Export', text='No key images found. Wallet may be new or feature not supported.', status_headline='No Key Images', status_color='yellow')
            return Destination(BackStackView)
        try:
            self.run_screen(
                QRDisplayScreen,
                qr_encoder=MoneroKeyImageQrEncoder(key_image, self.controller.settings.get_value(SettingsConstants.SETTING__QR_DENSITY))
            )
        except Exception as e:
            raise e
            self.run_screen(WarningScreen, title='Key Images Export', text='Error on exporting key images from the wallet', status_headline='Failed!', status_color='red')
            return Destination(BackStackView)
        return Destination(MainMenuView)


class NoOutputsImportedView(View):

    def __init__(self, network: Union[str, Network]):
        super().__init__()
        self.network = Network.ensure(network)
        self.seed: Seed = self.controller.get_wallet_seed(network)

    def run(self):
        self.run_screen(LargeIconStatusScreen, title='Load Outputs', text=f"Wallet {self.seed.fingerprint} has not received funds yet.", status_headline='No balance found!')
        return Destination(MainMenuView)  # TODO: 2024-07-27, thought: redirect to address viewer as soon it exists


class ImportOutputsView(View):

    def __init__(self, seed_num: Optional[int] = None):
        super().__init__()
        self.loading_screen = None
        self.seed = self.controller.get_seed(seed_num) if seed_num else self.controller.selected_seed
        self.network = Network.ensure(self.seed.network) if self.seed else None
        self.wallet: MoneroWallet = self.controller.get_wallet(self.network)
        if self.seed and self.wallet and sha256(str(self.wallet.address()).encode()).hexdigest()[-6:].upper() == self.seed.fingerprint:
            from xmrsigner.gui.screens.screen import LoadingScreenThread
            self.loading_screen = LoadingScreenThread(text=f'Loading Outputs for {self.seed.fingerprint}...')
            self.loading_screen.start()

    def run(self):
        if not self.wallet and self.seed and self.controller.has_seed(self.seed):
            return Destination(LoadWalletView, view_args={'seed_num': self.controller.get_seed_num(self.seed)})
        try:
            num_imported = WalletRpcWrapper(self.wallet).import_outputs(self.controller.outputs)
            if int(num_imported) == 0:  # we have a zero balance
                if self.loading_screen:
                    self.loading_screen.stop()
                return Destination(NoOutputsImportedView, view_args={'network': self.network})
            if self.loading_screen:
                self.loading_screen.stop()
            self.run_screen(LargeIconStatusScreen, title='Loaded Outputs', text=f"Loaded {num_imported} outputs for {self.seed.fingerprint} into wallet.", status_headline='Success!')
            return Destination(ExportKeyImagesView, view_args={'network': self.network})
        except Exception as e:
            print(e)
        if self.loading_screen:
            self.loading_screen.stop()
        self.run_screen(WarningScreen, title='Import outputs', text=f'Error on importing outputs into wallet {self.seed.fingerprint}', status_headline='Failed!', status_color='red')
        return Destination(MainMenuView)


class WalletOptionsView(View):
    """
    Views for actions on individual seeds:
    """

    SCAN = ButtonData('Scan for Wallet').with_icon(IconConstants.SCAN)
    EXPORT_KEY_IMAGES = ButtonData('Export Key Imags').with_icon(IconConstants.QRCODE)
    VIEW_ONLY_WALLET = ButtonData('View only Wallet').with_icon(IconConstants.QRCODE)
    PURGE_WALLET = ButtonData('Purge from Wallet').with_icon(FontAwesomeIconConstants.TRASH_CAN).with_icon_color(GUIConstants.RED).with_label_color(GUIConstants.RED)

    def __init__(self, network: Union[str, Network]):
        super().__init__()
        self.network = Network.ensure(network)
        self.fingerprint: str = self.controller.wallet_rpc_manager.get_fingerprint(self.network)
        self.seed = self.controller.get_wallet_seed(self.network)

    def run(self):
        button_data = []
        button_data.append(self.SCAN)
        button_data.append(self.EXPORT_KEY_IMAGES)
        button_data.append(self.VIEW_ONLY_WALLET)
        # button_data.append(self.PURGE_WALLET)  # TODO: 2024-08-09 implement
        selected_menu_num = self.run_screen(
            WalletOptionsScreen,
            button_data=button_data,
            fingerprint=self.fingerprint,
            polyseed=isinstance(self.seed, PolyseedSeed),
            my_monero=self.seed.is_my_monero,
            has_passphrase=self.seed.has_passphrase
        )
        if selected_menu_num == RET_CODE__BACK_BUTTON:
            return Destination(BackStackView)
        if button_data[selected_menu_num] == self.SCAN:
            from xmrsigner.views.scan_views import ScanUR2View
            return Destination(ScanUR2View)
        if button_data[selected_menu_num] == self.VIEW_ONLY_WALLET:
            return Destination(WalletViewKeyQRView, view_args={'seed_num': self.controller.get_seed_num(self.seed), 'network': self.network})
        if button_data[selected_menu_num] == self.PURGE_WALLET:  # TODO: 2024-08-04, implement
            # return Destination(PurgeWalletView, view_args={'seed_num': self.seed_num})
            pass
        if button_data[selected_menu_num] == self.EXPORT_KEY_IMAGES:
            return Destination(ExportKeyImagesView, view_args={'network': self.network})


class LoadWalletView(View):

    def __init__(self, seed_num: int):
        super().__init__()
        self.loading_screen = None
        self.wallet_seed = self.controller.get_seed(seed_num)

        if self.controller.get_wallet(self.wallet_seed.network) is None or self.controller.get_wallet_seed(self.wallet_seed.network) != self.wallet_seed:
            self.loading_screen = EtaLoadingScreenThread(text="Loading Wallet...", eta=180)
            self.loading_screen.start()

    def run(self):
        if self.controller.get_wallet(self.wallet_seed.network) and self.controller.get_wallet_seed(self.wallet_seed.network) == self.wallet_seed:
            return Destination(BackStackView)
        try:
            network = self.wallet_seed.network
            print(f'LoadWalletView: starting daemon with network: {network}')
            self.controller.wallet_rpc_manager.start_daemon(network)
            print('Wait for rpc comming up...', end='', flush=True)
            while not self.controller.wallet_rpc_manager.is_rpc_running(network):
                print('.', end='', flush=True)
                sleep(0.2)
            print('Done')
            self.controller.wallet_rpc_manager.close_wallet(network)
            moneroSeed: MoneroSeed = self.wallet_seed.monero_seed
            # Pass the correct network to generate the appropriate address
            from monero.const import NET_MAIN, NET_TEST, NET_STAGE
            print(f"DEBUG: network type: {type(network)}")
            print(f"DEBUG: network value: {network}")
            print(f"DEBUG: str(network): {str(network)}")
            network_const = NET_MAIN
            network_str = str(network)
            if network_str == "testnet":
                network_const = NET_TEST
                print("DEBUG: Setting network_const to NET_TEST")
            elif network_str == "stagenet" or network_str == "stage":
                network_const = NET_STAGE
                print("DEBUG: Setting network_const to NET_STAGE")
            else:
                print(f"DEBUG: No match, using default NET_MAIN, str(network) = '{network_str}'")
                
            public_address = moneroSeed.public_address(network_const)
            view_key = moneroSeed.secret_view_key()
            spend_key = moneroSeed.secret_spend_key()
            
            # Debug information
            print(f"DEBUG: Network: {network}")
            print(f"DEBUG: Network const: {network_const}")
            print(f"DEBUG: Public address: {public_address}")
            print(f"DEBUG: View key: {view_key[:10]}...")  # First 10 chars for privacy
            print(f"DEBUG: Spend key: {spend_key[:10]}...")  # First 10 chars for privacy
            
            self.controller.wallet_rpc_manager.load_wallet(
                network,
                self.wallet_seed.fingerprint,
                public_address,
                view_key,
                spend_key,
                self.wallet_seed.height,
                self.wallet_seed.passphrase
                )
            self.controller.set_wallet(network, MoneroWallet(port=WALLET_PORT.forNetwork(network)))
            self.controller.set_wallet_seed(network, self.wallet_seed)
        except Exception as e:
            # Error occured, we have no more progress
            if self.loading_screen:
                self.loading_screen.stop()
            raise e
        # Everything is set. Stop the loading screen
        if self.loading_screen:
            self.loading_screen.stop()
        return Destination(BackStackView)
