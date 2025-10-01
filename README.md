# Solana utils

Utilities for working with Solana transactions: parsing, hashing, and Pydantic models for transaction data.

## Installation

```bash
pip install swap-io-py-solana-utils
```

Or install from source:

```bash
pip install git+https://github.com/swap-dot-io/swap-io-py-solana-utils.git
```

## Requirements

- Python >= 3.10
- solders >= 0.18.0
- base58 >= 2.1.1
- pydantic >= 2.0

## Features

### Transaction Parsing

Parse Solana transactions from base64, base58, or raw bytes:

```python
from swap_io_py_solana_utils import (
    try_build_versioned_tx_from_base64,
    try_build_legacy_tx_from_base64,
    try_build_versioned_tx_from_base58,
    try_build_legacy_tx_from_base58,
    try_build_versioned_tx_from_bytes,
    try_build_legacy_tx_from_bytes
)

# Parse from base64
tx = try_build_versioned_tx_from_base64(tx_base64)

# Parse from base58
tx = try_build_legacy_tx_from_base58(tx_base58)

# Gracefully handle errors
tx = try_build_versioned_tx_from_base64(tx_base64, raise_on_error=False)
```

### Transaction Message Hashing

Calculate hashes of transaction messages:

```python
from swap_io_py_solana_utils import (
    get_tx_message_hash,
    get_base64_tx_message_hash,
    get_base58_tx_message_hash
)

# From transaction object
hash_value = get_tx_message_hash(tx_object)

# From base64 string
hash_value = get_base64_tx_message_hash(base64_tx)

# From base58 string
hash_value = get_base58_tx_message_hash(base58_tx)

# Use different hash algorithm (default: sha256)
hash_value = get_tx_message_hash(tx_object, algorithm='sha512')
```

### Pydantic Models

Type-safe models for Solana transaction data with automatic base58 encoding/decoding:

```python
from swap_io_py_solana_utils import SubscribeUpdateTransaction

# Build from base64 transaction
tx = SubscribeUpdateTransaction.from_base64_transaction(base64_tx)

# Build from base58 transaction
tx = SubscribeUpdateTransaction.from_base58_transaction(base58_tx)

# Build from solders transaction object
tx = SubscribeUpdateTransaction.from_solders_transaction(solders_tx)

# Access parsed data
print(tx.transaction.transaction.signatures)
print(tx.transaction.transaction.message.account_keys)
print(tx.message_hash.value)
```

Available models:
- `SubscribeUpdateTransaction` - Complete transaction with metadata and message hash
- `SubscribeUpdateTransactionInfo` - Transaction info with signature and metadata
- `Transaction` - Transaction with signatures and message
- `Message` - Transaction message with instructions and account keys
- `TransactionStatusMeta` - Transaction execution metadata
- `CompiledInstruction`, `InnerInstruction` - Instruction data
- `MessageHeader`, `MessageAddressTableLookup` - Message components
- `TokenBalance`, `UiTokenAmount`, `ReturnData`, `Reward` - Metadata components

## License

MIT