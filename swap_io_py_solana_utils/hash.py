import base64
import hashlib

import base58
from solders.message import Message
from solders.pubkey import Pubkey
from solders.compute_budget import ID as COMPUTE_BUDGET_ID
from solders.transaction import (Transaction as SoldersLegacyTransaction,
                                 VersionedTransaction as SoldersVersionedTransaction)

from .core import try_build_versioned_tx_from_bytes, try_build_legacy_tx_from_bytes

DEFAULT_ALGORITHM = "sha256"
LIGHTHOUSE_PROGRAM_ID = Pubkey.from_string("L2TExMFKdjpN9kozasaurPirfHy9P8sbXoAN1qA3S95")
SWAP_HELPER_PROGRAM_ID = Pubkey.from_string("7wuFcHkbVckS6nMqZ5pg6ykmw5uWTqzvqK1gdb8xGdp4")

DEFAULT_IGNORE_PROGRAMS = [
    COMPUTE_BUDGET_ID,
    LIGHTHOUSE_PROGRAM_ID,
    SWAP_HELPER_PROGRAM_ID,
]


def _serialize_message(message: Message) -> bytes:
    """Manually serialize transaction message components."""
    result = bytearray()

    # Prepare account keys and build ignore index map
    account_keys = list(message.account_keys)
    ignore_indices = set()

    for i, key in enumerate(account_keys):
        if key in DEFAULT_IGNORE_PROGRAMS:
            ignore_indices.add(i)

    # Filter out ignored programs from account keys
    account_keys = [key for key in account_keys if key not in DEFAULT_IGNORE_PROGRAMS]
    # Sorted account keys
    sorted_keys = sorted(account_keys, key=lambda x: bytes(x))

    for key in sorted_keys:
        result.extend(bytes(key))

    # Instructions data only (skip instructions from ignored programs)
    for ix in message.instructions:
        # Skip if instruction's program is in ignore list
        if ix.program_id_index in ignore_indices:
            continue
        # Skip if any of instruction's accounts reference ignored programs
        if any(acc_idx in ignore_indices for acc_idx in ix.accounts):
            continue

        result.extend(ix.data)

    # Recent blockhash
    result.extend(bytes(message.recent_blockhash))

    return bytes(result)


def get_tx_message_hash(tx_object: SoldersLegacyTransaction | SoldersVersionedTransaction,
                        algorithm: str = DEFAULT_ALGORITHM) -> str:
    message_bytes = _serialize_message(tx_object.message)
    hash_func = getattr(hashlib, algorithm, None)
    if hash_func is None:
        raise ValueError(f"Unsupported hash algorithm: {algorithm}")
    return hash_func(message_bytes).hexdigest()


def get_base64_tx_message_hash(base64_tx: str,
                               algorithm: str = DEFAULT_ALGORITHM) -> str:
    try:
        raw_bytes = base64.b64decode(base64_tx, validate=True)
    except Exception as e:
        raise ValueError(f"Invalid base64: {e}")

    tx_object = (try_build_versioned_tx_from_bytes(raw_bytes, raise_on_error=False)
                 or try_build_legacy_tx_from_bytes(raw_bytes, raise_on_error=False))
    if tx_object:
        return get_tx_message_hash(tx_object, algorithm)

    raise ValueError(f"Invalid base64 transaction: {base64_tx}")


def get_base58_tx_message_hash(base58_tx: str,
                               algorithm: str = DEFAULT_ALGORITHM) -> str:
    try:
        raw_bytes = base58.b58decode(base58_tx)
    except Exception as e:
        raise ValueError(f"Invalid base58: {e}")

    tx_object = (try_build_versioned_tx_from_bytes(raw_bytes, raise_on_error=False)
                 or try_build_legacy_tx_from_bytes(raw_bytes, raise_on_error=False))
    if tx_object:
        return get_tx_message_hash(tx_object, algorithm)

    raise ValueError(f"Invalid base58 transaction: {base58_tx}")
