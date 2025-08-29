import pytest
from unittest.mock import patch, MagicMock
from xmrsigner.models.tx_parser import TxParser

def test_tx_parser_integration():
    """Test integration of TxParser with transaction flow"""
    # Create mock transaction bytes
    mock_tx_bytes = b"mock transaction data"
    
    # Create parser instance
    parser = TxParser(mock_tx_bytes)
    
    # Verify it can be created
    assert parser is not None
    
    # Verify it has the expected attributes
    assert hasattr(parser, 'unsigned_tx_bytes')
    assert hasattr(parser, 'parsed_data')
    assert parser.parsed_data is None

def test_tx_parser_with_mock_data():
    """Test TxParser with mock transaction data"""
    # Create mock transaction bytes
    mock_tx_bytes = b"mock transaction data"
    
    # Create parser instance
    parser = TxParser(mock_tx_bytes)
    
    # Mock the TxDecoder to return specific data
    with patch('xmrsigner.models.tx_decoder.TxDecoder') as mock_decoder_class:
        mock_decoder_instance = MagicMock()
        mock_decoder_instance.parse.return_value = {
            'recipients': [
                {'address': '4Address1', 'amount': 1000000000},
                {'address': '4Address2', 'amount': 2000000000}
            ],
            'fee': 10000000,
            'unlock_time': 0
        }
        mock_decoder_class.return_value = mock_decoder_instance
        
        # Test parsing
        result = parser.parse()
        
        # Verify the mock was called correctly
        mock_decoder_class.assert_called_once_with(mock_tx_bytes)
        mock_decoder_instance.parse.assert_called_once()
        
        # Verify the result
        assert 'recipients' in result
        assert 'fee' in result
        assert 'unlock_time' in result
        assert len(result['recipients']) == 2
        assert result['fee'] == 10000000
        assert result['unlock_time'] == 0