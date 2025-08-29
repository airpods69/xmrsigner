import unittest
from xmrsigner.models.seed import Seed
from monero.const import NET_MAIN, NET_TEST, NET_STAGE

class TestSeedNetworkUpdate(unittest.TestCase):
    
    def test_seed_change_network(self):
        """Test that change_network method works correctly"""
        # Create a seed with mainnet
        seed = Seed([
            'abbey', 'abducts', 'ability', 'ablaze', 'abnormal', 'abort', 'abrasive', 'absorb', 'abyss', 'academy',
            'aces', 'aching', 'acidic', 'acoustic', 'acquire', 'across', 'actress', 'actual', 'adapt', 'addicted',
            'adequate', 'adhesive', 'adjust', 'adopt', 'adult'
        ], network=NET_MAIN)
        
        # Check initial network
        self.assertEqual(seed.network, NET_MAIN)
        
        # Change to testnet
        seed.change_network(NET_TEST)
        self.assertEqual(seed.network, NET_TEST)
        
        # Change to stagenet
        seed.change_network(NET_STAGE)
        self.assertEqual(seed.network, NET_STAGE)

if __name__ == '__main__':
    unittest.main()