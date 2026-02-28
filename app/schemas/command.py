from pydantic import BaseModel


class SellerCommandRequest(BaseModel):
    command: str
