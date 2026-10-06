import logging

from fastapi import APIRouter, HTTPException

from app.infrastructure.database.mongo import salvar_cotacao_no_mongo

router = APIRouter(prefix="/quotes", tags=["quotes"])
logger = logging.getLogger(__name__)


@router.post("/{symbol}")
def get_quote(symbol: str):
    try:
        quote = salvar_cotacao_no_mongo(symbol.upper())
    except Exception as exc:
        logger.exception("Quote fetch/save failed")
        raise HTTPException(
            status_code=502,
            detail="Could not fetch the quote or save it to MongoDB",
        ) from exc

    if not quote:
        raise HTTPException(status_code=404, detail="No quote found for this symbol")

    return quote