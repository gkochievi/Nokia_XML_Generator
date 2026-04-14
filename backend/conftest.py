import os
import shutil
import tempfile
import pytest


@pytest.fixture()
def app():
    """Create a Flask application configured for testing."""
    # Create temp dirs so tests don't touch real data
    tmp = tempfile.mkdtemp()
    upload_dir = os.path.join(tmp, 'uploads')
    generated_dir = os.path.join(tmp, 'generated')
    example_dir = os.path.join(tmp, 'example_files')
    os.makedirs(upload_dir)
    os.makedirs(generated_dir)
    os.makedirs(example_dir)
    os.makedirs(os.path.join(example_dir, 'East'))
    os.makedirs(os.path.join(example_dir, 'West'))
    os.makedirs(os.path.join(example_dir, 'IP'))

    from app import app as flask_app
    flask_app.config.update({
        'TESTING': True,
        'UPLOAD_FOLDER': upload_dir,
        'GENERATED_FOLDER': generated_dir,
        'EXAMPLE_FILES_FOLDER': example_dir,
    })

    yield flask_app

    shutil.rmtree(tmp, ignore_errors=True)


@pytest.fixture()
def client(app):
    """Flask test client."""
    return app.test_client()


@pytest.fixture()
def example_dir(app):
    """Path to the test example_files directory."""
    return app.config['EXAMPLE_FILES_FOLDER']


@pytest.fixture()
def generated_dir(app):
    """Path to the test generated directory."""
    return app.config['GENERATED_FOLDER']


# ---------------------------------------------------------------------------
# Minimal Nokia XML fixtures (in-memory strings)
# ---------------------------------------------------------------------------

MINIMAL_NOKIA_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<raml xmlns="raml21.xsd" version="2.1">
  <cmData type="plan" scope="all" id="1234">
    <header>
      <log action="create" dateTime="2026-01-01T00:00:00Z"/>
    </header>
    <managedObject class="com.nokia.srbts:MRBTS" distName="MRBTS-12345" operation="create">
      <p name="btsName">Test_Station_Alpha</p>
    </managedObject>
    <managedObject class="com.nokia.srbts:WNBTS" distName="MRBTS-12345/WNBTS-12345" operation="create">
      <list name="cPlaneList">
        <item>
          <p name="sctpPortMin">2905</p>
        </item>
      </list>
    </managedObject>
    <managedObject class="NOKLTE:LNBTS" distName="MRBTS-12345/LNBTS-12345" operation="create">
      <p name="lnBtsId">12345</p>
    </managedObject>
    <managedObject class="NOKLTE:LNCEL" distName="MRBTS-12345/LNBTS-12345/LNCEL-11" operation="create">
      <p name="phyCellId">100</p>
      <p name="tac">5001</p>
      <p name="eutraCelId">11</p>
    </managedObject>
    <managedObject class="NOKLTE:LNCEL" distName="MRBTS-12345/LNBTS-12345/LNCEL-12" operation="create">
      <p name="phyCellId">101</p>
      <p name="tac">5001</p>
      <p name="eutraCelId">12</p>
    </managedObject>
    <managedObject class="NOKLTE:LNCEL_FDD" distName="MRBTS-12345/LNBTS-12345/LNCEL-11/LNCEL_FDD-11" operation="create">
      <p name="rootSeqIndex">620</p>
    </managedObject>
    <managedObject class="NOKLTE:LNCEL_FDD" distName="MRBTS-12345/LNBTS-12345/LNCEL-12/LNCEL_FDD-12" operation="create">
      <p name="rootSeqIndex">350</p>
    </managedObject>
    <managedObject class="com.nokia.srbts.nrbts:NRBTS" distName="MRBTS-12345/NRBTS-12345" operation="create">
      <p name="nrBtsName">Test_Station_Alpha</p>
    </managedObject>
    <managedObject class="com.nokia.srbts.nrbts:NRCELL" distName="MRBTS-12345/NRBTS-12345/NRCELL-111" operation="create">
      <p name="physCellId">200</p>
    </managedObject>
    <managedObject class="com.nokia.srbts.nrbts:NRCELL" distName="MRBTS-12345/NRBTS-12345/NRCELL-112" operation="create">
      <p name="physCellId">201</p>
    </managedObject>
  </cmData>
</raml>
"""

MINIMAL_NOKIA_XML_NO_NAMESPACE = """\
<?xml version="1.0" encoding="UTF-8"?>
<raml version="2.1">
  <cmData type="plan" scope="all" id="9999">
    <header>
      <log action="create" dateTime="2026-01-01T00:00:00Z"/>
    </header>
    <managedObject class="com.nokia.srbts:MRBTS" distName="MRBTS-99999" operation="create">
      <p name="btsName">NoNS_Station</p>
    </managedObject>
  </cmData>
</raml>
"""


@pytest.fixture()
def sample_xml_content():
    """Return minimal Nokia XML string."""
    return MINIMAL_NOKIA_XML


@pytest.fixture()
def sample_xml_file(tmp_path):
    """Write minimal Nokia XML to a temp file, return path."""
    p = tmp_path / "test_station.xml"
    p.write_text(MINIMAL_NOKIA_XML, encoding='utf-8')
    return str(p)


@pytest.fixture()
def sample_xml_no_ns_file(tmp_path):
    """Write Nokia XML without default namespace to a temp file."""
    p = tmp_path / "test_no_ns.xml"
    p.write_text(MINIMAL_NOKIA_XML_NO_NAMESPACE, encoding='utf-8')
    return str(p)
