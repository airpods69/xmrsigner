#!/usr/bin/env python3

"""
Debug script for testing QR code scanning with detailed logging
"""

import sys
import os

# Add the src directory to the path so we can import xmrsigner modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from xmrsigner.models.decode_qr import DecodeQR
from xmrsigner.models.qr_type import QRType

def test_ur_qr_data(qr_data):
    """Test UR QR data decoding with detailed logging"""
    print("=== Testing UR QR Data Decoding ===")
    
    # Create a decoder instance
    decoder = DecodeQR()
    
    # Add the data
    result = decoder.add_data(qr_data.encode() if isinstance(qr_data, str) else qr_data)
    
    print(f"Decoder result: {result}")
    print(f"QR type: {decoder.qr_type}")
    print(f"Is complete: {decoder.is_complete}")
    print(f"Is UR: {decoder.is_ur}")
    print(f"Percent complete: {decoder.get_percent_complete()}%")
    
    if decoder.is_complete:
        print("Decoding completed successfully!")
        if decoder.qr_type == QRType.XMR_TX_UNSIGNED_UR:
            tx = decoder.get_tx()
            if tx:
                print("Transaction data retrieved successfully!")
            else:
                print("Failed to get transaction data")
        return True
    else:
        print("Decoding not complete yet")
        return False

def test_multipart_ur():
    """Test multipart UR decoding with detailed logging"""
    print("\n=== Testing Multipart UR Decoding ===")
    
    # Create a decoder instance
    decoder = DecodeQR()
    
    # Simulate receiving multiple parts of a UR
    # These are simplified examples - real UR parts would be more complex
    part1 = "UR:XMR-TXUNSIGNED/1-3/LPADAOCFADFLDAXL"
    part2 = "UR:XMR-TXUNSIGNED/2-3/LPADAOCFADFLDAXL"
    part3 = "UR:XMR-TXUNSIGNED/3-3/LPADAOCFADFLDAXL"
    
    print("Adding part 1:")
    result1 = decoder.add_data(part1.encode())
    print(f"Result: {result1}")
    print(f"Percent complete: {decoder.get_percent_complete()}%")
    
    print("\nAdding part 2:")
    result2 = decoder.add_data(part2.encode())
    print(f"Result: {result2}")
    print(f"Percent complete: {decoder.get_percent_complete()}%")
    
    print("\nAdding part 3:")
    result3 = decoder.add_data(part3.encode())
    print(f"Result: {result3}")
    print(f"Percent complete: {decoder.get_percent_complete()}%")
    
    print(f"\nFinal state:")
    print(f"Is complete: {decoder.is_complete}")
    print(f"QR type: {decoder.qr_type}")

if __name__ == "__main__":
    # Example UR data for testing (this would be replaced with actual QR data)
    # This is just a placeholder to test the logging
    sample_ur = "UR:XMR-TXUNSIGNED/1-2/LPADAOCFADFLDAXL"
    
    print("Starting QR scan debug test...")
    test_ur_qr_data(sample_ur)
    test_multipart_ur()
    print("Test completed.")
