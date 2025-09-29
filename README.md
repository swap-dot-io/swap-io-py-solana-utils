# Solana TX Utils

Utilities for working with Solana transactions

## Installation

```bash
pip install solana-tx-utils
```

Or install from source:

```bash
pip install git+https://github.com/swap-dot-io/solana-tx-utils.git
```

## Usage

```python
from solana_tx_utils import get_base64_tx_message_hash

# Get transaction message hash from base64-encoded transaction
base64_tx = "your_base64_encoded_transaction_here"
tx_hash = get_base64_tx_message_hash(base64_tx)
print(f"Transaction hash: {tx_hash}")
```

### Working with transaction objects directly

```python
from solana_tx_utils import get_tx_message_hash, try_build_versioned_tx, try_build_legacy_tx

# Build transaction from raw bytes
raw_bytes = b"..."
tx = try_build_versioned_tx(raw_bytes) or try_build_legacy_tx(raw_bytes)

if tx:
    tx_hash = get_tx_message_hash(tx)
    print(f"Transaction hash: {tx_hash}")
```

## API

### `get_base64_tx_message_hash(base64_tx: str) -> str`

Computes the SHA-256 hash of a transaction message from a base64-encoded transaction string.

- **Parameters:** `base64_tx` - Base64-encoded Solana transaction
- **Returns:** Hex-encoded SHA-256 hash of the transaction message
- **Raises:** `ValueError` if the input is invalid

### `get_tx_message_hash(tx_object: Transaction | VersionedTransaction) -> str`

Computes the SHA-256 hash of a transaction message from a transaction object.

- **Parameters:** `tx_object` - Solana transaction object (legacy or versioned)
- **Returns:** Hex-encoded SHA-256 hash of the transaction message

### `try_build_versioned_tx(tx_raw_bytes: bytes) -> VersionedTransaction | None`

Attempts to build a versioned transaction from raw bytes.

- **Parameters:** `tx_raw_bytes` - Raw transaction bytes
- **Returns:** `VersionedTransaction` object or `None` if parsing fails

### `try_build_legacy_tx(tx_raw_bytes: bytes) -> Transaction | None`

Attempts to build a legacy transaction from raw bytes.

- **Parameters:** `tx_raw_bytes` - Raw transaction bytes
- **Returns:** `Transaction` object or `None` if parsing fails

## Requirements

- Python >= 3.10
- solders >= 0.18.0

## License

MIT