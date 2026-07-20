from pydantic import BaseModel, Field


class ContestParameters(BaseModel):
    contest_type: str = Field(default="by_finish_date")
    length_value: int = Field(default=3)
    length_option: str = Field(default="days")
    prize_type: str = Field(default="money")
    count_winners: int = Field(default=1)
    prize_data_money: int = Field(default=500)
    require_like_count: int = Field(default=1)
    require_total_like_count: int = Field(default=200)
    tags: str = Field(default="")


class ContestConfig(BaseModel):
    title: str
    body: str
    parameters: ContestParameters = Field(default_factory=ContestParameters)
