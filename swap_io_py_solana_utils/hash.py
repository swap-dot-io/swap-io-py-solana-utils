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
    """
    Creates a consistent 'logical fingerprint' of a transaction message.

    This function ignores volatile data that varies between a locally created
    Pending transaction and a Finalized transaction returned by RPC nodes
    (e.g., expanded ALT keys, modified headers, or shifted indices).
    """
    result = bytearray()

    # 1. Recent Blockhash (Time Anchor)
    # Ensures we are comparing transactions within the same time window.
    result.extend(bytes(message.recent_blockhash))

    # 2. Fee Payer / Signer (Identity Anchor)
    # The first account at index 0 is ALWAYS the fee payer/signer.
    # It remains constant even if the RPC node expands the account list with ALT keys.
    # This distinguishes identical swaps made by different users.
    if len(message.account_keys) > 0:
        result.extend(bytes(message.account_keys[0]))

    # 3. Instructions (Action Anchor)
    # We serialize 'WHAT' is happening (Program + Data), ignoring 'HOW' it's indexed.
    for ix in message.instructions:
        # Resolve the actual Program ID using the index.
        # This fixes issues where indices shift (e.g., ComputeBudget moving from idx 4 to 5).
        try:
            program_id = message.account_keys[ix.program_id_index]
        except IndexError:
            # Skip malformed instructions if index is out of bounds
            continue

        # Skip infrastructure programs that don't affect the business logic
        if program_id in DEFAULT_IGNORE_PROGRAMS:
            continue

        # Serialize Program ID (Who executes)
        result.extend(bytes(program_id))

        # Serialize Instruction Data (What parameters/amounts)
        # If the user uses a Memo program for uniqueness, it will be captured here.
        result.extend(ix.data)

        # NOTE: We intentionally exclude 'ix.accounts' and 'message.header'.
        # These fields are often modified by RPC nodes (resolving ALT lookups),
        # causing hash mismatches even for the same logical transaction.

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
