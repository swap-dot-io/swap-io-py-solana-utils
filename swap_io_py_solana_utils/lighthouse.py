from typing import Union
from solders.solders import Pubkey
from solders.instruction import Instruction, AccountMeta
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

    # Helper to check account properties
    def is_signer(idx): return idx < msg.header.num_required_signatures
    def is_writable(idx):
        if idx < msg.header.num_required_signatures:
            return idx >= msg.header.num_readonly_signed_accounts
        return idx < len(msg.account_keys) - msg.header.num_readonly_unsigned_accounts

    # Build instructions without Lighthouse
    instructions = []
    for ci in msg.instructions:
        # Skip if program_id is Lighthouse
        if ci.program_id_index == lighthouse_idx:
            continue

        # Skip if any account is Lighthouse (check only valid indices)
        if any(i == lighthouse_idx for i in ci.accounts if i < len(msg.account_keys)):
            continue

        # Build account metas only for valid indices
        account_metas = []
        for i in ci.accounts:
            if i < len(msg.account_keys):
                account_metas.append(AccountMeta(msg.account_keys[i], is_signer(i), is_writable(i)))

        instructions.append(Instruction(
            program_id=msg.account_keys[ci.program_id_index],
            accounts=account_metas,
            data=bytes(ci.data)
        ))

    # Rebuild message and transaction
    if isinstance(solders_transaction, SoldersVersionedTransaction):
        new_msg = MessageV0.try_compile(msg.account_keys[0], instructions, [], msg.recent_blockhash)
        # Create empty signatures for required signers
        from solders.signature import Signature
        empty_sigs = [Signature.default()] * new_msg.header.num_required_signatures
        return SoldersVersionedTransaction(new_msg, empty_sigs)
    else:
        new_msg = Message.new_with_blockhash(instructions, msg.account_keys[0], msg.recent_blockhash)
        return SoldersLegacyTransaction.new_unsigned(new_msg)
