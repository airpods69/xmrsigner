#!/usr/bin/env python3

"""
Debug script to capture and analyze frames from XmrSigner's camera
"""

import sys
import os
import cv2
import numpy as np
from PIL import Image

# Add the src directory to the path so we can import xmrsigner modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def analyze_frame(frame_path):
    """Analyze a captured frame to see why QR decoding might be failing"""
    print(f"\n=== Analyzing Frame: {frame_path} ===")
    
    if not os.path.exists(frame_path):
        print(f"ERROR: File not found: {frame_path}")
        return
    
    try:
        # Load with PIL (as XmrSigner does)
        pil_img = Image.open(frame_path)
        print(f"PIL Image - Size: {pil_img.size}, Mode: {pil_img.mode}")
        
        # Convert to numpy array (as XmrSigner does)
        np_img = np.array(pil_img)
        print(f"Numpy array shape: {np_img.shape}")
        print(f"Data type: {np_img.dtype}")
        print(f"Value range: {np_img.min()} to {np_img.max()}")
        
        # Test with pyzbar (as XmrSigner does)
        print("\nTesting with pyzbar...")
        from pyzbar import pyzbar
        from pyzbar.pyzbar import ZBarSymbol
        
        # Try different approaches
        approaches = [
            ("default", {"symbols": [ZBarSymbol.QRCODE], "binary": True}),
            ("density=2", {"symbols": [ZBarSymbol.QRCODE], "binary": True, "x_density": 2, "y_density": 2}),
            ("binary=False", {"symbols": [ZBarSymbol.QRCODE], "binary": False}),
            ("no symbols", {"binary": True}),
        ]
        
        found_qr = False
        for name, params in approaches:
            print(f"  {name}...", end=" ")
            try:
                barcodes = pyzbar.decode(np_img, **params)
                print(f"Found {len(barcodes)} barcodes")
                if barcodes:
                    found_qr = True
                    for i, barcode in enumerate(barcodes):
                        data = barcode.data.decode('utf-8', errors='replace')
                        print(f"    Data: {data[:100]}{'...' if len(data) > 100 else ''}")
            except Exception as e:
                print(f"Error: {e}")
        
        if not found_qr:
            print("  No QR codes found with pyzbar")
        
        # Test with OpenCV
        print("\nTesting with OpenCV...")
        try:
            # Convert PIL to OpenCV format
            if pil_img.mode != 'RGB':
                pil_img = pil_img.convert('RGB')
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
                    # Draw bounding box for visualization
                    if points is not None:
                        points = np.int32(points)
                        for i in range(len(points)):
                            pt1 = tuple(points[i][0])
                            pt2 = tuple(points[(i + 1) % len(points)][0])
                            cv_image = cv2.line(cv_image, pt1, pt2, (0, 255, 0), 3)
                        # Save annotated image
                        annotated_path = frame_path.replace('.png', '_annotated.png')
                        cv2.imwrite(annotated_path, cv_image)
                        print(f"Annotated image saved to: {annotated_path}")
                else:
                    print("OpenCV could not detect QR code")
        except Exception as e:
            print(f"Error with OpenCV: {e}")
            import traceback
            traceback.print_exc()
            
    except Exception as e:
        print(f"Error analyzing frame: {e}")
        import traceback
        traceback.print_exc()

def batch_analyze_frames(directory):
    """Analyze all PNG frames in a directory"""
    print(f"\n=== Batch Analyzing Frames in: {directory} ===")
    
    if not os.path.exists(directory):
        print(f"ERROR: Directory not found: {directory}")
        return
    
    # Find all PNG files
    png_files = [f for f in os.listdir(directory) if f.endswith('.png')]
    png_files.sort()
    
    print(f"Found {len(png_files)} PNG files")
    
    for png_file in png_files:
        frame_path = os.path.join(directory, png_file)
        analyze_frame(frame_path)
        print("-" * 50)

if __name__ == "__main__":
    print("XmrSigner Frame Analysis Tool")
    print("=" * 40)
    
    if len(sys.argv) > 1:
        for path in sys.argv[1:]:
            if os.path.isdir(path):
                batch_analyze_frames(path)
            else:
                analyze_frame(path)
    else:
        print("Usage:")
        print("  python analyze_frames.py <frame.png>          # Analyze a single frame")
        print("  python analyze_frames.py <directory>          # Analyze all frames in directory")
        print("\nThis tool will help diagnose why QR codes might not be decoding properly")
        print("by testing both pyzbar (used by XmrSigner) and OpenCV (more robust) approaches.")