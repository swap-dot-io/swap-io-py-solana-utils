import base64
import hashlib

import base58
from solders.message import to_bytes_versioned
from solders.transaction import Transaction, VersionedTransaction


def try_build_versioned_tx(tx_raw_bytes: bytes) -> VersionedTransaction | None:
    try:
        return VersionedTransaction.from_bytes(tx_raw_bytes)
    except Exception:  # noqa
        pass


def try_build_legacy_tx(tx_raw_bytes: bytes) -> Transaction | None:
    try:
        return Transaction.from_bytes(tx_raw_bytes)
    except Exception:  # noqa
        pass


def get_tx_message_hash(tx_object: Transaction | VersionedTransaction) -> str:
    message_bytes = to_bytes_versioned(tx_object.message)
    return hashlib.sha256(message_bytes).digest().hex()


def get_base64_tx_message_hash(base64_tx: str) -> str:
    try:
        raw_bytes = base64.b64decode(base64_tx, validate=True)
    except Exception as e:
        raise ValueError(f"Invalid base64: {e}")

    tx_object = try_build_versioned_tx(raw_bytes) or try_build_legacy_tx(raw_bytes)
    if tx_object:
        return get_tx_message_hash(tx_object)

    raise ValueError(f"Invalid base64 transaction: {base64_tx}")


def get_base58_tx_message_hash(base58_tx: str) -> str:
    try:
        raw_bytes = base58.b58decode(base58_tx)
    except Exception as e:
        raise ValueError(f"Invalid base58: {e}")

    tx_object = try_build_versioned_tx(raw_bytes) or try_build_legacy_tx(raw_bytes)
    if tx_object:
        return get_tx_message_hash(tx_object)

    raise ValueError(f"Invalid base58 transaction: {base58_tx}")
