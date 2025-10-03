"""
Pydantic models for Solana transaction data with base58 decoding support.
"""
from typing import List, Optional, Union
from pydantic import BaseModel, Field, field_validator, ConfigDict
import base58

from solders.message import Message as SoldersMessage, MessageV0 as SoldersMessageV0
from solders.transaction import (Transaction as SoldersLegacyTransaction,
                                 VersionedTransaction as SoldersVersionedTransaction)

from .hash import DEFAULT_ALGORITHM, get_tx_message_hash
from .core import try_build_versioned_tx_from_base64, try_build_legacy_tx_from_base64, \
    try_build_versioned_tx_from_base58, try_build_legacy_tx_from_base58
from .lighthouse import build_transaction_without_lighthouse


class MessageHeader(BaseModel):
    num_required_signatures: int
    num_readonly_signed_accounts: int
    num_readonly_unsigned_accounts: int


class MessageAddressTableLookup(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    account_key: str
    writable_indexes: str
    readonly_indexes: str

    @field_validator('account_key', mode='before')
    @classmethod
    def decode_account_key(cls, v):
        if isinstance(v, bytes):
            return base58.b58encode(v).decode('utf-8')
        return v

    @field_validator('writable_indexes', 'readonly_indexes', mode='before')
    @classmethod
    def decode_indexes(cls, v):
        if isinstance(v, bytes):
            return v.hex()
        return v


class CompiledInstruction(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    program_id_index: int
    accounts: str
    data: str

    @field_validator('accounts', 'data', mode='before')
    @classmethod
    def decode_bytes_fields(cls, v):
        if isinstance(v, bytes):
            return v.hex()
        return v


class InnerInstruction(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    program_id_index: int
    accounts: str
    data: str
    stack_height: Optional[int] = None

    @field_validator('accounts', 'data', mode='before')
    @classmethod
    def decode_bytes_fields(cls, v):
        if isinstance(v, bytes):
            return v.hex()
        return v


class InnerInstructions(BaseModel):
    index: int
    instructions: List[InnerInstruction]


class Message(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    header: MessageHeader
    account_keys: List[str] = Field(default_factory=list)
    recent_blockhash: str
    instructions: List[CompiledInstruction] = Field(default_factory=list)
    versioned: bool = False
    address_table_lookups: List[MessageAddressTableLookup] = Field(default_factory=list)

    @field_validator('account_keys', mode='before')
    @classmethod
    def decode_account_keys(cls, v):
        if isinstance(v, list):
            return [base58.b58encode(key).decode('utf-8') if isinstance(key, bytes) else key for key in v]
        return v or []

    @field_validator('recent_blockhash', mode='before')
    @classmethod
    def decode_recent_blockhash(cls, v):
        if isinstance(v, bytes):
            return base58.b58encode(v).decode('utf-8')
        return v or ""


class UiTokenAmount(BaseModel):
    ui_amount: float
    decimals: int
    amount: str
    ui_amount_string: str


class TokenBalance(BaseModel):
    account_index: int
    mint: str
    ui_token_amount: Optional[UiTokenAmount] = None
    owner: str
    program_id: str


class ReturnData(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    program_id: str
    data: str

    @field_validator('program_id', mode='before')
    @classmethod
    def decode_program_id(cls, v):
        if isinstance(v, bytes):
            return base58.b58encode(v).decode('utf-8')
        return v

    @field_validator('data', mode='before')
    @classmethod
    def decode_data(cls, v):
        if isinstance(v, bytes):
            return v.hex()
        return v


class Reward(BaseModel):
    pubkey: str
    lamports: int
    post_balance: int
    reward_type: int
    commission: str


class TransactionError(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    err: str

    @field_validator('err', mode='before')
    @classmethod
    def decode_error(cls, v):
        if isinstance(v, bytes):
            return v.hex()
        return v


class TransactionStatusMeta(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    err: Optional[TransactionError] = None
    fee: int = 0
    pre_balances: List[int] = Field(default_factory=list)
    post_balances: List[int] = Field(default_factory=list)
    inner_instructions: List[InnerInstructions] = Field(default_factory=list)
    inner_instructions_none: bool = False
    log_messages: List[str] = Field(default_factory=list)
    log_messages_none: bool = False
    pre_token_balances: List[TokenBalance] = Field(default_factory=list)
    post_token_balances: List[TokenBalance] = Field(default_factory=list)
    rewards: List[Reward] = Field(default_factory=list)
    loaded_writable_addresses: List[str] = Field(default_factory=list)
    loaded_readonly_addresses: List[str] = Field(default_factory=list)
    return_data: Optional[ReturnData] = None
    return_data_none: bool = False
    compute_units_consumed: Optional[int] = None

    @field_validator('loaded_writable_addresses', 'loaded_readonly_addresses', mode='before')
    @classmethod
    def decode_addresses(cls, v):
        if isinstance(v, list):
            return [base58.b58encode(addr).decode('utf-8') if isinstance(addr, bytes) else addr for addr in v]
        return v or []


class Transaction(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    signatures: List[str] = Field(default_factory=list)
    message: Message

    @field_validator('signatures', mode='before')
    @classmethod
    def decode_signatures(cls, v):
        if isinstance(v, list):
            return [base58.b58encode(sig).decode('utf-8') if isinstance(sig, bytes) else sig for sig in v]
        return v or []


class SubscribeUpdateTransactionInfo(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    transaction: Transaction
    signature: Optional[str] = None
    is_vote: bool = False
    meta: Optional[TransactionStatusMeta] = None
    index: Optional[int] = None

    @field_validator('signature', mode='before')
    @classmethod
    def decode_signature(cls, v):
        if v is None:
            return None
        if isinstance(v, bytes):
            return base58.b58encode(v).decode('utf-8')
        return v


class MessageHash(BaseModel):
    value: str
    value_lighthouse_off: str
    algorithm: str = DEFAULT_ALGORITHM


class SubscribeUpdateTransaction(BaseModel):
    transaction: SubscribeUpdateTransactionInfo
    message_hash: MessageHash
    slot: Optional[int] = None
    batch_id: Optional[str] = None
    pre_sign_metadata: Optional[dict] = None

    @classmethod
    def from_base64_transaction(
        cls,
        base64_transaction: str,
        message_hash_algorithm: str = DEFAULT_ALGORITHM,
    ) -> "SubscribeUpdateTransaction":
        transaction = (try_build_versioned_tx_from_base64(base64_transaction, raise_on_error=False)
                       or try_build_legacy_tx_from_base64(base64_transaction, raise_on_error=False))
        if transaction:
            return cls.from_solders_transaction(transaction, message_hash_algorithm)
        raise ValueError(f"Could not decode transaction: {base64_transaction}")

    @classmethod
    def from_base58_transaction(
        cls,
        base58_transaction: str,
        message_hash_algorithm: str = DEFAULT_ALGORITHM,
    ) -> "SubscribeUpdateTransaction":
        transaction = (try_build_versioned_tx_from_base58(base58_transaction, raise_on_error=False)
                       or try_build_legacy_tx_from_base58(base58_transaction, raise_on_error=False))
        if transaction:
            return cls.from_solders_transaction(transaction, message_hash_algorithm)
        raise ValueError(f"Could not decode transaction: {base58_transaction}")

    @classmethod
    def from_solders_transaction(
        cls,
        solders_transaction: Union[SoldersLegacyTransaction, SoldersVersionedTransaction],
        message_hash_algorithm: str = DEFAULT_ALGORITHM,
    ) -> "SubscribeUpdateTransaction":
        message = solders_transaction.message
        message: Union[SoldersMessage, SoldersMessageV0]

        header = MessageHeader(
            num_required_signatures=message.header.num_required_signatures,
            num_readonly_signed_accounts=message.header.num_readonly_signed_accounts,
            num_readonly_unsigned_accounts=message.header.num_readonly_unsigned_accounts,
        )

        account_keys = [str(key) for key in message.account_keys]

        recent_blockhash = str(message.recent_blockhash)

        instructions = []
        for instr in message.instructions:
            instructions.append(CompiledInstruction(
                program_id_index=instr.program_id_index,
                accounts=bytes(instr.accounts).hex(),
                data=bytes(instr.data).hex(),
            ))

        versioned = hasattr(message, 'address_table_lookups')
        address_table_lookups = []
        if versioned:
            message: SoldersMessageV0
            for lookup in message.address_table_lookups:
                address_table_lookups.append(MessageAddressTableLookup(
                    account_key=str(lookup.account_key),
                    writable_indexes=bytes(lookup.writable_indexes).hex(),
                    readonly_indexes=bytes(lookup.readonly_indexes).hex(),
                ))

        msg = Message(
            header=header,
            account_keys=account_keys,
            recent_blockhash=recent_blockhash,
            instructions=instructions,
            versioned=versioned,
            address_table_lookups=address_table_lookups,
        )

        signatures = [str(sig) for sig in solders_transaction.signatures]
        transaction = Transaction(
            signatures=signatures,
            message=msg,
        )

        tx_without_lighthouse = build_transaction_without_lighthouse(solders_transaction)
        message_hash = MessageHash(
            value=get_tx_message_hash(solders_transaction, message_hash_algorithm),
            value_lighthouse_off=get_tx_message_hash(tx_without_lighthouse, message_hash_algorithm),
            algorithm=message_hash_algorithm,
        )

        tx_info = SubscribeUpdateTransactionInfo(transaction=transaction)

        return cls(
            transaction=tx_info,
            message_hash=message_hash,
        )
