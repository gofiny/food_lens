from sqlalchemy import MetaData
import sqlalchemy


metadata = MetaData()


users = sqlalchemy.Table(
    "users",
    metadata,
    sqlalchemy.Column("chat_id", sqlalchemy.BigInteger, primary_key=True),
)
