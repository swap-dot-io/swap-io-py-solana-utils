# Solana utils

Utilities for working with Solana

## Installation

```bash
pip install swap-io-py-solana-utils
```

Or install from source:

```bash
pip install git+https://github.com/swap-dot-io/swap-io-py-solana-utils.git
```

## Usage

```python
from swap_io_py_solana_utils import get_base64_tx_message_hash

# Get transaction message hash from base64-encoded transaction
base64_tx = "your_base64_encoded_transaction_here"
tx_hash = get_base64_tx_message_hash(base64_tx)
print(f"Transaction hash: {tx_hash}")
```

### Working with transaction objects directly

```python
from swap_io_py_solana_utils import get_tx_message_hash, try_build_versioned_tx, try_build_legacy_tx

# Build transaction from raw bytes
raw_bytes = b"..."
tx = try_build_versioned_tx(raw_bytes) or try_build_legacy_tx(raw_bytes)

if tx:
    tx_hash = get_tx_message_hash(tx)
    print(f"Transaction hash: {tx_hash}")
```

## API

### `get_base64_tx_message_hash(base64_tx: str, algorithm: str = "sha256") -> str`

Computes the hash of a transaction message from a base64-encoded transaction string.

- **Parameters:**
  - `base64_tx` - Base64-encoded Solana transaction
  - `algorithm` - Hash algorithm to use (default: "sha256")
- **Returns:** Hex-encoded hash of the transaction message
- **Raises:** `ValueError` if the input is invalid or algorithm is unsupported

### `get_base58_tx_message_hash(base58_tx: str, algorithm: str = "sha256") -> str`

Computes the hash of a transaction message from a base58-encoded transaction string.

- **Parameters:**
  - `base58_tx` - Base58-encoded Solana transaction
  - `algorithm` - Hash algorithm to use (default: "sha256")
- **Returns:** Hex-encoded hash of the transaction message
- **Raises:** `ValueError` if the input is invalid or algorithm is unsupported

### `get_tx_message_hash(tx_object: Transaction | VersionedTransaction, algorithm: str = "sha256") -> str`

Computes the hash of a transaction message from a transaction object.

- **Parameters:**
  - `tx_object` - Solana transaction object (legacy or versioned)
  - `algorithm` - Hash algorithm to use (default: "sha256")
- **Returns:** Hex-encoded hash of the transaction message
- **Raises:** `ValueError` if the algorithm is unsupported

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
- base58 >= 2.1.1

## License

MIT