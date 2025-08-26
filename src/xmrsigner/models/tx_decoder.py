import io
import varint

from monero.address import address

class TxDecoder:
    """
    A parser for the Monero `unsigned_txset` binary format. This format is not
    formally specified; the implementation is based on the Monero C++ source code.
    """
    def __init__(self, unsigned_tx_set_bytes: bytes):
        self.stream = io.BytesIO(unsigned_tx_set_bytes)

    def read_varint(self):
        return varint.decode_stream(self.stream)

    def read_uint64(self):
        return int.from_bytes(self.stream.read(8), 'little')

    def read_public_key(self):
        return self.stream.read(32)

    def read_address(self):
        spend_key = self.read_public_key()
        view_key = self.read_public_key()
        return address(spend_key, view_key)

    def _parse_tx_source_entry(self):
        # For now, just parse the amount and skip the rest of the complex structure
        # This is a simplification to get the total input amount for fee calculation.
        num_outputs = self.read_varint()
        for _ in range(num_outputs):
            self.read_varint()  # output index
            self.read_public_key() # public key
        self.read_varint() # real_output
        self.read_public_key() # real_out_tx_key
        num_additional_tx_keys = self.read_varint()
        for _ in range(num_additional_tx_keys):
            self.read_public_key()
        self.read_varint() # real_output_in_tx_index
        amount = self.read_uint64()
        self.read(1) # rct bool
        self.read(32) # mask
        return {"amount": amount}

    def _parse_tx_destination_entry(self):
        amount = self.read_uint64()
        addr = self.read_address()
        self.read(1) # is_subaddress
        return {"amount": amount, "address": addr}

    def _parse_tx_construction_data(self):
        # 1. Parse sources (inputs)
        num_sources = self.read_varint()
        sources = []
        for _ in range(num_sources):
            sources.append(self._parse_tx_source_entry())
        total_in = sum(s['amount'] for s in sources)

        # 2. Parse change_dts (we can ignore this if we parse splitted_dsts)
        self._parse_tx_destination_entry()

        # 3. Parse splitted_dsts (final outputs)
        num_splitted_dsts = self.read_varint()
        destinations = []
        for _ in range(num_splitted_dsts):
            destinations.append(self._parse_tx_destination_entry())
        total_out = sum(d['amount'] for d in destinations)

        # 4. Skip selected_transfers
        num_selected_transfers = self.read_varint()
        for _ in range(num_selected_transfers):
            self.read_varint()

        # 5. Skip extra
        extra_len = self.read_varint()
        self.stream.read(extra_len)

        # 6. Parse unlock_time
        unlock_time = self.read_uint64()

        # 7. Skip use_rct and rct_config
        self.stream.read(1) # use_rct
        self.stream.read(1) # rct_config (simplification, likely larger)

        # 8. Calculate fee
        fee = total_in - total_out

        return {
            "recipients": destinations,
            "fee": fee,
            "unlock_time": unlock_time,
        }

    def parse(self):
        magic_string = self.stream.read(len(b"Monero unsigned tx set"))
        if magic_string != b"Monero unsigned tx set":
            raise ValueError("Invalid magic string. This is not a Monero unsigned tx set file.")
        
        version = self.stream.read(1)

        # Parse the top-level unsigned_tx_set object
        # It contains txes (vector) and transfers (container)

        # 1. Parse txes vector
        num_txes = self.read_varint()
        if num_txes != 1:
            # For now, we only support unsigned_tx_set with a single transaction.
            raise NotImplementedError(f"Expected 1 transaction, but found {num_txes}")

        tx_data = self._parse_tx_construction_data()

        # We can skip parsing the 'transfers' container as we have what we need.

        self.recipients = tx_data['recipients']
        self.fee = tx_data['fee']
        self.unlock_time = tx_data['unlock_time']

        return {
            "recipients": self.recipients,
            "fee": self.fee,
            "unlock_time": self.unlock_time,
        }
