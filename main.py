import os
import logging
import typing
from annotated_types import Len
import uvicorn
from fastapi import FastAPI, BackgroundTasks, Request
from pydantic import BaseModel
from fastapi.responses import FileResponse, RedirectResponse
from mflive import MFLive


# logger = logging.getLogger(__name__)
domain_url = os.getenv("DOMAIN_URL")
redirect_status_code = 302


app = FastAPI(
    title="Mutual Funds Live",
    contact={
        "email": "mf-live@" + domain_url.split("//")[-1].replace("/", ""),
    },
    docs_url="/"
)


class MultiFundRequestDTO(BaseModel):
    funds: typing.Annotated[list[str], Len(min_length=1, max_length=5)]


class FundResponseDTO(BaseModel):
    fund: str
    day_change_percentage: float
    not_found: dict
    not_matched: dict


# @app.middleware("http")
# async def my_background_task_middleware(request: Request, call_next):
#     background_tasks = BackgroundTasks()
#     background_tasks.add_task(add_document, request)
#     response = await call_next(request)
#     response.background = background_tasks
#     return response


@app.exception_handler(404)
async def custom_404_handler(req, exc):
    return RedirectResponse(url=domain_url, status_code=redirect_status_code)


@app.get("/mutual-funds/{mutual_fund}", tags=["mutual-funds"])
async def single_fund(mutual_fund: str) -> FundResponseDTO:
    """
    Get live (estimated) day change percentage for a single fund
    """
    mflive = MFLive(mutual_fund)
    info = await mflive.get_info()
    return info[0]


@app.post("/mutual-funds", tags=["mutual-funds"])
async def multiple_funds(mfs: MultiFundRequestDTO) -> list[FundResponseDTO]:
    """
    Get live (estimated) day change percentage for multiple funds
    """
    funds = mfs.funds
    mflive = MFLive(*funds)
    info = await mflive.get_info()
    return info


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", default=5001)), log_level="debug", reload=True)
