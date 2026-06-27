from expert_skill_system.core.schema_catalog import SCHEMAS, export_schemas


def test_schema_catalog_is_versioned_strict_and_exportable(tmp_path) -> None:
    assert {
        "active_binding.v1",
        "artifact_ref.v1",
        "compiler_stage_result.v1",
        "execution_envelope.v1",
        "evidence_unit.v1",
        "knowledge_ir.v1",
        "knowledge_projection.v1",
        "release_bundle.v1",
        "skill_ir.v1",
        "source_ref.v1",
    }.issubset(SCHEMAS)
    assert all(schema["additionalProperties"] is False for schema in SCHEMAS.values())
    paths = export_schemas(tmp_path)
    assert len(paths) == len(SCHEMAS)
    assert all(path.read_text(encoding="utf-8").endswith("\n") for path in paths)
