#!/usr/bin/env python3

"""
Test script for QR code decoding with logos using OpenCV
"""

import sys
import os
from PIL import Image, ImageDraw
import numpy as np
import cv2

# Add the src directory to the path so we can import xmrsigner modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def create_qr_with_logo_opencv(data, logo_size_ratio=0.2):
    """Create a QR code with a logo using OpenCV"""
    # Create QR code using qrcode library
    import qrcode
    
    # Create QR code with high error correction
    qr = qrcode.QRCode(
        version=10,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=4,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    # Create image
    img = qr.make_image(fill_color="black", back_color="white")
    img = img.convert('RGB')
    
    # Calculate logo size
    qr_size = min(img.size)
    logo_size = int(qr_size * logo_size_ratio)
    
    # Create a logo
    logo = Image.new('RGB', (logo_size, logo_size), color='red')
    draw = ImageDraw.Draw(logo)
    draw.rectangle([0, 0, logo_size-1, logo_size-1], outline='black')
    
    # Paste logo in center
    img_width, img_height = img.size
    logo_x = (img_width - logo_size) // 2
    logo_y = (img_height - logo_size) // 2
    img.paste(logo, (logo_x, logo_y))
    
    return img

def test_opencv_qr_decoding():
    """Test QR decoding with OpenCV"""
    print("=== Testing OpenCV QR Decoding ===")
    
    # Test data
    test_data = "UR:XMR-TXUNSIGNED/1-2/LPADAOCFADFLDAXL"
    
    try:
        # Create a QR code with logo
        print("Creating QR code with logo...")
        qr_img = create_qr_with_logo_opencv(test_data, logo_size_ratio=0.15)
        qr_img.save("test_opencv_qr.png")
        print("QR code with logo saved as test_opencv_qr.png")
        
        # Convert to OpenCV format
        cv_image = np.array(qr_img)
        cv_image = cv2.cvtColor(cv_image, cv2.COLOR_RGB2BGR)
        print(f"OpenCV image shape: {cv_image.shape}")
        
        # Create QR detector
        qr_detector = cv2.QRCodeDetector()
        
        # Detect and decode
        print("Attempting to decode with OpenCV...")
        data, bbox, straight_qrcode = qr_detector.detectAndDecode(cv_image)
        
        if data:
            print(f"SUCCESS: OpenCV decoded data: {data}")
            print(f"Match: {data == test_data}")
        else:
            print("FAILED: OpenCV could not decode the QR code")
            
        # Also try with pyzbar for comparison
        print("\nTesting with pyzbar for comparison...")
        from pyzbar import pyzbar
        from pyzbar.pyzbar import ZBarSymbol
        
        # Convert back to RGB for pyzbar
        rgb_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
        
        barcodes = pyzbar.decode(rgb_image, symbols=[ZBarSymbol.QRCODE])
        print(f"pyzbar found {len(barcodes)} barcodes")
        
        if barcodes:
            pyzbar_data = barcodes[0].data.decode()
            print(f"pyzbar decoded data: {pyzbar_data}")
            print(f"Match: {pyzbar_data == test_data}")
        else:
            print("pyzbar could not decode the QR code")
            
    except ImportError as e:
        print(f"Import error: {e}")
        print("Make sure you have installed: pip install opencv-python qrcode")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

def test_existing_image(image_path):
    """Test decoding an existing image file with both OpenCV and pyzbar"""
    print(f"\n=== Testing Existing Image: {image_path} ===")
    
    if not os.path.exists(image_path):
        print(f"ERROR: File not found: {image_path}")
        return
    
    try:
        # Load image with PIL
        pil_img = Image.open(image_path)
        print(f"PIL Image size: {pil_img.size}, mode: {pil_img.mode}")
        
        # Convert to RGB if needed
        if pil_img.mode != 'RGB':
            pil_img = pil_img.convert('RGB')
        
        # Test with pyzbar
        print("\nTesting with pyzbar...")
        from pyzbar import pyzbar
        from pyzbar.pyzbar import ZBarSymbol
        
        # Convert to numpy array
        np_img = np.array(pil_img)
        
        # Try different pyzbar approaches
        approaches = [
            ("default", {"symbols": [ZBarSymbol.QRCODE]}),
            ("binary=False", {"symbols": [ZBarSymbol.QRCODE], "binary": False}),
            ("no symbols", {}),
        ]
        
        for name, params in approaches:
            print(f"  {name}...", end=" ")
            try:
                barcodes = pyzbar.decode(np_img, **params)
                print(f"Found {len(barcodes)} barcodes")
                if barcodes:
                    for i, barcode in enumerate(barcodes):
                        data = barcode.data.decode('utf-8', errors='replace')
                        print(f"    Data: {data[:100]}{'...' if len(data) > 100 else ''}")
            except Exception as e:
                print(f"Error: {e}")
        
        # Test with OpenCV
        print("\nTesting with OpenCV...")
        import cv2
        
        # Convert PIL to OpenCV format
        cv_image = np.array(pil_img)
        cv_image = cv2.cvtColor(cv_image, cv2.COLOR_RGB2BGR)
        
        # Create QR detector
        qr_detector = cv2.QRCodeDetector()
        
        # Detect and decode
        data, bbox, straight_qrcode = qr_detector.detectAndDecode(cv_image)
        
        if data:
            print(f"SUCCESS: OpenCV decoded data: {data}")
        else:
            print("OpenCV could not decode the QR code")
            # Try detection only
            retval, points = qr_detector.detect(cv_image)
            if retval:
                print(f"OpenCV detected QR code at points: {points}")
            else:
                print("OpenCV could not detect QR code")
                
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("QR Code Decoding Test with Logos")
    print("=" * 40)
    
    # Test with generated QR code
    test_opencv_qr_decoding()
    
    # If command line arguments are provided, treat them as image paths
    if len(sys.argv) > 1:
        for image_path in sys.argv[1:]:
            test_existing_image(image_path)
    else:
        print("\nUsage: python test_qr_decoding.py <image1.png> <image2.png> ...")
        print("This will test both pyzbar and OpenCV decoding approaches")