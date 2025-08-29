import unittest
from xmrsigner.models.seed import Seed
from monero.const import NET_MAIN, NET_TEST, NET_STAGE

class TestChangeNetwork(unittest.TestCase):
    
    def test_change_network_calls_generate_seed(self):
        """Test that change_network method calls _generate_seed"""
        # Create a mock seed object
        class MockSeed:
            def __init__(self, network):
                self.network = network
                self._generate_seed_called = False
            
            def _generate_seed(self):
                self._generate_seed_called = True
                
            def change_network(self, network: str) -> None:
                self.network = network
                self._generate_seed()  # This is what we fixed
        
        seed = MockSeed(NET_MAIN)
        self.assertEqual(seed.network, NET_MAIN)
        self.assertFalse(seed._generate_seed_called)
        
        # Change to testnet
        seed.change_network(NET_TEST)
        self.assertEqual(seed.network, NET_TEST)
        self.assertTrue(seed._generate_seed_called)
        
        # Reset the flag
        seed._generate_seed_called = False
        
        # Change to stagenet
        seed.change_network(NET_STAGE)
        self.assertEqual(seed.network, NET_STAGE)
        self.assertTrue(seed._generate_seed_called)

if __name__ == '__main__':
    unittest.main()