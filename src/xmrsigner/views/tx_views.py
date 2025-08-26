from xmrsigner.views.view import View, Destination
from xmrsigner.gui.screens.tx_screens import TxDetailsScreen
from xmrsigner.helpers.monero import TxDescription
from xmrsigner.gui.screens.screen import RET_CODE__BACK_BUTTON


class TxDetailsView(View):
    """
    View to display detailed transaction information.
    """
    
    def run(self):
        # Get the transaction description from the controller
        tx_description: TxDescription = self.controller.tx_description
        
        if not tx_description:
            # This shouldn't happen, but let's handle it gracefully
            from xmrsigner.views.view import ErrorView
            return Destination(ErrorView, view_args={
                "title": "Error",
                "status_headline": "No Transaction",
                "text": "No transaction data found.",
                "button_text": "Back to Menu"
            })
        
        # Extract transaction details
        amount_in = int(tx_description.amount_in)
        amount_out = int(tx_description.amount_out)
        fee = int(tx_description.fee)
        
        # Get recipients
        recipients = []
        for recipient in tx_description.recipients:
            recipients.append((str(recipient.address), int(recipient.amount)))
        
        # Get change information
        change_address = str(tx_description.change_addresses[0]) if tx_description.change_addresses else None
        change_amount = int(tx_description.change_amount)
        
        # Get unlock time
        unlock_time = tx_description.details[0].unlock_time if tx_description.details else 0
        
        # Display the transaction details screen
        selected_menu_num = self.run_screen(
            TxDetailsScreen,
            amount_in=amount_in,
            amount_out=amount_out,
            fee=fee,
            recipients=recipients,
            change_address=change_address,
            change_amount=change_amount,
            unlock_time=unlock_time
        )
        
        if selected_menu_num == RET_CODE__BACK_BUTTON:
            return Destination(BackStackView)
            
        # If user chooses to sign, proceed to the signing view
        return Destination(SignTxView)


from xmrsigner.views.view import BackStackView
from xmrsigner.views.monero_views import SignedQRDisplayView


class SignTxView(View):
    """
    View to handle transaction signing.
    """
    
    def run(self):
        # The signing process is already implemented in SignedQRDisplayView
        # We'll just redirect to it
        return Destination(SignedQRDisplayView)