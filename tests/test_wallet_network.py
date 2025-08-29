import unittest
from xmrsigner.models.seed import Seed
from xmrsigner.views.wallet_views import WalletViewKeyQRView
from xmrsigner.controller import Controller
from xmrsigner.models.settings import Settings
from monero.const import NET_MAIN, NET_TEST, NET_STAGE

class MockController:
    def __init__(self):
        self.jar = MockSeedJar()
        
    def get_seed(self, seed_num):
        return self.jar.seeds[seed_num]

class MockSeedJar:
    def __init__(self):
        # Create a seed with mainnet by default
        self.seeds = [Seed([
            'abbey', 'abducts', 'ability', 'ablaze', 'abnormal', 'abort', 'abrasive', 'absorb', 'abyss', 'academy',
            'aces', 'aching', 'acidic', 'acoustic', 'acquire', 'across', 'actress', 'actual', 'adapt', 'addicted',
            'adequate', 'adhesive', 'adjust', 'adopt'
        ], network=NET_MAIN)]

class MockSettings:
    def get_value(self, key):
        # Mock implementation
        return [NET_MAIN, NET_TEST, NET_STAGE]

class TestWalletViewKeyQRView(unittest.TestCase):
    
    def setUp(self):
        # Mock the controller and settings
        self.mock_controller = MockController()
        self.mock_settings = MockSettings()
        
        # Temporarily replace the real controller and settings with mocks
        self.original_controller = Controller._instance
        self.original_settings = Settings._instance
        Controller._instance = self.mock_controller
        Settings._instance = self.mock_settings
        
    def tearDown(self):
        # Restore the original controller and settings
        Controller._instance = self.original_controller
        Settings._instance = self.original_settings
    
    def test_wallet_view_key_qr_view_network_update(self):
        """Test that WalletViewKeyQRView updates seed network correctly"""
        # Create a WalletViewKeyQRView with a specific network
        view = WalletViewKeyQRView(seed_num=0, network=NET_TEST)
        
        # Check that the seed's network was updated
        self.assertEqual(view.seed.network, NET_TEST)
        
        # Create another WalletViewKeyQRView with stagenet
        view2 = WalletViewKeyQRView(seed_num=0, network=NET_STAGE)
        
        # Check that the seed's network was updated
        self.assertEqual(view2.seed.network, NET_STAGE)

if __name__ == '__main__':
    unittest.main()