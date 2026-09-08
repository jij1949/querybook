from models.datadoc import DataDoc
from models.environment import Environment


def test_summary_dict_omits_meta(db_engine):
    env = Environment.create(fields={"name": "summary-dict-env"})
    doc = DataDoc.create(
        fields={
            "environment_id": env.id,
            "title": "doc with a huge variable",
            "_meta": {
                "variables": [
                    {"name": "big", "value": "x" * 100000, "type": "string"}
                ]
            },
        }
    )

    full_dict = doc.to_dict()
    summary_dict = doc.to_summary_dict()

    assert "meta" in full_dict
    assert "meta" not in summary_dict
    # Everything else the sidebar relies on is still there
    assert summary_dict["id"] == doc.id
    assert summary_dict["title"] == "doc with a huge variable"
    assert set(summary_dict) == set(full_dict) - {"meta"}
