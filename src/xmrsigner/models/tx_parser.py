class TxParser:
    """
    Parser for Monero transactions that extracts key information from the unsigned transaction set.
    """
    
    def __init__(self, unsigned_tx_bytes: bytes):
        self.unsigned_tx_bytes = unsigned_tx_bytes
        self.parsed_data = None
        
    def parse(self):
        """
        Parse the unsigned transaction bytes and extract transaction details.
        """
        # For now, we'll use the existing TxDecoder implementation
        # In the future, we might want to expand this parser to handle more details
        from xmrsigner.models.tx_decoder import TxDecoder
        decoder = TxDecoder(self.unsigned_tx_bytes)
        self.parsed_data = decoder.parse()
        return self.parsed_data
        
    def get_recipients(self):
        """
        Get the list of recipients and amounts.
        """
        if not self.parsed_data:
            self.parse()
        return self.parsed_data.get('recipients', [])
        
    def get_fee(self):
        """
        Get the transaction fee.
        """
        if not self.parsed_data:
            self.parse()
        return self.parsed_data.get('fee', 0)
        
    def get_unlock_time(self):
        """
        Get the transaction unlock time.
        """
        if not self.parsed_data:
            self.parse()
        return self.parsed_data.get('unlock_time', 0)
