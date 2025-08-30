import re
import time
from collections import OrderedDict
from typing import List, Tuple, Optional, Dict, Any
from PIL import Image

from xmrsigner.models.decode_qr import DecodeQR
from xmrsigner.models.qr_type import QRType
from xmrsigner.hardware.camera import Camera
from xmrsigner.models.threads import BaseThread
from xmrsigner.models.base_decoder import DecodeQRStatus
from xmrsigner.helpers.ur2.ur_decoder import URDecoder
from xmrsigner.helpers.ur2.ur import UR
from xmrsigner.helpers.ur2 import cbor_lite as cbor

class LiveQRScanner:
    """
    Implements a live QR scanner that can handle animated QR codes (UR format) with progress tracking,
    following the Cake Wallet approach for fast QR changes.
    """
    
    def __init__(self, wordlist_language_code: str = "english"):
        self.wordlist_language_code = wordlist_language_code
        self.decoder = DecodeQR(wordlist_language_code=wordlist_language_code)
        self.ur_decoder = URDecoder()  # Dedicated UR decoder for progress tracking
        self.ur_parts = OrderedDict()  # Store unique UR parts by their index
        self.total_parts = None
        self.bytes_tag = None
        self.progress = 0.0
        self.is_complete = False
        self.last_scan_time = 0
        self.scan_cooldown = 0.05  # Minimum time between scans (50ms) for faster scanning
        self.last_qr_data = None
        self.scanned_parts = set()  # Track which parts we've already scanned
        
    def scan_frame(self, frame: Image) -> Tuple[bool, float, str]:
        """
        Scan a single frame for QR codes following the Cake Wallet approach.
        
        Returns:
            Tuple[bool, float, str]: (is_complete, progress, status_message)
        """
        current_time = time.time()
        if current_time - self.last_scan_time < self.scan_cooldown:
            return self.is_complete, self.progress, "Scanning..."
        
        self.last_scan_time = current_time
        
        # Extract QR data from frame
        qr_data = self._extract_qr_data(frame)
        if not qr_data:
            return self.is_complete, self.progress, "Scanning..."
            
        # Check if this is a UR format QR code
        qr_string = qr_data if isinstance(qr_data, str) else qr_data.decode('utf-8', errors='ignore')
        
        if qr_string.lower().startswith('ur:'):
            return self._handle_ur_qr(qr_string, qr_data)
        else:
            # Handle non-UR QR codes using the existing decoder
            status = self.decoder.add_data(qr_data)
            if status == DecodeQRStatus.COMPLETE:
                self.is_complete = True
                self.progress = 1.0
                return self.is_complete, self.progress, "Complete"
            elif status == DecodeQRStatus.INVALID:
                return self.is_complete, self.progress, "Invalid QR code"
                
        return self.is_complete, self.progress, "Processing..."
    
    def _extract_qr_data(self, frame: Image) -> Optional[str]:
        """
        Extract raw QR data from a frame.
        """
        # Use the same approach as the existing code
        try:
            data = DecodeQR.extract_qr_data(frame, is_binary=True)
            return data
        except Exception as e:
            return None
    
    def _handle_ur_qr(self, qr_string: str, raw_data: bytes) -> Tuple[bool, float, str]:
        """
        Handle UR format QR codes with progress tracking, following the Cake Wallet approach.
        
        Returns:
            Tuple[bool, float, str]: (is_complete, progress, status_message)
        """
        try:
            # Parse the UR structure to get part information
            part_info = self._parse_ur_part(qr_string)
            if not part_info:
                return self.is_complete, self.progress, "Invalid UR format"
                
            # Check if we've already scanned this part
            part_key = f"{part_info['index']}"
            if part_key in self.scanned_parts:
                # Already scanned this part, just update progress
                return self.is_complete, self.progress, self._get_progress_message()
                
            # Add this part to our scanned parts
            self.scanned_parts.add(part_key)
            
            # Update total parts if we haven't set it yet
            if self.total_parts is None:
                self.total_parts = part_info['total_parts']
                self.bytes_tag = part_info['bytes_tag']
                
            # Add the part to our UR decoder
            self.ur_decoder.receive_part(qr_string)
            
            # Update progress
            self.progress = self.ur_decoder.estimated_percent_complete()
            
            # Check if complete
            if self.ur_decoder.is_complete():
                self.is_complete = True
                return self.is_complete, self.progress, f"Complete {self.total_parts}/{self.total_parts}"
            else:
                # Return progress message
                scanned_count = len(self.scanned_parts)
                return self.is_complete, self.progress, f"Scanning... {scanned_count}/{self.total_parts}"
                
        except Exception as e:
            return self.is_complete, self.progress, f"Error: {str(e)}"
    
    def _parse_ur_part(self, ur_string: str) -> Optional[Dict[str, Any]]:
        """
        Parse a UR string to extract part information, following the Cake Wallet approach.
        
        Example UR string: ur:xmr-txunsigned/5-1/data
        Format: ur:BYTES_TAG/TOTAL_COUNT-INDEX/DATA_PAYLOAD
        
        Returns:
            Dict with part information or None if invalid
        """
        # UR format: ur:bytes-tag/total-index/data
        pattern = r'^ur:([^/]+)/(\d+)-(\d+)/(.+)$'
        match = re.match(pattern, ur_string.lower())
        
        if not match:
            # Try alternative format
            pattern2 = r'^ur:([^/]+)/(\d+)-(\d+)(/.+)?$'
            match = re.match(pattern2, ur_string.lower())
            if not match:
                return None
                
        bytes_tag = match.group(1)
        total_parts = int(match.group(2))
        index = int(match.group(3))
        
        return {
            'bytes_tag': bytes_tag,
            'total_parts': total_parts,
            'index': index
        }
    
    def _get_progress_message(self) -> str:
        """
        Get a formatted progress message.
        """
        if self.total_parts:
            scanned_count = len(self.scanned_parts)
            return f"Scanning... {scanned_count}/{self.total_parts}"
        else:
            return f"Scanning... {int(self.progress * 100)}%"
    
    def reset(self):
        """Reset the scanner state."""
        self.decoder = DecodeQR(wordlist_language_code=self.wordlist_language_code)
        self.ur_decoder = URDecoder()
        self.ur_parts.clear()
        self.scanned_parts.clear()
        self.total_parts = None
        self.bytes_tag = None
        self.progress = 0.0
        self.is_complete = False
        self.last_scan_time = 0
        self.last_qr_data = None
    
    def get_decoded_data(self):
        """
        Get the fully decoded data when scanning is complete.
        
        Returns:
            The decoded data or None if not complete
        """
        if not self.is_complete:
            return None
            
        # For UR formats, get the decoded data from the UR decoder
        try:
            if self.ur_decoder.is_complete():
                # Get the result UR
                result_ur = self.ur_decoder.result_message()
                
                # Extract the data based on the bytes tag
                if self.bytes_tag and 'txunsigned' in self.bytes_tag:
                    # Handle unsigned transaction
                    return self._decode_unsigned_transaction(result_ur.cbor)
                elif self.bytes_tag and 'output' in self.bytes_tag:
                    # Handle output data
                    return self._decode_output_data(result_ur.cbor)
                else:
                    # Generic decoding
                    return {
                        'type': 'ur',
                        'tag': self.bytes_tag,
                        'data': result_ur.cbor
                    }
        except Exception as e:
            return {'error': f'Failed to decode UR data: {str(e)}'}
            
        return None
    
    def _decode_unsigned_transaction(self, cbor_data: bytes):
        """
        Decode an unsigned transaction from CBOR data.
        """
        try:
            from xmrsigner.urtypes.xmr import XmrTxUnsigned
            tx = XmrTxUnsigned.from_cbor(cbor_data)
            return tx.data
        except Exception as e:
            return {'error': f'Failed to decode unsigned transaction: {str(e)}'}
    
    def _decode_output_data(self, cbor_data: bytes):
        """
        Decode output data from CBOR data.
        """
        try:
            from xmrsigner.urtypes.xmr import XmrOutput
            output = XmrOutput.from_cbor(cbor_data)
            return output.data
        except Exception as e:
            return {'error': f'Failed to decode output data: {str(e)}'}


class LiveQRScannerThread(BaseThread):
    """
    Thread for continuously scanning QR codes from camera frames, following the Cake Wallet approach.
    """
    
    def __init__(self, camera: Camera, scanner: LiveQRScanner, callback=None):
        self.camera = camera
        self.scanner = scanner
        self.callback = callback  # Callback function to report progress
        self.running = True
        super().__init__()
        
    def run(self):
        """Main scanning loop - continuously captures and processes frames."""
        while self.running and self.keep_running:
            try:
                # Capture frame from camera
                frame = self.camera.read_video_stream(as_image=True)
                if frame is not None:
                    # Scan the frame
                    is_complete, progress, status = self.scanner.scan_frame(frame)
                    
                    # Report progress via callback if provided
                    if self.callback:
                        self.callback(is_complete, progress, status)
                        
                    # If complete, stop scanning
                    if is_complete:
                        self.running = False
                        
                # Small delay to prevent excessive CPU usage but keep scanning fast
                time.sleep(0.01)
                
            except Exception as e:
                if self.callback:
                    self.callback(False, 0.0, f"Error: {str(e)}")
                time.sleep(0.1)
                
    def stop(self):
        """Stop the scanning thread."""
        self.running = False
        super().stop()


# Example usage:
"""
# Create scanner and camera
scanner = LiveQRScanner()
camera = Camera.get_instance()
camera.start_video_stream_mode(resolution=(480, 480), framerate=10)  # Higher framerate for faster scanning

# Define callback for progress updates
def progress_callback(is_complete, progress, status):
    print(f"Progress: {progress:.1%} - {status}")
    if is_complete:
        data = scanner.get_decoded_data()
        print(f"Decoded data: {data}")
        # Stop camera
        camera.stop_video_stream_mode()

# Start scanning thread
scanner_thread = LiveQRScannerThread(camera, scanner, progress_callback)
scanner_thread.start()

# To stop scanning manually:
# scanner_thread.stop()
# camera.stop_video_stream_mode()
"""