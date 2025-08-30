#!/usr/bin/env python3

"""
Advanced debug script for testing QR code scanning with detailed logging,
especially for QR codes with logos like Cake Wallet
"""

import sys
import os
from PIL import Image, ImageDraw
import numpy as np

# Add the src directory to the path so we can import xmrsigner modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from xmrsigner.models.decode_qr import DecodeQR
from pyzbar import pyzbar
from pyzbar.pyzbar import ZBarSymbol
import qrcode

def create_qr_with_logo(data, logo_size_ratio=0.2):
    """Create a QR code with a logo in the center for testing"""
    
    # Create QR code with high error correction
    qr = qrcode.QRCode(
        version=10,  # Larger QR code
        error_correction=qrcode.constants.ERROR_CORRECT_H,  # High error correction
        box_size=4,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    # Create image
    img = qr.make_image(fill_color="black", back_color="white")
    img = img.convert('RGB')
    
    # Calculate logo size (smaller than before)
    qr_size = min(img.size)
    logo_size = int(qr_size * logo_size_ratio)
    
    # Create a smaller, simpler logo
    logo = Image.new('RGB', (logo_size, logo_size), color='white')  # White logo
    draw = ImageDraw.Draw(logo)
    draw.rectangle([0, 0, logo_size-1, logo_size-1], outline='black')
    
    # Paste logo in center
    img_width, img_height = img.size
    logo_x = (img_width - logo_size) // 2
    logo_y = (img_height - logo_size) // 2
    img.paste(logo, (logo_x, logo_y))
    
    return img

def test_qr_with_logo_decoding():
    """Test decoding QR codes with logos"""
    print("=== Testing QR Code with Logo Decoding ===")
    
    # Test data (simplified for testing)
    test_data = "TEST_DATA_12345"
    
    try:
        # Create a QR code with logo
        print("Creating QR code with logo...")
        qr_img = create_qr_with_logo(test_data, logo_size_ratio=0.15)  # Smaller logo
        qr_img.save("test_qr_with_logo.png")
        print("QR code with logo saved as test_qr_with_logo.png")
        
        # Convert to numpy array for decoding
        np_img = np.array(qr_img)
        print(f"Image shape: {np_img.shape}")
        
        # Test decoding with different settings
        print("\nTesting decoding with default settings...")
        barcodes = pyzbar.decode(np_img, symbols=[ZBarSymbol.QRCODE], binary=True)
        print(f"Found {len(barcodes)} barcodes with default settings")
        
        if barcodes:
            decoded_data = barcodes[0].data.decode()
            print(f"Decoded data: {decoded_data}")
            print(f"Match: {decoded_data == test_data}")
        else:
            print("No barcodes found with default settings")
            
            # Try with different density settings
            print("\nTesting decoding with density=2...")
            barcodes = pyzbar.decode(np_img, symbols=[ZBarSymbol.QRCODE], binary=True, x_density=2, y_density=2)
            print(f"Found {len(barcodes)} barcodes with density=2")
            
            if barcodes:
                decoded_data = barcodes[0].data.decode()
                print(f"Decoded data: {decoded_data}")
                print(f"Match: {decoded_data == test_data}")
            else:
                print("No barcodes found with density=2")
                
                # Try with binary=False
                print("\nTesting decoding with binary=False...")
                barcodes = pyzbar.decode(np_img, symbols=[ZBarSymbol.QRCODE], binary=False)
                print(f"Found {len(barcodes)} barcodes with binary=False")
                
                if barcodes:
                    decoded_data = barcodes[0].data.decode()
                    print(f"Decoded data: {decoded_data}")
                    print(f"Match: {decoded_data == test_data}")
                else:
                    print("No barcodes found with binary=False")
                    
                    # Try with both density and binary=False
                    print("\nTesting decoding with density=2 and binary=False...")
                    barcodes = pyzbar.decode(np_img, symbols=[ZBarSymbol.QRCODE], binary=False, x_density=2, y_density=2)
                    print(f"Found {len(barcodes)} barcodes with density=2 and binary=False")
                    
                    if barcodes:
                        decoded_data = barcodes[0].data.decode()
                        print(f"Decoded data: {decoded_data}")
                        print(f"Match: {decoded_data == test_data}")
                    else:
                        print("No barcodes found with density=2 and binary=False")
        
    except Exception as e:
        print(f"Error during QR code testing: {e}")
        import traceback
        traceback.print_exc()

def test_existing_image(image_path):
    """Test decoding an existing image file"""
    print(f"\n=== Testing Existing Image: {image_path} ===")
    
    try:
        # Load image
        img = Image.open(image_path)
        print(f"Image size: {img.size}")
        print(f"Image mode: {img.mode}")
        
        # Convert to RGB if needed
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Convert to numpy array
        np_img = np.array(img)
        print(f"Numpy array shape: {np_img.shape}")
        
        # Try different decoding approaches
        approaches = [
            ("default", {}),
            ("density=2", {"x_density": 2, "y_density": 2}),
            ("density=3", {"x_density": 3, "y_density": 3}),
            ("binary=False", {"binary": False}),
            ("binary=False, density=2", {"binary": False, "x_density": 2, "y_density": 2}),
        ]
        
        for name, params in approaches:
            print(f"\nTesting with {name}...")
            try:
                barcodes = pyzbar.decode(np_img, symbols=[ZBarSymbol.QRCODE], **params)
                print(f"Found {len(barcodes)} barcodes")
                if barcodes:
                    for i, barcode in enumerate(barcodes):
                        print(f"  Barcode {i+1}: {barcode.data.decode()[:50]}...")
            except Exception as e:
                print(f"Error with {name}: {e}")
                
    except Exception as e:
        print(f"Error loading image: {e}")

if __name__ == "__main__":
    print("Starting advanced QR scan debug test...")
    
    # Test QR codes with logos
    test_qr_with_logo_decoding()
    
    # If you have a specific image you want to test, uncomment the following line
    # and provide the path to your image:
    # test_existing_image("path/to/your/cake_wallet_qr.png")
    
    print("\nTest completed.")