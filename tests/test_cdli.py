"""Tests for the CDLI adapter with mocked HTTP."""
import io
import json
from unittest.mock import MagicMock, patch
import urllib.error

from theosis_ancient_context.adapters.cdli import (
    CDLIAdapter,
    _validate_id,
    _validate_query,
    _artifact_summary,
    _inscription_summary,
)


# ---------------------------------------------------------------------------
# Sample API responses (derived from live probing)
# ---------------------------------------------------------------------------

SAMPLE_SEARCH_RESULT = [
    {
        "id": 1,
        "designation": "CDLI Lexical 000002, ex. 065",
        "excavation_no": "W 06435,a",
        "findspot_comments": "auf H\u00fcgeloberfl\u00e4che in der N\u00e4he des S\u00fcdbaues",
        "findspot_square": "M XVIII,?",
        "museum_no": "VAT 01533",
        "thickness": "18.0",
        "height": "31.0",
        "width": "61.0",
        "dates_referenced": "00.00.00.00",
        "languages": [{"language": {"inline_code": "qpc"}}],
        "genres": [{"genre": {"genre": "Lexical"}}],
        "inscription": {"id": 2309985, "artifact_id": 1},
    }
]

SAMPLE_ARTIFACT_RESULT = [
    {
        "id": 1,
        "designation": "CDLI Lexical 000002, ex. 065",
        "excavation_no": "W 06435,a",
        "findspot_comments": "auf H\u00fcgeloberfl\u00e4che",
        "findspot_square": "M XVIII,?",
        "museum_no": "VAT 01533",
        "thickness": "18.0",
        "height": "31.0",
        "width": "61.0",
        "dates_referenced": "00.00.00.00",
        "languages": [{"id": 1, "artifact_id": 1, "language_id": 16, "language": {"id": 16, "sequence": 1, "language": "undetermined", "inline_code": "qpc"}}],
        "genres": [{"id": 8192, "artifact_id": 1, "genre_id": 4, "genre": {"id": 4, "genre": "Lexical"}}],
        "materials": [{"id": 393353, "artifact_id": 1, "material": {"material": "clay"}}],
        "publications": [],
        "composites": [],
        "inscription": {"id": 2309985, "artifact_id": 1},
    }
]

SAMPLE_INSCRIPTION_RESULT = [
    {
        "id": 2309985,
        "artifact_id": 1,
        "atf": "&P000001 = CDLI Lexical 000002, ex. 065\n#atf: lang qpc\n@tablet\n@obverse\n@column 1\n$ beginning broken\n1'. 1(N01) , [...]\n",
        "is_latest": True,
    }
]


def _mock_response(data, status=200):
    """Create a mock urllib response."""
    resp = MagicMock()
    resp.read.return_value = json.dumps(data).encode("utf-8")
    resp.status = status
    return resp


def _mock_http_error(code, reason="Error"):
    """Create a real urllib HTTPError that can be raised via side_effect."""
    url = "https://cdli.earth/test"
    fp = io.BytesIO(b"")
    return urllib.error.HTTPError(url, code, reason, {}, fp)


# ---------------------------------------------------------------------------
# Validation helper tests
# ---------------------------------------------------------------------------

class TestValidateQuery:
    def test_valid_query(self):
        assert _validate_query("tablet") == "tablet"

    def test_strips_whitespace(self):
        assert _validate_query("  tablet  ") == "tablet"

    def test_empty_returns_none(self):
        assert _validate_query("") is None

    def test_whitespace_only_returns_none(self):
        assert _validate_query("   ") is None

    def test_too_long_returns_none(self):
        assert _validate_query("x" * 501) is None

    def test_max_length_ok(self):
        assert _validate_query("x" * 500) == "x" * 500


class TestValidateId:
    def test_valid_integer(self):
        assert _validate_id("1") == 1

    def test_valid_large_integer(self):
        assert _validate_id("2309985") == 2309985

    def test_p_style(self):
        assert _validate_id("P000001") == 1

    def test_q_style(self):
        assert _validate_id("Q000002") == 2

    def test_zero_returns_none(self):
        assert _validate_id("0") is None

    def test_negative_returns_none(self):
        assert _validate_id("-1") is None

    def test_empty_returns_none(self):
        assert _validate_id("") is None

    def test_alpha_only_returns_none(self):
        assert _validate_id("abc") is None

    def test_too_large_returns_none(self):
        assert _validate_id("999999999") is None

    def test_p_lowercase(self):
        assert _validate_id("p123") == 123


# ---------------------------------------------------------------------------
# Artifact summary tests
# ---------------------------------------------------------------------------

class TestArtifactSummary:
    def test_basic_fields(self):
        art = {"id": 42, "designation": "Test tablet", "museum_no": "M 123"}
        s = _artifact_summary(art)
        assert s["id"] == 42
        assert s["designation"] == "Test tablet"
        assert s["museum_no"] == "M 123"
        assert "cdli.earth" in s["source_url"]

    def test_languages_extracted(self):
        art = {"id": 1, "languages": [{"language": {"inline_code": "akk"}}]}
        s = _artifact_summary(art)
        assert "akk" in s["languages"]

    def test_genres_extracted(self):
        art = {"id": 1, "genres": [{"genre": {"genre": "Administrative"}}]}
        s = _artifact_summary(art)
        assert "Administrative" in s["genres"]

    def test_dimensions(self):
        art = {"id": 1, "height": "10.0", "width": "5.0"}
        s = _artifact_summary(art)
        assert s["height"] == "10.0"
        assert s["width"] == "5.0"


class TestInscriptionSummary:
    def test_basic_fields(self):
        insc = {"id": 2309985, "artifact_id": 1, "atf": "some atf text"}
        s = _inscription_summary(insc)
        assert s["id"] == 2309985
        assert s["artifact_id"] == 1
        assert s["has_atf"] is True
        assert "cdli.earth" in s["source_url"]

    def test_no_atf(self):
        insc = {"id": 2309985, "artifact_id": 1}
        s = _inscription_summary(insc)
        assert "has_atf" not in s


# ---------------------------------------------------------------------------
# Adapter tests with mocked HTTP
# ---------------------------------------------------------------------------

class TestCDLIAdapterAvailable:
    def test_is_available(self):
        adapter = CDLIAdapter()
        assert adapter.is_available() is True


class TestCDLISearch:
    def test_search_invalid_query(self):
        adapter = CDLIAdapter()
        result = adapter.search("")
        assert result.status == "error"
        assert "Invalid" in result.message

    def test_search_long_query(self):
        adapter = CDLIAdapter()
        result = adapter.search("x" * 501)
        assert result.status == "error"

    @patch("urllib.request.urlopen")
    def test_search_ok(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response(SAMPLE_SEARCH_RESULT)
        adapter = CDLIAdapter()
        result = adapter.search("tablet")
        assert result.status == "ok"
        assert len(result.results) == 1
        assert result.results[0]["id"] == 1
        assert result.results[0]["designation"] == "CDLI Lexical 000002, ex. 065"
        assert "cdli.earth" in result.results[0]["source_url"]
        assert "Open access" in result.message

    @patch("urllib.request.urlopen")
    def test_search_respects_limit(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response(SAMPLE_SEARCH_RESULT)
        adapter = CDLIAdapter()
        result = adapter.search("tablet", limit=1)
        assert len(result.results) <= 1

    @patch("urllib.request.urlopen")
    def test_search_upstream_error(self, mock_urlopen):
        mock_urlopen.side_effect = _mock_http_error(500, "Internal Server Error")
        adapter = CDLIAdapter()
        result = adapter.search("tablet")
        assert result.status == "upstream_error"
        assert "500" in result.message

    @patch("urllib.request.urlopen")
    def test_search_network_error(self, mock_urlopen):
        mock_urlopen.side_effect = OSError("Connection refused")
        adapter = CDLIAdapter()
        result = adapter.search("tablet")
        assert result.status == "network_error"
        assert "Connection refused" in result.message

    @patch("urllib.request.urlopen")
    def test_search_unexpected_format(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response({"not": "a list"})
        adapter = CDLIAdapter()
        result = adapter.search("tablet")
        assert result.status == "error"
        assert "Unexpected" in result.message


class TestCDLIGetText:
    def test_get_text_invalid_reference(self):
        adapter = CDLIAdapter()
        result = adapter.get_text("abc")
        assert result.status == "error"
        assert "Invalid" in result.message

    def test_get_text_empty_reference(self):
        adapter = CDLIAdapter()
        result = adapter.get_text("")
        assert result.status == "error"

    @patch("urllib.request.urlopen")
    def test_get_text_ok(self, mock_urlopen):
        # First call: artifact endpoint; second: inscription endpoint
        mock_urlopen.side_effect = [
            _mock_response(SAMPLE_ARTIFACT_RESULT),
            _mock_response(SAMPLE_INSCRIPTION_RESULT),
        ]
        adapter = CDLIAdapter()
        result = adapter.get_text("1")
        assert result.status == "ok"
        assert "P000001" in result.text
        assert "@tablet" in result.text
        assert result.metadata["inscription_id"] == 2309985
        assert result.metadata["artifact_id"] == 1
        assert "Open access" in result.message

    @patch("urllib.request.urlopen")
    def test_get_text_artifact_not_found(self, mock_urlopen):
        mock_urlopen.side_effect = _mock_http_error(404, "Not Found")
        adapter = CDLIAdapter()
        result = adapter.get_text("999999")
        assert result.status == "not_found"

    @patch("urllib.request.urlopen")
    def test_get_text_artifact_empty_list(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response([])
        adapter = CDLIAdapter()
        result = adapter.get_text("1")
        assert result.status == "not_found"

    @patch("urllib.request.urlopen")
    def test_get_text_no_inscription(self, mock_urlopen):
        art_no_insc = [{"id": 1, "designation": "Test"}]
        mock_urlopen.return_value = _mock_response(art_no_insc)
        adapter = CDLIAdapter()
        result = adapter.get_text("1")
        assert result.status == "not_found"
        assert "no inscription" in result.message

    @patch("urllib.request.urlopen")
    def test_get_text_inscription_no_atf(self, mock_urlopen):
        art = [{"id": 1, "inscription": {"id": 100, "artifact_id": 1}}]
        insc_no_atf = [{"id": 100, "artifact_id": 1}]
        mock_urlopen.side_effect = [_mock_response(art), _mock_response(insc_no_atf)]
        adapter = CDLIAdapter()
        result = adapter.get_text("1")
        assert result.status == "ok"
        assert result.text == ""
        assert "no ATF text" in result.message

    @patch("urllib.request.urlopen")
    def test_get_text_p_style_reference(self, mock_urlopen):
        mock_urlopen.side_effect = [
            _mock_response(SAMPLE_ARTIFACT_RESULT),
            _mock_response(SAMPLE_INSCRIPTION_RESULT),
        ]
        adapter = CDLIAdapter()
        result = adapter.get_text("P000001")
        assert result.status == "ok"
        assert "@tablet" in result.text

    @patch("urllib.request.urlopen")
    def test_get_text_inscription_network_error(self, mock_urlopen):
        mock_urlopen.side_effect = [
            _mock_response(SAMPLE_ARTIFACT_RESULT),
            OSError("timeout"),
        ]
        adapter = CDLIAdapter()
        result = adapter.get_text("1")
        assert result.status == "network_error"


class TestCDLIGetMetadata:
    def test_get_metadata_invalid_reference(self):
        adapter = CDLIAdapter()
        result = adapter.get_metadata("abc")
        assert result.status == "error"
        assert "Invalid" in result.message

    @patch("urllib.request.urlopen")
    def test_get_metadata_ok(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response(SAMPLE_ARTIFACT_RESULT)
        adapter = CDLIAdapter()
        result = adapter.get_metadata("1")
        assert result.status == "ok"
        assert result.metadata["id"] == 1
        assert result.metadata["designation"] == "CDLI Lexical 000002, ex. 065"
        assert "materials" in result.metadata
        assert "Open access" in result.message

    @patch("urllib.request.urlopen")
    def test_get_metadata_not_found(self, mock_urlopen):
        mock_urlopen.side_effect = _mock_http_error(404, "Not Found")
        adapter = CDLIAdapter()
        result = adapter.get_metadata("999999")
        assert result.status == "not_found"

    @patch("urllib.request.urlopen")
    def test_get_metadata_empty_list(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response([])
        adapter = CDLIAdapter()
        result = adapter.get_metadata("1")
        assert result.status == "not_found"

    @patch("urllib.request.urlopen")
    def test_get_metadata_upstream_error(self, mock_urlopen):
        mock_urlopen.side_effect = _mock_http_error(503, "Service Unavailable")
        adapter = CDLIAdapter()
        result = adapter.get_metadata("1")
        assert result.status == "upstream_error"
        assert "503" in result.message

    @patch("urllib.request.urlopen")
    def test_get_metadata_network_error(self, mock_urlopen):
        mock_urlopen.side_effect = OSError("DNS failure")
        adapter = CDLIAdapter()
        result = adapter.get_metadata("1")
        assert result.status == "network_error"
        assert "DNS failure" in result.message

    @patch("urllib.request.urlopen")
    def test_get_metadata_p_style_reference(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response(SAMPLE_ARTIFACT_RESULT)
        adapter = CDLIAdapter()
        result = adapter.get_metadata("P000001")
        assert result.status == "ok"
        assert result.metadata["id"] == 1


# ---------------------------------------------------------------------------
# Provenance envelope tests
# ---------------------------------------------------------------------------

class TestCDLIProvenance:
    def test_search_provenance(self):
        adapter = CDLIAdapter()
        result = adapter.search("")
        assert result.provenance.corpus_id == "cdli"
        assert result.provenance.licence == "Open access"

    @patch("urllib.request.urlopen")
    def test_get_text_provenance(self, mock_urlopen):
        mock_urlopen.side_effect = [
            _mock_response(SAMPLE_ARTIFACT_RESULT),
            _mock_response(SAMPLE_INSCRIPTION_RESULT),
        ]
        adapter = CDLIAdapter()
        result = adapter.get_text("1")
        assert result.provenance.corpus_id == "cdli"
        assert result.provenance.licence == "Open access"

    @patch("urllib.request.urlopen")
    def test_get_metadata_provenance(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response(SAMPLE_ARTIFACT_RESULT)
        adapter = CDLIAdapter()
        result = adapter.get_metadata("1")
        assert result.provenance.corpus_id == "cdli"
        assert result.provenance.licence == "Open access"


# ---------------------------------------------------------------------------
# Custom base_url / timeout tests
# ---------------------------------------------------------------------------

class TestCDLIConfig:
    def test_custom_base_url(self):
        adapter = CDLIAdapter(base_url="https://custom.example.com")
        assert adapter._base_url == "https://custom.example.com"

    def test_trailing_slash_stripped(self):
        adapter = CDLIAdapter(base_url="https://custom.example.com/")
        assert adapter._base_url == "https://custom.example.com"

    def test_custom_timeout(self):
        adapter = CDLIAdapter(timeout=30)
        assert adapter._timeout == 30
