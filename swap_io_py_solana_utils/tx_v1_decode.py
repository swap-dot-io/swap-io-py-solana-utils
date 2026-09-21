"""
Solana Transaction **v1** decoder (SIMD-0296 "Larger Transactions" + SIMD-0385
"Transaction v1 Format").

solders (as of the pinned version) cannot parse a v1 transaction — its
``VersionedTransaction.from_bytes`` only understands legacy + v0 (version byte
0x80). A v1 tx starts with ``0x81`` and carries its compute-budget config in a
header ``config_mask``/``config_values`` block instead of as ComputeBudget
instructions, and it forbids address lookup tables (all accounts inline, max 64).

Because a v1 tx has no ALTs and ≤64 inline accounts, it can always be represented
losslessly as a solders ``MessageV0`` (v0's only extra capability — ALT lookups —
is simply unused). So we parse the v1 wire bytes by hand and rebuild an equivalent
``VersionedTransaction``, which lets every existing helper in this package
(``from_solders_transaction``, ``get_tx_message_hash``, …) work on v1 unchanged.

v1 wire layout (integers little-endian):
    version                u8   = 0x81
    header                 3xu8 = required_sigs, readonly_signed, readonly_unsigned
    config_mask            u32  bitmask: [0,1]=priority-fee(u64) [2]=cu-limit(u32)
                                         [3]=loaded-accounts-data-size(u32) [4]=heap(u32)
    blockhash              32B
    num_instructions       u8
    num_addresses          u8
    addresses              num_addresses x 32B
    config_values          popcount(mask) x 4B  (ascending bit order; priority-fee
                                                  spans 2 bits == 2 words == one u64)
    instruction_headers    num_instructions x (prog_idx u8, n_accts u8, n_data u16)
    instruction_payloads   per ix: account-index bytes ++ data bytes
    signatures             required_sigs x 64B  (trailing; may be absent/partial)
"""

from __future__ import annotations

from solders.hash import Hash
from solders.instruction import CompiledInstruction
from solders.message import MessageHeader, MessageV0
from solders.pubkey import Pubkey
from solders.signature import Signature
from solders.transaction import VersionedTransaction

TX_V1_VERSION_BYTE = 0x81  # == 129


def is_v1_transaction(raw: bytes) -> bool:
    """True if the raw bytes look like a Transaction v1 (version byte 0x81)."""
    return len(raw) > 0 and raw[0] == TX_V1_VERSION_BYTE


def rebuild_versioned_tx_from_v1_bytes(raw: bytes) -> VersionedTransaction:
    """Parse v1 wire bytes and rebuild an equivalent solders ``VersionedTransaction``.

    Accepts a full (signed) v1 tx or a bare message body (no trailing signatures);
    missing signature slots are filled with the default (all-zero) signature.
    Raises ``ValueError`` on malformed/truncated input.
    """
    o = 0

    def take(n: int) -> bytes:
        nonlocal o
        if o + n > len(raw):
            raise ValueError("truncated v1 transaction")
        b = raw[o:o + n]
        o += n
        return b

    if take(1)[0] != TX_V1_VERSION_BYTE:
        raise ValueError("not a v1 transaction")
    req_sigs = take(1)[0]
    ro_signed = take(1)[0]
    ro_unsigned = take(1)[0]
    config_mask = int.from_bytes(take(4), "little")
    blockhash = Hash.from_bytes(take(32))
    num_ix = take(1)[0]
    num_addr = take(1)[0]
    account_keys = [Pubkey.from_bytes(take(32)) for _ in range(num_addr)]
    # config_values: one 4-byte word per set mask bit (priority-fee's 2 bits == 2 words).
    take(bin(config_mask).count("1") * 4)

    headers = []  # (prog_idx, n_acc, n_data)
    for _ in range(num_ix):
        prog_idx = take(1)[0]
        n_acc = take(1)[0]
        n_data = int.from_bytes(take(2), "little")
        headers.append((prog_idx, n_acc, n_data))

    instructions = []
    for prog_idx, n_acc, n_data in headers:
        accounts = take(n_acc)
        data = take(n_data)
        instructions.append(
            CompiledInstruction(program_id_index=prog_idx, accounts=bytes(accounts), data=bytes(data))
        )

    message = MessageV0(
        MessageHeader(req_sigs, ro_signed, ro_unsigned),
        account_keys,
        blockhash,
        instructions,
        [],  # v1 has no address lookup tables
    )

    trailing = raw[o:]
    signatures = [
        Signature.from_bytes(trailing[i * 64:(i + 1) * 64])
        for i in range(len(trailing) // 64)
    ]
    if len(signatures) < req_sigs:
        signatures += [Signature.default()] * (req_sigs - len(signatures))
    signatures = signatures[:req_sigs]

    return VersionedTransaction.populate(message, signatures)
