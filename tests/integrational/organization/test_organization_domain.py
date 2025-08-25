from uuid import uuid4

from easy_diagrams.domain.organization import Organization
from easy_diagrams.domain.organization import OrganizationEdit
from easy_diagrams.domain.organization import OrganizationID
from easy_diagrams.domain.organization import OrganizationListItem


def test_organization_id_creation():
    """Test OrganizationID creation."""
    org_uuid = uuid4()
    org_id = OrganizationID(org_uuid)
    assert org_id.value == org_uuid


def test_organization_creation():
    """Test Organization creation."""
    org_id = OrganizationID(uuid4())
    org = Organization(id=org_id, name="Test Organization")
    assert org.id == org_id
    assert org.name == "Test Organization"


def test_organization_edit_creation():
    """Test OrganizationEdit creation."""
    edit = OrganizationEdit(name="Updated Name")
    assert edit.name == "Updated Name"


def test_organization_edit_default():
    """Test OrganizationEdit with default values."""
    edit = OrganizationEdit()
    assert edit.name is None


def test_organization_list_item_creation():
    """Test OrganizationListItem creation."""
    org_id = OrganizationID(uuid4())
    item = OrganizationListItem(id=org_id, name="List Item")
    assert item.id == org_id
    assert item.name == "List Item"
