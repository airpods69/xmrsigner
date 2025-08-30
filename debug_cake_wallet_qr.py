#!/usr/bin/env python3

"""
Comprehensive debug script for testing QR code scanning with detailed logging,
specifically for troubleshooting Cake Wallet multipart QR codes
"""

import sys
import os
from PIL import Image
import numpy as np

# Add the src directory to the path so we can import xmrsigner modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from xmrsigner.models.decode_qr import DecodeQR
from xmrsigner.models.qr_type import QRType
from pyzbar import pyzbar
from pyzbar.pyzbar import ZBarSymbol

def debug_image_decoding(image_path):
    \"\"\"Debug decoding of a specific image file\"\"\"
    print(f\"\\n=== Debugging Image: {image_path} ===\")
    
    if not os.path.exists(image_path):
        print(f\"ERROR: File not found: {image_path}\")
        return
    
    try:
        # Load image
        img = Image.open(image_path)
        print(f\"Image size: {img.size}\")
        print(f\"Image mode: {img.mode}\")
        
        # Convert to RGB if needed
        if img.mode != 'RGB':
            img = img.convert('RGB')
            print(f\"Converted to RGB mode\")
        
        # Convert to numpy array
        np_img = np.array(img)
        print(f\"Numpy array shape: {np_img.shape}\")
        
        # Show image info
        print(f\"Image data range: {np_img.min()} to {np_img.max()}\")
        print(f\"Image data type: {np_img.dtype}\")
        
        # Try different decoding approaches
        approaches = [
            (\"default\", {\"symbols\": [ZBarSymbol.QRCODE], \"binary\": True}),
            (\"density=2\", {\"symbols\": [ZBarSymbol.QRCODE], \"binary\": True, \"x_density\": 2, \"y_density\": 2}),
            (\"density=3\", {\"symbols\": [ZBarSymbol.QRCODE], \"binary\": True, \"x_density\": 3, \"y_density\": 3}),
            (\"binary=False\", {\"symbols\": [ZBarSymbol.QRCODE], \"binary\": False}),
            (\"binary=False, density=2\", {\"symbols\": [ZBarSymbol.QRCODE], \"binary\": False, \"x_density\": 2, \"y_density\": 2}),
            (\"no symbols\", {\"binary\": True}),
        ]
        
        print(\"\\nTrying different decoding approaches:\")
        found_qr = False
        for name, params in approaches:
            print(f\"  {name}...\", end=\" \")
            try:
                barcodes = pyzbar.decode(np_img, **params)
                print(f\"Found {len(barcodes)} barcodes\")
                if barcodes:
                    found_qr = True
                    for i, barcode in enumerate(barcodes):
                        data = barcode.data.decode('utf-8', errors='replace')
                        print(f\"    Barcode {i+1}: {data[:100]}{'...' if len(data) > 100 else ''}\")
                        
                        # Try to detect QR type
                        qr_type = DecodeQR.detect_segment_type(data)
                        print(f\"    Detected QR type: {qr_type}\")
            except Exception as e:
                print(f\"Error: {e}\")
        
        if not found_qr:
            print(\"  No QR codes found with any approach\")
            
    except Exception as e:
        print(f\"Error loading/processing image: {e}\")
        import traceback
        traceback.print_exc()

def debug_ur_decoding(qr_data_list):
    \"\"\"Debug UR decoding of multipart QR data\"\"\"
    print(f\"\\n=== Debugging UR Decoding ===\")
    print(f\"Processing {len(qr_data_list)} QR code parts\")
    
    # Create a decoder instance
    decoder = DecodeQR()
    
    # Process each part
    for i, qr_data in enumerate(qr_data_list):
        print(f\"\\nProcessing part {i+1}:\")
        print(f\"  Data: {qr_data[:100]}{'...' if len(qr_data) > 100 else ''}\")
        
        # Add the data
        result = decoder.add_data(qr_data.encode() if isinstance(qr_data, str) else qr_data)
        
        print(f\"  Decoder result: {result}\")
        print(f\"  QR type: {decoder.qr_type}\")
        print(f\"  Is complete: {decoder.is_complete}\")
        print(f\"  Is UR: {decoder.is_ur}\")
        print(f\"  Percent complete: {decoder.get_percent_complete()}%\")
        
        if decoder.is_complete:
            print(\"  Decoding completed successfully!\")
            if decoder.qr_type == QRType.XMR_TX_UNSIGNED_UR:
                try:
                    tx = decoder.get_tx()
                    if tx:
                        print(\"  Transaction data retrieved successfully!\")
                    else:
                        print(\"  Failed to get transaction data\")
                except Exception as e:
                    print(f\"  Error getting transaction data: {e}\")
            break
        else:
            print(f\"  Decoding not complete yet ({decoder.get_percent_complete()}% complete)\")

def main():
    print(\"XmrSigner QR Code Debug Tool\")
    print(\"=\" * 40)
    
    # If command line arguments are provided, treat them as image paths
    if len(sys.argv) > 1:
        for image_path in sys.argv[1:]:
            debug_image_decoding(image_path)
    else:
        print(\"Usage: python debug_cake_wallet_qr.py <image1.png> <image2.png> ...\")
        print(\"Or import this script and use the debug functions directly\")
        print(\"\\nExample usage:\")
        print(\"# To debug image decoding:\")
        print(\"# debug_image_decoding('path/to/cake_wallet_qr.png')\")
        print(\"\\n# To debug UR decoding with actual QR data:\")
        print(\"# debug_ur_decoding(['UR:XMR-TXUNSIGNED/1-3/...', 'UR:XMR-TXUNSIGNED/2-3/...', 'UR:XMR-TXUNSIGNED/3-3/...'])\")

if __name__ == \"__main__\":
    main()