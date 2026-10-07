from pathlib import Path

from app.core.paths import adopt_legacy_data_dir


def test_earlier_data_folder_is_moved_to_the_new_name(tmp_path: Path) -> None:
    legacy = tmp_path / "LocalResearchAssistant"
    (legacy / "database").mkdir(parents=True)
    (legacy / "database" / "local_research.db").write_text("data")
    target = tmp_path / "Loci"

    assert adopt_legacy_data_dir(target, [legacy]) == target
    assert (target / "database" / "local_research.db").read_text() == "data"
    assert not legacy.exists()


def test_existing_new_folder_is_kept(tmp_path: Path) -> None:
    legacy = tmp_path / "LocalResearchAssistant"
    legacy.mkdir()
    target = tmp_path / "Loci"
    target.mkdir()

    assert adopt_legacy_data_dir(target, [legacy]) == target
    assert legacy.exists()


def test_fresh_install_uses_the_new_folder(tmp_path: Path) -> None:
    target = tmp_path / "Loci"
    assert adopt_legacy_data_dir(target, [tmp_path / "LocalResearchAssistant"]) == target


def test_old_folder_is_used_when_it_cannot_be_moved(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    legacy = tmp_path / "LocalResearchAssistant"
    legacy.mkdir()

    def refuse(self: Path, target: Path) -> Path:
        raise PermissionError("in use")

    monkeypatch.setattr(Path, "rename", refuse)

    assert adopt_legacy_data_dir(tmp_path / "Loci", [legacy]) == legacy
