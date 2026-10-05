import numpy as np
import pytest

from sonore_sketch import page, tracks

from test_tracks import DOCUMENT

PAGE = {
    "app": "sonore-sketch", "version": 2, "sonore": "0.5.0",
    "duration": DOCUMENT["duration"], "fs": DOCUMENT["fs"], "tab": "tracks",
    "tracks": {"mode": "klatt", "params": DOCUMENT["params"]},
}


def test_a_trackdraw_document_upgrades_to_a_page_document():
    assert page.upgrade(DOCUMENT) == PAGE


def test_the_tracks_state_of_a_page_document_is_the_trackdraw_document():
    assert page.tab_state(PAGE, "tracks") == DOCUMENT


def test_a_saved_page_sounds_as_its_tab_does():
    np.testing.assert_array_equal(page.synthesize(PAGE).data, tracks.synthesize(DOCUMENT).data)


@pytest.mark.parametrize(
    "document, message",
    [({"app": "sonore-sketch", "version": 3}, "version 2"), ({"hello": 1}, "not a sonore sketch"), ({**PAGE, "tab": "nope"}, "unknown tab")],
)
def test_other_documents_are_refused(document, message):
    with pytest.raises(ValueError, match=message):
        page.tab_state(document)
