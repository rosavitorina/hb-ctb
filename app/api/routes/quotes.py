import logging

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.dependencies import get_current_user
from app.infrastructure.database.mongo import (
    listar_cotacoes_no_mongo,
    salvar_cotacao_no_mongo,
)

router = APIRouter(
    prefix="/quotes",
    tags=["quotes"],
    dependencies=[Depends(get_current_user)],
)
logger = logging.getLogger(__name__)


@router.get("")
def list_quotes(limit: int = Query(default=50, ge=1, le=100)):
    try:
        return listar_cotacoes_no_mongo(limit)
    except Exception as exc:
        logger.exception("Saved quotes could not be read")
        raise HTTPException(
            status_code=503,
            detail="Could not read saved quotes from MongoDB",
        ) from exc


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