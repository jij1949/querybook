from typing import List, Optional, Tuple

from flask_login import current_user

from app.db import DBSession
from lib.metastore import get_metastore_loader_class_by_name
from logic import admin as admin_logic


def get_user_sandbox_schema(user) -> str:
    """Derive a user's sandbox schema name from their email prefix."""
    if not user.email:
        return ""
    return user.email.split("@")[0]


def get_sandbox_context(
    metastore_id: int,
) -> Optional[Tuple[List[str], str]]:
    """Resolve sandbox filtering context for the current user.

    Returns (sandbox_catalog_names, user_schema_name) if sandbox filtering
    applies, or None if no filtering is needed.
    """
    from models.user import User as UserModel

    metastore = admin_logic.get_query_metastore_by_id(metastore_id)
    if not metastore:
        return None

    metastore_dict = metastore.to_dict_admin()
    loader_class = get_metastore_loader_class_by_name(metastore_dict["loader"])
    sandbox_catalog_names = loader_class.get_sandbox_catalog_names(metastore_dict)
    if not sandbox_catalog_names:
        return None

    with DBSession() as session:
        orm_user = (
            session.query(UserModel).filter(UserModel.id == current_user.id).first()
        )

    user_schema = get_user_sandbox_schema(orm_user)
    if not user_schema:
        return None

    return sandbox_catalog_names, user_schema
