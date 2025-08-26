from dataclasses import dataclass
from PIL import Image, ImageDraw
from xmrsigner.gui.components import (
    XmrAmount,
    FormattedAddress,
    GUIConstants,
    Fonts,
    TextArea,
)
from xmrsigner.gui.screens.screen import ButtonListScreen
from typing import List
from monero.address import Address


@dataclass
class TxDetailsScreen(ButtonListScreen):
    """
    Displays detailed transaction information including inputs, outputs, fees, and recipients.
    """
    title: str = "Transaction Details"
    amount_in: int = 0
    amount_out: int = 0
    fee: int = 0
    recipients: List[tuple] = None  # List of (address, amount) tuples
    change_address: str = None
    change_amount: int = 0
    unlock_time: int = 0
    
    def __post_init__(self):
        self.is_bottom_list = True
        self.button_data = ["Sign Transaction"]
        
        if self.recipients is None:
            self.recipients = []
            
        super().__post_init__()
        
        # Start rendering the transaction details
        screen_y = self.top_nav.height + GUIConstants.COMPONENT_PADDING
        
        # Display total input amount
        self.components.append(XmrAmount(
            total_atomic_units=self.amount_in,
            screen_y=screen_y,
            font_size=18
        ))
        screen_y += self.components[-1].height + GUIConstants.COMPONENT_PADDING
        
        # Display fee
        self.components.append(XmrAmount(
            total_atomic_units=self.fee,
            screen_y=screen_y,
            font_size=14
        ))
        screen_y += self.components[-1].height + GUIConstants.COMPONENT_PADDING
        
        # Display recipients
        if self.recipients:
            for address, amount in self.recipients:
                # Amount
                self.components.append(XmrAmount(
                    total_atomic_units=amount,
                    screen_y=screen_y,
                    font_size=14
                ))
                screen_y += self.components[-1].height + GUIConstants.COMPONENT_PADDING // 2
                
                # Address
                self.components.append(FormattedAddress(
                    screen_y=screen_y,
                    address=address,
                    max_lines=2,
                    font_size=12
                ))
                screen_y += self.components[-1].height + GUIConstants.COMPONENT_PADDING
        
        # Display change if present
        if self.change_amount > 0 and self.change_address:
            # Change amount
            self.components.append(XmrAmount(
                total_atomic_units=self.change_amount,
                screen_y=screen_y,
                font_size=14
            ))
            screen_y += self.components[-1].height + GUIConstants.COMPONENT_PADDING // 2
            
            # Change address
            self.components.append(FormattedAddress(
                screen_y=screen_y,
                address=self.change_address,
                max_lines=2,
                font_size=12
            ))
            screen_y += self.components[-1].height + GUIConstants.COMPONENT_PADDING
            
        # Display unlock time if set
        if self.unlock_time > 0:
            self.components.append(TextArea(
                text=f"Unlock Time: {self.unlock_time}",
                screen_y=screen_y,
                font_size=12
            ))