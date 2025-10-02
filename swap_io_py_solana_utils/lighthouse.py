from typing import Union
from solders.solders import Pubkey
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

    # Filter out instructions that use Lighthouse
    new_instructions = [
        CompiledInstruction(ci.program_id_index, bytes(ci.accounts), bytes(ci.data))
        for ci in msg.instructions
        if ci.program_id_index != lighthouse_idx and lighthouse_idx not in ci.accounts
    ]

    if isinstance(solders_transaction, SoldersVersionedTransaction):
        # For VersionedTransaction, rebuild MessageV0 with address_table_lookups
        new_msg = MessageV0(
            msg.header,
            list(msg.account_keys),
            msg.recent_blockhash,
            new_instructions,
            list(msg.address_table_lookups) if hasattr(msg, 'address_table_lookups') else []
        )
        return SoldersVersionedTransaction.populate(new_msg, solders_transaction.signatures)
    else:
        new_msg = Message.new_with_compiled_instructions(
            msg.header.num_required_signatures,
            msg.header.num_readonly_signed_accounts,
            msg.header.num_readonly_unsigned_accounts,
            list(msg.account_keys),
            msg.recent_blockhash,
            new_instructions
        )
        return SoldersLegacyTransaction.populate(new_msg, solders_transaction.signatures)
