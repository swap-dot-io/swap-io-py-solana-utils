import base64

import base58
from solders.transaction import (Transaction as SoldersLegacyTransaction,
                                 VersionedTransaction as SoldersVersionedTransaction)


def try_build_versioned_tx_from_base64(tx_base64: str, raise_on_error: bool = True) -> SoldersVersionedTransaction | None:
    try:
        raw_bytes = base64.b64decode(tx_base64, validate=True)
    except Exception:
        if raise_on_error:
            raise
    else:
        return try_build_versioned_tx_from_bytes(raw_bytes, raise_on_error)


def try_build_legacy_tx_from_base64(tx_base64: str, raise_on_error: bool = True) -> SoldersLegacyTransaction | None:
    try:
        raw_bytes = base64.b64decode(tx_base64, validate=True)
    except Exception:
        if raise_on_error:
            raise
    else:
        return try_build_legacy_tx_from_bytes(raw_bytes, raise_on_error)


def try_build_versioned_tx_from_base58(tx_base58: str, raise_on_error: bool = True) -> SoldersVersionedTransaction | None:
    try:
        raw_bytes = base58.b58decode(tx_base58)
    except Exception:
        if raise_on_error:
            raise
    else:
        return try_build_versioned_tx_from_bytes(raw_bytes, raise_on_error)


def try_build_legacy_tx_from_base58(tx_base58: str, raise_on_error: bool = True) -> SoldersLegacyTransaction | None:
    try:
        raw_bytes = base58.b58decode(tx_base58)
    except Exception:
        if raise_on_error:
            raise
    else:
        return try_build_legacy_tx_from_bytes(raw_bytes, raise_on_error)


def try_build_versioned_tx_from_bytes(tx_raw_bytes: bytes, raise_on_error: bool = True) -> SoldersVersionedTransaction | None:
    try:
        return SoldersVersionedTransaction.from_bytes(tx_raw_bytes)
    except Exception:
        if raise_on_error:
            raise


def try_build_legacy_tx_from_bytes(tx_raw_bytes: bytes, raise_on_error: bool = True) -> SoldersLegacyTransaction | None:
    try:
        return SoldersLegacyTransaction.from_bytes(tx_raw_bytes)
    except Exception:
        if raise_on_error:
            raise
