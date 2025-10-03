from typing import Union
from solders.pubkey import Pubkey
from solders.instruction import CompiledInstruction
from solders.message import Message, MessageV0, MessageHeader
from solders.transaction import Transaction as SoldersLegacyTransaction, VersionedTransaction as SoldersVersionedTransaction

LIGHTHOUSE_PUBKEY = Pubkey.from_string("L2TExMFKdjpN9kozasaurPirfHy9P8sbXoAN1qA3S95")


def build_transaction_without_lighthouse(
    solders_transaction: Union[SoldersLegacyTransaction, SoldersVersionedTransaction]
) -> Union[SoldersLegacyTransaction, SoldersVersionedTransaction]:
    msg = solders_transaction.message

    lighthouse_idx = next((i for i, k in enumerate(msg.account_keys) if k == LIGHTHOUSE_PUBKEY), None)
    if lighthouse_idx is None:
        return solders_transaction

    # Remove Lighthouse from account_keys
    new_account_keys = [k for i, k in enumerate(msg.account_keys) if i != lighthouse_idx]

    # Determine if Lighthouse was readonly unsigned and adjust header
    num_signed = msg.header.num_required_signatures
    num_readonly_signed = msg.header.num_readonly_signed_accounts
    num_readonly_unsigned = msg.header.num_readonly_unsigned_accounts

    # Check if lighthouse_idx is in readonly unsigned section
    readonly_unsigned_start = num_signed + num_readonly_signed
    if lighthouse_idx >= readonly_unsigned_start:
        num_readonly_unsigned -= 1

    new_header = MessageHeader(
        num_required_signatures=num_signed,
        num_readonly_signed_accounts=num_readonly_signed,
        num_readonly_unsigned_accounts=num_readonly_unsigned
    )

    # Helper function to adjust account index
    def adjust_index(idx: int) -> int:
        if idx == lighthouse_idx:
            raise ValueError(f"Instruction references Lighthouse account at index {lighthouse_idx}")
        return idx if idx < lighthouse_idx else idx - 1

    # Filter out instructions that use Lighthouse and adjust indices
    new_instructions = []
    for ci in msg.instructions:
        if ci.program_id_index == lighthouse_idx or lighthouse_idx in ci.accounts:
            continue

        new_program_id_index = adjust_index(ci.program_id_index)
        new_accounts = bytes([adjust_index(acc) for acc in ci.accounts])
        new_instructions.append(
            CompiledInstruction(new_program_id_index, bytes(ci.data), new_accounts)
        )

    if isinstance(solders_transaction, SoldersVersionedTransaction):
        # For VersionedTransaction, rebuild MessageV0 with address_table_lookups
        new_msg = MessageV0(
            new_header,
            new_account_keys,
            msg.recent_blockhash,
            new_instructions,
            list(msg.address_table_lookups) if hasattr(msg, 'address_table_lookups') else []
        )
        return SoldersVersionedTransaction.populate(new_msg, solders_transaction.signatures)
    else:
        new_msg = Message.new_with_compiled_instructions(
            new_header.num_required_signatures,
            new_header.num_readonly_signed_accounts,
            new_header.num_readonly_unsigned_accounts,
            new_account_keys,
            msg.recent_blockhash,
            new_instructions
        )
        return SoldersLegacyTransaction.populate(new_msg, solders_transaction.signatures)
