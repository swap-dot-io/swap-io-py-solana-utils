from typing import Union
from solders.solders import Pubkey
from solders.instruction import CompiledInstruction
from solders.message import Message, MessageV0
from solders.transaction import (Transaction as SoldersLegacyTransaction,
                                 VersionedTransaction as SoldersVersionedTransaction)

LIGHTHOUSE_PUBKEY = Pubkey.from_string("L2TExMFKdjpN9kozasaurPirfHy9P8sbXoAN1qA3S95")


def build_transaction_without_lighthouse(solders_transaction: Union[SoldersLegacyTransaction, SoldersVersionedTransaction]) -> Union[SoldersLegacyTransaction, SoldersVersionedTransaction]:
    msg = solders_transaction.message

    # Find Lighthouse index
    lighthouse_idx = next((i for i, k in enumerate(msg.account_keys) if k == LIGHTHOUSE_PUBKEY), None)
    if lighthouse_idx is None:
        return solders_transaction

    # Remove Lighthouse from account_keys and build index mapping
    new_account_keys = []
    index_mapping = {}  # old_idx -> new_idx
    for i, key in enumerate(msg.account_keys):
        if i != lighthouse_idx:
            index_mapping[i] = len(new_account_keys)
            new_account_keys.append(key)

    # Filter and remap instructions
    new_instructions = []
    for ci in msg.instructions:
        # Skip if program_id is Lighthouse
        if ci.program_id_index == lighthouse_idx:
            continue

        # Skip if any account is Lighthouse
        if lighthouse_idx in ci.accounts:
            continue

        # Remap indices
        new_program_id_index = index_mapping.get(ci.program_id_index)
        new_accounts = bytes([index_mapping[i] for i in ci.accounts if i in index_mapping])

        new_instructions.append(CompiledInstruction(
            program_id_index=new_program_id_index,
            accounts=new_accounts,
            data=bytes(ci.data)
        ))

    # Rebuild message with new_with_compiled_instructions
    if isinstance(solders_transaction, SoldersVersionedTransaction):
        new_msg = MessageV0.try_compile(new_account_keys[0], [], [], msg.recent_blockhash)
        # Manually reconstruct with filtered data
        from solders.message import Message as LegacyMessage
        temp_msg = LegacyMessage.new_with_compiled_instructions(
            msg.header.num_required_signatures,
            msg.header.num_readonly_signed_accounts,
            msg.header.num_readonly_unsigned_accounts,
            new_account_keys,
            msg.recent_blockhash,
            new_instructions
        )
        return SoldersLegacyTransaction.populate(temp_msg, solders_transaction.signatures)
    else:
        new_msg = Message.new_with_compiled_instructions(
            msg.header.num_required_signatures,
            msg.header.num_readonly_signed_accounts,
            msg.header.num_readonly_unsigned_accounts,
            new_account_keys,
            msg.recent_blockhash,
            new_instructions
        )
        return SoldersLegacyTransaction.populate(new_msg, solders_transaction.signatures)
