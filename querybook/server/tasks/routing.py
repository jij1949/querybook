from lib.logger import get_logger

LOG = get_logger(__name__)

K8S_ONLY_QUEUE = "k8s-only"

# task name → the arg carrying the metastore id the task operates on
_ROUTED_METASTORE_TASKS = {
    "tasks.update_metastore.update_metastore": "id",
    "tasks.update_metastore.update_metastore_child": "combo_id",
    "tasks.update_metastore.finalize_combo_metastore": "combo_id",
}

# Lazily-built {class_name: loader_class} map. Deferred to first use on purpose:
# importing the loader registry at module load pulls the metastore/logic graph
# into the Celery/app import chain and causes a circular import.
_loader_by_name = None


def _get_loader_by_name():
    global _loader_by_name
    if _loader_by_name is None:
        from lib.metastore.all_loaders import ALL_METASTORE_LOADERS

        _loader_by_name = {cls.__name__: cls for cls in ALL_METASTORE_LOADERS}
    return _loader_by_name


def route_metastore_task(name, args, kwargs, options, task=None, **kw):
    if name not in _ROUTED_METASTORE_TASKS:
        return None
    kwarg_name = _ROUTED_METASTORE_TASKS[name]
    metastore_id = args[0] if args else kwargs.get(kwarg_name)
    if metastore_id is None:
        return None
    child_id = kwargs.get("child_id")
    detail = f" child_id={child_id}" if child_id is not None else ""
    try:
        requires_oidc = _metastore_requires_oidc_worker(metastore_id)
    except Exception:
        # Routing runs synchronously at task-publish time; a lookup failure
        # (e.g. a transient DB error) must never break task dispatch. Fall back
        # to the default queue, consistent with the not-found / unknown-loader
        # paths in _metastore_requires_oidc_worker.
        LOG.exception(
            "[route_metastore_task] routing lookup failed for %s (metastore_id=%s%s); "
            "falling back to default queue",
            name,
            metastore_id,
            detail,
        )
        return None
    if requires_oidc:
        LOG.info(
            "[route_metastore_task] %s (metastore_id=%s%s) -> queue=%s",
            name,
            metastore_id,
            detail,
            K8S_ONLY_QUEUE,
        )
        return {"queue": K8S_ONLY_QUEUE}
    # Default-queue routing is the common case for every metastore sync; keep it
    # at DEBUG so INFO carries only the actionable k8s-only routing signal.
    LOG.debug(
        "[route_metastore_task] %s (metastore_id=%s%s) -> queue=celery (default)",
        name,
        metastore_id,
        detail,
    )
    return None


def _metastore_requires_oidc_worker(metastore_id, _seen=None):
    """True if syncing this metastore will connect to a loader that needs an OIDC
    worker (Databricks). Recurses combo children via config only — never
    instantiates a loader (dispatch must stay a cheap metadata read)."""
    from models.admin import QueryMetastore  # local import avoids circular app init

    if _seen is None:
        _seen = set()
    if metastore_id in _seen:
        return False
    _seen.add(metastore_id)

    metastore = QueryMetastore.get(id=metastore_id)
    if not metastore:
        LOG.warning(
            "[route_metastore_task] metastore id=%s not found, routing to default queue",
            metastore_id,
        )
        return False

    loader_by_name = _get_loader_by_name()
    loader_cls = loader_by_name.get(metastore.loader)
    if loader_cls is None:
        LOG.warning(
            "[route_metastore_task] metastore id=%s has unknown loader %r, "
            "routing to default queue",
            metastore_id,
            metastore.loader,
        )
        return False

    combo_cls = loader_by_name.get("ComboMetastoreLoader")
    if combo_cls is not None and issubclass(loader_cls, combo_cls):
        sub_loaders = (metastore.metastore_params or {}).get("sub_loaders", []) or []
        for child in sub_loaders:
            child_id = child.get("metastore_id") if isinstance(child, dict) else None
            if child_id is not None and _metastore_requires_oidc_worker(
                child_id, _seen
            ):
                return True
        return False

    return getattr(loader_cls, "REQUIRES_OIDC_WORKER", False)
