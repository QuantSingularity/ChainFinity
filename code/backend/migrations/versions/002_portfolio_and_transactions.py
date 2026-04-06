"""Portfolio and transaction tables

Revision ID: 002
Revises: 001
Create Date: 2025-01-08 12:00:00.000000

"""

import uuid
from typing import Any

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> Any:
    op.create_table(
        "portfolios",
        sa.Column(
            "id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "portfolio_type",
            sa.Enum("personal", "managed", "algorithmic", name="portfoliotype"),
            nullable=False,
            default="personal",
        ),
        sa.Column("base_currency", sa.String(3), nullable=False, default="USD"),
        sa.Column("total_value_usd", sa.Numeric(20, 8), nullable=False, default=0),
        sa.Column("total_cost_basis_usd", sa.Numeric(20, 8), nullable=False, default=0),
        sa.Column("unrealized_pnl_usd", sa.Numeric(20, 8), nullable=False, default=0),
        sa.Column("realized_pnl_usd", sa.Numeric(20, 8), nullable=False, default=0),
        sa.Column("performance_1d", sa.Numeric(10, 4), nullable=True),
        sa.Column("performance_7d", sa.Numeric(10, 4), nullable=True),
        sa.Column("performance_30d", sa.Numeric(10, 4), nullable=True),
        sa.Column("performance_ytd", sa.Numeric(10, 4), nullable=True),
        sa.Column("performance_all_time", sa.Numeric(10, 4), nullable=True),
        sa.Column("risk_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("sharpe_ratio", sa.Numeric(10, 4), nullable=True),
        sa.Column("max_drawdown", sa.Numeric(10, 4), nullable=True),
        sa.Column("volatility", sa.Numeric(10, 4), nullable=True),
        sa.Column("beta", sa.Numeric(10, 4), nullable=True),
        sa.Column("alpha", sa.Numeric(10, 4), nullable=True),
        sa.Column("last_rebalanced_at", sa.DateTime(), nullable=True),
        sa.Column("rebalance_frequency_days", sa.Integer(), nullable=True),
        sa.Column(
            "auto_rebalance_enabled", sa.Boolean(), nullable=False, default=False
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, default=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, default=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, default=1),
    )
    op.create_index("idx_portfolio_user_id", "portfolios", ["user_id"])
    op.create_index("idx_portfolio_user_active", "portfolios", ["user_id", "is_active"])
    op.create_index("idx_portfolio_type", "portfolios", ["portfolio_type"])
    op.create_table(
        "portfolio_assets",
        sa.Column(
            "id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
        ),
        sa.Column(
            "portfolio_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("portfolios.id"),
            nullable=False,
        ),
        sa.Column("asset_symbol", sa.String(20), nullable=False),
        sa.Column("asset_name", sa.String(255), nullable=False),
        sa.Column(
            "asset_type",
            sa.Enum("cryptocurrency", "token", "nft", "defi", name="assettype"),
            nullable=False,
        ),
        sa.Column("chain_id", sa.Integer(), nullable=False),
        sa.Column("contract_address", sa.String(42), nullable=True),
        sa.Column("quantity", sa.Numeric(30, 18), nullable=False, default=0),
        sa.Column("average_cost_usd", sa.Numeric(20, 8), nullable=False, default=0),
        sa.Column("current_price_usd", sa.Numeric(20, 8), nullable=False, default=0),
        sa.Column("market_value_usd", sa.Numeric(20, 8), nullable=False, default=0),
        sa.Column("cost_basis_usd", sa.Numeric(20, 8), nullable=False, default=0),
        sa.Column("unrealized_pnl_usd", sa.Numeric(20, 8), nullable=False, default=0),
        sa.Column("realized_pnl_usd", sa.Numeric(20, 8), nullable=False, default=0),
        sa.Column("allocation_percentage", sa.Numeric(5, 2), nullable=False, default=0),
        sa.Column("target_allocation_percentage", sa.Numeric(5, 2), nullable=True),
        sa.Column("last_price_update", sa.DateTime(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, default=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, default=1),
    )
    op.create_index(
        "idx_portfolio_asset_portfolio_id", "portfolio_assets", ["portfolio_id"]
    )
    op.create_index("idx_portfolio_asset_symbol", "portfolio_assets", ["asset_symbol"])
    op.create_index("idx_portfolio_asset_chain", "portfolio_assets", ["chain_id"])
    op.create_unique_constraint(
        "uq_portfolio_asset",
        "portfolio_assets",
        ["portfolio_id", "asset_symbol", "chain_id"],
    )
    op.create_table(
        "transactions",
        sa.Column(
            "id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column(
            "portfolio_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("portfolios.id"),
            nullable=True,
        ),
        sa.Column("transaction_hash", sa.String(66), nullable=True, unique=True),
        sa.Column(
            "transaction_type",
            sa.Enum(
                "buy",
                "sell",
                "transfer_in",
                "transfer_out",
                "swap",
                "stake",
                "unstake",
                "claim",
                "deposit",
                "withdraw",
                name="transactiontype",
            ),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "pending", "confirmed", "failed", "cancelled", name="transactionstatus"
            ),
            nullable=False,
            default="pending",
        ),
        sa.Column("chain_id", sa.Integer(), nullable=False),
        sa.Column("block_number", sa.BigInteger(), nullable=True),
        sa.Column("block_timestamp", sa.DateTime(), nullable=True),
        sa.Column("from_address", sa.String(42), nullable=True),
        sa.Column("to_address", sa.String(42), nullable=True),
        sa.Column("asset_symbol", sa.String(20), nullable=False),
        sa.Column("asset_contract_address", sa.String(42), nullable=True),
        sa.Column("quantity", sa.Numeric(30, 18), nullable=False),
        sa.Column("price_usd", sa.Numeric(20, 8), nullable=True),
        sa.Column("value_usd", sa.Numeric(20, 8), nullable=True),
        sa.Column("gas_used", sa.BigInteger(), nullable=True),
        sa.Column("gas_price", sa.BigInteger(), nullable=True),
        sa.Column("gas_fee_usd", sa.Numeric(20, 8), nullable=True),
        sa.Column("exchange_rate", sa.Numeric(30, 18), nullable=True),
        sa.Column("slippage", sa.Numeric(5, 4), nullable=True),
        sa.Column("fee_percentage", sa.Numeric(5, 4), nullable=True),
        sa.Column("fee_amount_usd", sa.Numeric(20, 8), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("risk_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("compliance_checked", sa.Boolean(), nullable=False, default=False),
        sa.Column(
            "compliance_status",
            sa.Enum(
                "pending", "approved", "flagged", "blocked", name="compliancestatus"
            ),
            nullable=False,
            default="pending",
        ),
        sa.Column("compliance_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, default=1),
    )
    op.create_index("idx_transaction_user_id", "transactions", ["user_id"])
    op.create_index("idx_transaction_portfolio_id", "transactions", ["portfolio_id"])
    op.create_index("idx_transaction_hash", "transactions", ["transaction_hash"])
    op.create_index("idx_transaction_status", "transactions", ["status"])
    op.create_index("idx_transaction_type", "transactions", ["transaction_type"])
    op.create_index("idx_transaction_chain", "transactions", ["chain_id"])
    op.create_index("idx_transaction_created", "transactions", ["created_at"])
    op.create_index("idx_transaction_compliance", "transactions", ["compliance_status"])
    op.create_table(
        "blockchain_networks",
        sa.Column(
            "id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
        ),
        sa.Column("chain_id", sa.Integer(), nullable=False, unique=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("symbol", sa.String(10), nullable=False),
        sa.Column("rpc_url", sa.String(500), nullable=False),
        sa.Column("websocket_url", sa.String(500), nullable=True),
        sa.Column("explorer_url", sa.String(500), nullable=True),
        sa.Column("explorer_api_url", sa.String(500), nullable=True),
        sa.Column("explorer_api_key", sa.String(255), nullable=True),
        sa.Column("is_testnet", sa.Boolean(), nullable=False, default=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, default=True),
        sa.Column("block_time_seconds", sa.Integer(), nullable=True),
        sa.Column("gas_price_gwei", sa.Numeric(10, 2), nullable=True),
        sa.Column("native_currency_symbol", sa.String(10), nullable=False),
        sa.Column("native_currency_decimals", sa.Integer(), nullable=False, default=18),
        sa.Column("supports_eip1559", sa.Boolean(), nullable=False, default=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )
    op.create_index(
        "idx_blockchain_network_chain_id", "blockchain_networks", ["chain_id"]
    )
    op.create_index(
        "idx_blockchain_network_active", "blockchain_networks", ["is_active"]
    )


def downgrade() -> Any:
    op.drop_table("blockchain_networks")
    op.drop_table("transactions")
    op.drop_table("portfolio_assets")
    op.drop_table("portfolios")
    op.execute("DROP TYPE IF EXISTS portfoliotype")
    op.execute("DROP TYPE IF EXISTS assettype")
    op.execute("DROP TYPE IF EXISTS transactiontype")
    op.execute("DROP TYPE IF EXISTS transactionstatus")
    op.execute("DROP TYPE IF EXISTS compliancestatus")
