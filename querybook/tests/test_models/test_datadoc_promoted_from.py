from models.datadoc import DataDoc
from models.environment import Environment


def test_datadoc_promoted_from_id_defaults_none(db_engine):
    env = Environment.create(fields={"name": "promoted-from-defaults-env"})
    doc = DataDoc.create(fields={"environment_id": env.id, "title": "src"})
    assert doc.promoted_from_id is None
    assert "promoted_from_id" in doc.to_dict()


def test_datadoc_promoted_from_id_settable(db_engine):
    corp = Environment.create(fields={"name": "promoted-from-corp-env"})
    dw = Environment.create(fields={"name": "promoted-from-dw-env"})
    source = DataDoc.create(fields={"environment_id": corp.id, "title": "corp doc"})
    promoted = DataDoc.create(
        fields={
            "environment_id": dw.id,
            "title": "dw doc",
            "promoted_from_id": source.id,
        }
    )
    assert promoted.promoted_from_id == source.id
    assert promoted.to_dict()["promoted_from_id"] == source.id
