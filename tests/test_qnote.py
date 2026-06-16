import pytest
from pathlib import Path

from qnote.models import Note
from qnote.storage import NoteStorage


@pytest.fixture
def storage(tmp_path):
    return NoteStorage(db_path=tmp_path / "test.db")


def test_add_note(storage):
    note = storage.add_note(Note(content="Hello world", tags=["test"]))
    assert note.id > 0
    assert note.content == "Hello world"


def test_get_note(storage):
    saved = storage.add_note(Note(content="Get me", tags=["demo"]))
    fetched = storage.get_note(saved.id)
    assert fetched is not None
    assert fetched.content == "Get me"
    assert fetched.tags == ["demo"]


def test_get_note_not_found(storage):
    assert storage.get_note(9999) is None


def test_list_notes(storage):
    storage.add_note(Note(content="Note 1"))
    storage.add_note(Note(content="Note 2", tags=["work"]))
    assert len(storage.list_notes()) == 2


def test_list_notes_by_tag(storage):
    storage.add_note(Note(content="Work note", tags=["work"]))
    storage.add_note(Note(content="Personal note", tags=["personal"]))
    work_notes = storage.list_notes(tag="work")
    assert len(work_notes) == 1
    assert work_notes[0].content == "Work note"


def test_search_notes(storage):
    storage.add_note(Note(content="Python is great"))
    storage.add_note(Note(content="JavaScript rocks"))
    results = storage.search_notes("Python")
    assert len(results) == 1
    assert "Python" in results[0].content


def test_delete_note(storage):
    note = storage.add_note(Note(content="Delete me"))
    assert storage.delete_note(note.id) is True
    assert storage.get_note(note.id) is None


def test_delete_nonexistent(storage):
    assert storage.delete_note(9999) is False


def test_get_all_tags(storage):
    storage.add_note(Note(content="A", tags=["python", "cli"]))
    storage.add_note(Note(content="B", tags=["python"]))
    storage.add_note(Note(content="C", tags=["cli"]))
    tag_dict = dict(storage.get_all_tags())
    assert tag_dict["python"] == 2
    assert tag_dict["cli"] == 2


def test_export_all(storage):
    storage.add_note(Note(content="Note 1"))
    storage.add_note(Note(content="Note 2"))
    all_notes = storage.export_all()
    assert len(all_notes) == 2
    assert all_notes[0].id < all_notes[1].id


def test_note_multiple_tags(storage):
    note = storage.add_note(Note(content="Multi", tags=["a", "b", "c"]))
    fetched = storage.get_note(note.id)
    assert fetched.tags == ["a", "b", "c"]


def test_list_notes_limit(storage):
    for i in range(10):
        storage.add_note(Note(content=f"Note {i}"))
    assert len(storage.list_notes(limit=5)) == 5
