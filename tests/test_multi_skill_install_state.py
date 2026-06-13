from pathlib import Path

from skill_deployment.evidence import write_json, write_text
from skill_deployment.install_state import install_skill_package, load_active_pointer, resolve_installed_skill
from skill_deployment.schemas import SkillPackage


def write_package(root: Path, skill_id: str, version: str) -> Path:
    package_dir = root / skill_id
    write_json(
        package_dir / "manifest.json",
        {
            "skill_id": skill_id,
            "available_versions": [version],
            "default_version": version,
        },
    )
    skill = SkillPackage(
        skill_id=skill_id,
        version=version,
        task_family=skill_id,
        capabilities=("UPLOAD_PATH_ISOLATION",),
    )
    write_text(package_dir / "versions" / version / "SKILL.md", f"# {skill_id} {version}\n")
    write_json(package_dir / "versions" / version / "manifest.json", skill.to_dict())
    return package_dir


def test_per_skill_active_pointer_preserves_multiple_installed_skills(tmp_path: Path) -> None:
    source_root = tmp_path / "sources"
    secure_dir = write_package(source_root, "secure_code_review", "v2")
    patch_dir = write_package(source_root, "software_patch_review", "v1")

    install_skill_package(tmp_path, secure_dir, requested_version="v2")
    install_skill_package(tmp_path, patch_dir, requested_version="v1")

    secure_pointer = load_active_pointer(tmp_path, "secure_code_review")
    patch_pointer = load_active_pointer(tmp_path, "software_patch_review")
    legacy_pointer = load_active_pointer(tmp_path)

    assert secure_pointer["active_version"] == "v2"
    assert patch_pointer["active_version"] == "v1"
    assert legacy_pointer["skill_id"] == "software_patch_review"
    assert resolve_installed_skill(tmp_path, "secure_code_review")["skill_package"].version == "v2"
    assert resolve_installed_skill(tmp_path, "software_patch_review")["skill_package"].version == "v1"
