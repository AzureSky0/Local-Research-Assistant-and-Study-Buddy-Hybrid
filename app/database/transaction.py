from sqlalchemy.orm import Session


def commit(session: Session) -> None:
    """Commit the current transaction, rolling back if the commit fails.

    Services own transaction boundaries. Repositories only add, flush,
    and query, so several repository calls can be committed together.
    """
    try:
        session.commit()
    except Exception:
        session.rollback()
        raise
