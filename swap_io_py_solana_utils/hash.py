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


def _serialize_message(message: Message) -> bytes:
    """Manually serialize transaction message components."""
    result = bytearray()

    # Prepare account keys
    account_keys = list(message.account_keys)
    lighthouse_index = None
    compute_budget_index = None

    for i, key in enumerate(account_keys):
        if key == LIGHTHOUSE_PROGRAM_ID:
            lighthouse_index = i
        if key == COMPUTE_BUDGET_ID:
            compute_budget_index = i

    account_keys = [key for key in account_keys if key not in [LIGHTHOUSE_PROGRAM_ID, COMPUTE_BUDGET_ID]]
    # Sorted account keys
    sorted_keys = sorted(account_keys, key=lambda x: bytes(x))

    for key in sorted_keys:
        result.extend(bytes(key))

    # Instructions data only
    for ix in message.instructions:
        if lighthouse_index is not None:
            if (
                ix.program_id_index == lighthouse_index
                or lighthouse_index in ix.accounts
            ):
                continue
        if compute_budget_index is not None:
            if (
                ix.program_id_index == compute_budget_index
                or compute_budget_index in ix.accounts
            ):
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
