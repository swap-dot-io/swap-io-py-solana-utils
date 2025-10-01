"""
Pydantic models for Solana transaction data with base58 decoding support.
"""
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
import base58


class MessageHeader(BaseModel):
    num_required_signatures: int
    num_readonly_signed_accounts: int
    num_readonly_unsigned_accounts: int


class MessageAddressTableLookup(BaseModel):
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
    header: Optional[MessageHeader] = None
    account_keys: List[str] = Field(default_factory=list)
    recent_blockhash: str = ""
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
    err: str

    @field_validator('err', mode='before')
    @classmethod
    def decode_error(cls, v):
        if isinstance(v, bytes):
            return v.hex()
        return v


class TransactionStatusMeta(BaseModel):
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
    signatures: List[str] = Field(default_factory=list)
    message: Optional[Message] = None

    @field_validator('signatures', mode='before')
    @classmethod
    def decode_signatures(cls, v):
        if isinstance(v, list):
            return [base58.b58encode(sig).decode('utf-8') if isinstance(sig, bytes) else sig for sig in v]
        return v or []


class TransactionInfo(BaseModel):
    signature: str
    is_vote: bool = False
    transaction: Optional[Transaction] = None
    meta: Optional[TransactionStatusMeta] = None
    index: int = 0

    @field_validator('signature', mode='before')
    @classmethod
    def decode_signature(cls, v):
        if isinstance(v, bytes):
            return base58.b58encode(v).decode('utf-8')
        return v


class MessageHash(BaseModel):
    value: str
    algorithm: str


class TransactionModel(BaseModel):
    transaction: Optional[TransactionInfo] = None
    slot: int = 0
    message_hash: Optional[MessageHash] = None
