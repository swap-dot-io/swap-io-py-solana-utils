import base64
import hashlib

import base58
from solders.message import to_bytes_versioned
from solders.transaction import (Transaction as SoldersLegacyTransaction,
                                 VersionedTransaction as SoldersVersionedTransaction)

from .core import try_build_versioned_tx_from_bytes, try_build_legacy_tx_from_bytes

DEFAULT_ALGORITHM = "sha256"


def get_tx_message_hash(tx_object: SoldersLegacyTransaction | SoldersVersionedTransaction,
                        algorithm: str = DEFAULT_ALGORITHM) -> str:
    message_bytes = to_bytes_versioned(tx_object.message)  # we can use the function for both types of transactions
    hash_func = getattr(hashlib, algorithm, None)
    if hash_func is None:
        raise ValueError(f"Unsupported hash algorithm: {algorithm}")
    return hash_func(message_bytes).hexdigest()


def get_base64_tx_message_hash(base64_tx: str, algorithm: str = DEFAULT_ALGORITHM) -> str:
    try:
        raw_bytes = base64.b64decode(base64_tx, validate=True)
    except Exception as e:
        raise ValueError(f"Invalid base64: {e}")

    tx_object = (try_build_versioned_tx_from_bytes(raw_bytes, raise_on_error=False)
                 or try_build_legacy_tx_from_bytes(raw_bytes, raise_on_error=False))
    if tx_object:
        return get_tx_message_hash(tx_object, algorithm)

    raise ValueError(f"Invalid base64 transaction: {base64_tx}")


def get_base58_tx_message_hash(base58_tx: str, algorithm: str = DEFAULT_ALGORITHM) -> str:
    try:
        raw_bytes = base58.b58decode(base58_tx)
    except Exception as e:
        raise ValueError(f"Invalid base58: {e}")

    tx_object = (try_build_versioned_tx_from_bytes(raw_bytes, raise_on_error=False)
                 or try_build_legacy_tx_from_bytes(raw_bytes, raise_on_error=False))
    if tx_object:
        return get_tx_message_hash(tx_object, algorithm)

    raise ValueError(f"Invalid base58 transaction: {base58_tx}")
