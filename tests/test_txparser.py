import pytest
from unittest.mock import patch, MagicMock
from xmrsigner.models.tx_parser import TxParser

def test_txparser_with_mock_data():
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

def test_txparser_get_recipients():
    """Test getting recipients from TxParser"""
    # Create mock transaction bytes
    mock_tx_bytes = b"mock transaction data"
    
    # Create parser instance
    parser = TxParser(mock_tx_bytes)
    
    # Mock the parsed data
    parser.parsed_data = {
        'recipients': [
            {'address': '4Address1', 'amount': 1000000000},
            {'address': '4Address2', 'amount': 2000000000}
        ],
        'fee': 10000000,
        'unlock_time': 0
    }
    
    # Test getting recipients
    recipients = parser.get_recipients()
    
    # Verify the result
    assert len(recipients) == 2
    assert recipients[0]['address'] == '4Address1'
    assert recipients[0]['amount'] == 1000000000
    assert recipients[1]['address'] == '4Address2'
    assert recipients[1]['amount'] == 2000000000

def test_txparser_get_fee():
    """Test getting fee from TxParser"""
    # Create mock transaction bytes
    mock_tx_bytes = b"mock transaction data"
    
    # Create parser instance
    parser = TxParser(mock_tx_bytes)
    
    # Mock the parsed data
    parser.parsed_data = {
        'recipients': [],
        'fee': 10000000,
        'unlock_time': 0
    }
    
    # Test getting fee
    fee = parser.get_fee()
    
    # Verify the result
    assert fee == 10000000

def test_txparser_get_unlock_time():
    """Test getting unlock time from TxParser"""
    # Create mock transaction bytes
    mock_tx_bytes = b"mock transaction data"
    
    # Create parser instance
    parser = TxParser(mock_tx_bytes)
    
    # Mock the parsed data
    parser.parsed_data = {
        'recipients': [],
        'fee': 10000000,
        'unlock_time': 123456
    }
    
    # Test getting unlock time
    unlock_time = parser.get_unlock_time()
    
    # Verify the result
    assert unlock_time == 123456