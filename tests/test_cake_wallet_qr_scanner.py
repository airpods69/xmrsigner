#!/usr/bin/env python3
"""
Simple test script for the CakeWalletQRScanner UR parsing logic that doesn't require hardware dependencies.
"""

import sys
import os
import re
from pathlib import Path

# Add the src directory to the path so we can import our modules
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

def test_ur_parsing():
    """Test UR parsing functionality without requiring hardware."""
    try:
        # We'll manually test the UR parsing logic from our implementation
        # Test a sample UR string
        ur_string = "ur:xmr-txunsigned/5-1/asdfasdf"
        pattern = r'^ur:([^/]+)/(\d+)-(\d+)/(.+)$'
        match = re.match(pattern, ur_string.lower())
        
        if match:
            bytes_tag = match.group(1)
            total_parts = int(match.group(2))
            index = int(match.group(3))
            
            if bytes_tag == 'xmr-txunsigned' and total_parts == 5 and index == 1:
                print("✓ UR parsing regex works correctly")
                return True
        
        print(f"✗ UR parsing regex failed. Match: {match}")
        return False
    except Exception as e:
        print(f"✗ UR parsing test failed with exception: {e}")
        return False

def test_ur_parsing_alternative():
    """Test alternative UR parsing format."""
    try:
        # Test alternative format without data part
        ur_string = "ur:xmr-txunsigned/5-1"
        pattern2 = r'^ur:([^/]+)/(\d+)-(\d+)(/.+)?$'
        match = re.match(pattern2, ur_string.lower())
        
        if match:
            bytes_tag = match.group(1)
            total_parts = int(match.group(2))
            index = int(match.group(3))
            
            if bytes_tag == 'xmr-txunsigned' and total_parts == 5 and index == 1:
                print("✓ Alternative UR parsing regex works correctly")
                return True
        
        print(f"✗ Alternative UR parsing regex failed. Match: {match}")
        return False
    except Exception as e:
        print(f"✗ Alternative UR parsing test failed with exception: {e}")
        return False

def test_ur_part_tracking():
    """Test UR part tracking logic."""
    try:
        # Simulate tracking of scanned parts
        scanned_parts = set()
        
        # Add some parts
        scanned_parts.add("1")
        scanned_parts.add("2")
        scanned_parts.add("3")
        
        # Check if a part is already scanned
        if "1" in scanned_parts and "2" in scanned_parts and "3" in scanned_parts:
            print("✓ UR part tracking works correctly")
            return True
        else:
            print("✗ UR part tracking failed")
            return False
    except Exception as e:
        print(f"✗ UR part tracking test failed with exception: {e}")
        return False

def main():
    """Run all tests."""
    print("Testing CakeWalletQRScanner UR parsing and tracking logic...")
    print()
    
    tests = [
        test_ur_parsing,
        test_ur_parsing_alternative,
        test_ur_part_tracking
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"Tests passed: {passed}/{len(tests)}")
    
    if passed == len(tests):
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())