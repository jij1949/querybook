import pytest

from metastore_plugin.eg_shared.enrichment_mixin import EgEnrichmentMixin


class DatabricksLoader(EgEnrichmentMixin):
    """Minimal concrete loader that declares the Databricks catalog type."""
    CATALOG_TYPE = "databricks"


class GlueLoader(EgEnrichmentMixin):
    """Minimal concrete loader that declares the Glue catalog type."""
    CATALOG_TYPE = "glue"


class UntypedLoader(EgEnrichmentMixin):
    """Loader that does not declare a catalog type (inherits CATALOG_TYPE=None)."""
    pass


class UnknownTypeLoader(EgEnrichmentMixin):
    """Loader declaring an unrecognized catalog type."""
    CATALOG_TYPE = "some_unknown_type"


@pytest.fixture
def databricks_loader():
    return DatabricksLoader.__new__(DatabricksLoader)


@pytest.fixture
def glue_loader():
    return GlueLoader.__new__(GlueLoader)


def test_databricks_loader_produces_databricks_tag(databricks_loader):
    tags, props = databricks_loader._process_catalog_type()
    assert len(tags) == 1
    assert tags[0].name == "Catalog Type: Databricks"
    assert tags[0].type == "Catalog Type"
    assert tags[0].color == "databricks-red"
    assert props["catalog_type"] == "databricks"
    assert "Databricks" in tags[0].description


def test_glue_loader_produces_glue_tag(glue_loader):
    tags, props = glue_loader._process_catalog_type()
    assert len(tags) == 1
    assert tags[0].name == "Catalog Type: AWS Glue"
    assert tags[0].color == "glue-purple"
    assert props["catalog_type"] == "glue"


def test_loader_without_catalog_type_returns_empty():
    loader = UntypedLoader.__new__(UntypedLoader)
    tags, props = loader._process_catalog_type()
    assert tags == []
    assert props == {}


def test_loader_with_unknown_catalog_type_returns_empty():
    loader = UnknownTypeLoader.__new__(UnknownTypeLoader)
    tags, props = loader._process_catalog_type()
    assert tags == []
    assert props == {}


def test_databricks_tag_meta_has_correct_fields(databricks_loader):
    tags, _ = databricks_loader._process_catalog_type()
    meta = tags[0].meta
    assert meta["rank"] == 35
    assert meta["admin"] is True
    assert meta["catalog_type"] == "databricks"


def test_glue_tag_meta_has_catalog_type_key(glue_loader):
    tags, _ = glue_loader._process_catalog_type()
    assert tags[0].meta["catalog_type"] == "glue"
