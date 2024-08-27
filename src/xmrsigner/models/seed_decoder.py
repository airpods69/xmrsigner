from xmrsigner.models.base_decoder import BaseSingleFrameQrDecoder, DecodeQRStatus
from xmrsigner.models.qr_type import QRType
from xmrsigner.models.seed import Seed
from xmrsigner.helpers.seedwordindex import SeedWordIndex
from xmrsigner.helpers.shortseed import ShortSeed
from xmrsigner.helpers.compactseed import CompactSeed
from monero.seed import Seed as MoneroSeed
from xmrsigner.models.polyseed import PolyseedSeed

from typing import List


class SeedQrDecoder(BaseSingleFrameQrDecoder):
    """
        Decodes single frame representing a seed.
        Supports XmrSigner SeedQR numeric (wordlist indices) representation of a seed.
        Supports XmrSigner CompactSeedQR entropy byte representation of a seed.
        Supports mnemonic seed phrase string data.
    """
    def __init__(self, wordlist_language_code):
        super().__init__()
        self.seed_phrase = []
        self.wordlist_language_code = wordlist_language_code

    def add(self, segment, qr_type=QRType.SEED__SEEDQR):
        # `segment` data will either be bytes or str, depending on the qr_type
        if qr_type == QRType.SEED__SEEDQR:
            print('SeedQrDecoder.add(): SEED__SEEDQR')
            try:
                self.seed_phrase = []
                num_words = int(len(segment) / 4)
                # Parse 12, 13, 16, 24 or 25-word QR code
                print(f'num_words: {num_words}')
                if num_words not in (12, 13, 16, 24, 25):
                    return DecodeQRStatus.INVALID
                wordlist = PolyseedSeed.get_wordlist(self.wordlist_language_code) if num_words == 16 else Seed.get_wordlist(self.wordlist_language_code)
                words = SeedWordIndex(wordlist).from_indices_string(segment)
                self.seed_phrase = MoneroSeed(MoneroSeed(' '.join(words)).hex).phrase.split() if len(words) in (12, 24) else words  # if there are only 12/24 words the checksum word is missing and we add it
                if not self.is_validphrase_word_count():
                    return DecodeQRStatus.INVALID
                self.complete = True
                self.collected_segments = 1
                return DecodeQRStatus.COMPLETE
            except Exception as e:
                print(f'SeedQrDecoder.add(): SEED__SEEDQR: {e}')
                return DecodeQRStatus.INVALID

        if qr_type == QRType.SEED__COMPACTSEEDQR:
            print('SeedQrDecoder.add(): SEED__COMPACTSEEDQR')
            try:
                word_count = CompactSeed.length(segment)
                if word_count in (12, 24):  # Monero seed
                    self.seed_phrase = MoneroSeed(MoneroSeed(' '.join(CompactSeed(Seed.get_wordlist(self.wordlist_language_code)).words(segment))).hex).phrase.split()  # convert direct to 13, 25 words
                    self.complete = True
                    self.collected_segments = 1
                    return DecodeQRStatus.COMPLETE
                if wordcount == 16:  # Polyseed
                    self.seed_phrase = CompactSeed(PolyseedSeed.get_wordlist(self.wordlist_language_code)).words(segment)
                    self.complete = True
                    self.collected_segments = 1
                    return DecodeQRStatus.COMPLETE
                return DecodeQRStatus.INVALID
            except Exception as e:
                logger.exception(repr(e))
                return DecodeQRStatus.INVALID

        elif qr_type == QRType.SEED__MNEMONIC:
            print('SeedQrDecoder.add(): SEED__MNEMONIC')
            try:
                seed_phrase_list = self.seed_phrase = segment.strip().split(' ')

                if len(seed_phrase_list) in (12, 13, 24, 25):  # Monero seed phrase
                    self.seed_phrase = MoneroSeed(MoneroSeed(' '.join(seed_phrase_list)).hex).phrase.split()
                if len(seed_phrase_list) == 16:  # polyseed
                    self.seed_phrase = PolyseedSeed(seed_phrase_list, passphrase='', wordlist_language_code=self.wordlist_language_code).mnemonic_list
                # self.seed_phrase = seed.mnemonic_list
                if self.is_validphrase_word_count():
                    self.complete = True
                    self.collected_segments = 1
                    return DecodeQRStatus.COMPLETE
                return DecodeQRStatus.INVALID
            except Exception as e:
                return DecodeQRStatus.INVALID

        elif qr_type == QRType.SEED__FOUR_LETTER_MNEMONIC:
            print('SeedQrDecoder.add(): SEED__FOUR_LETTER_MNEMONIC')
            try:
                seed_phrase_list = segment.strip().split(' ')
                if len(seed_phrase_list) in (12, 13, 24, 25):
                    words = ShortSeed(Seed.get_wordlist(self.wordlist_language_code)).expand(seed_phrase_list)
                    seed = Seed(
                        MoneroSeed(
                            MoneroSeed(' '.join(
                                ShortSeed(Seed.get_wordlist(self.wordlist_language_code)).expand(seed_phrase_list)
                            )).hex
                        ).phrase.split(),
                        passphrase="",
                        wordlist_language_code=self.wordlist_language_code
                    )
                if len(seed.mnemonic_list) == 16:
                    seed = PolyseedSeed(
                        ShortSeed(PolyseedSeed.get_wordlist(self.wordlist_language_code)).expand(seed_phrase_list),
                        passphrase='',
                        wordlist_language_code=self.wordlist_language_code
                    )
                if not seed:
                    # seed is not valid, return invalid
                    return DecodeQRStatus.INVALID
                self.seed_phrase = words
                if not self.is_validphrase_word_count():
                        return DecodeQRStatus.INVALID
                self.complete = True
                self.collected_segments = 1
                return DecodeQRStatus.COMPLETE
            except Exception as e:
                print(f'SeedQrDecoder.add(): {e}')
                return DecodeQRStatus.INVALID
            print(f'SeedQrDecoder.add(): after try block')
        print(f'SeedQrDecoder.add(): end')
        return DecodeQRStatus.INVALID

    def get_seed_phrase(self) -> List[str]:
        return self.seed_phrase if self.complete else []

    def is_validphrase_word_count(self) -> bool:
        return len(self.seed_phrase) in (13, 16, 25)
