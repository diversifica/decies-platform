from sqlalchemy.orm import Session

from app.models.game import Game
from app.models.item import Item


class GameService:
    def __init__(self, db: Session):
        self.db = db

    def list_games(self, active: bool | None = None) -> list[Game]:
        query = self.db.query(Game)
        if active is not None:
            query = query.filter(Game.active == active)
        return query.order_by(Game.code).all()

    def get_by_code(self, code: str) -> Game | None:
        return self.db.query(Game).filter(Game.code == code).first()

    def update(self, game: Game, *, active: bool | None = None) -> Game:
        if active is not None:
            game.active = active
        self.db.add(game)
        self.db.commit()
        self.db.refresh(game)
        return game

    def has_content(self, game: Game) -> bool:
        return (
            self.db.query(Item)
            .filter(Item.source_game == game.code, Item.is_active.is_(True))
            .limit(1)
            .first()
            is not None
        )
