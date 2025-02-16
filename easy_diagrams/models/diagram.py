import random
import string
import time
from datetime import datetime

from sqlalchemy import BigInteger
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import BYTEA
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from .meta import Base


def _gen_diagram_id() -> str:
    """Generate a unique identifier for the diagram."""
    return "".join(random.choices(string.ascii_letters + string.digits, k=32))


def _gen_code_version() -> int:
    """Generate a code version based on the current time and a random number.
    Returns a number smaller than 2^63 so it can be stored in a bigint column.
    """
    return int(time.time() * 1000)


class DiagramTable(Base):
    """Diagram model.

    Diagrams are stored in the database. They have a code and an image. The code is a textual representation of the diagram that can be used to generate the image. The image is a binary representation of the diagram that can be displayed to the user.

    The version fields `code_version` and `image_version` are used to track the changes in the code and image. `code_version` is generated automatically when code is set. The version is a number that is unique for each change of the code. If `image_version` is not the same as `code_version` it means that the image is outdated and should be regenerated or the code is invalid.

    The `code_is_valid` field is used to track if the code is valid. If the code is invalid the image can't be generated. The field can be set only after the code rendering is attempted.
    """

    __tablename__ = "diagrams"
    #: Unique publicly exposed identifier for the diagram
    id = Column(String(32), default=_gen_diagram_id, primary_key=True)

    #: Title of the diagram
    title = Column(String(300), index=True, nullable=True)

    #: Whatever the diagram is public
    is_public = Column(Boolean, nullable=False, default=False)

    #: When this user was created
    created_at = Column(DateTime, index=True, default=datetime.now)

    #: When the user data was updated last time
    updated_at = Column(
        DateTime, index=True, onupdate=datetime.now, default=datetime.now
    )

    # user relationship
    user_id = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    user = relationship("User", back_populates="diagrams")

    # code
    _code_version = Column("code_version", BigInteger, nullable=True)
    _code = Column("code", String(10_240), nullable=True)  # 10K characters limit
    _code_is_valid = Column("code_is_valid", Boolean, nullable=True)

    # image
    _image_version = Column("image_version", BigInteger, nullable=True)
    _image = Column("image", BYTEA, nullable=True)

    @hybrid_property
    def code(self):
        """The code of the diagram. Setting the code also will set the :property:`code_is_valid` to `None` and :property:`code_version` to new version, see :function:`_gen_code_version`."""
        return self._code

    @code.inplace.setter
    def _code_setter(self, value):
        self._code = value
        self._code_is_valid = None
        self._code_version = _gen_code_version()

    @hybrid_property
    def code_version(self):
        """The version of the code of the diagram. This is generated when the code is set and can't be set manually."""
        return self._code_version

    @hybrid_property
    def code_is_valid(self):
        return self._code_is_valid

    @code_is_valid.setter
    def code_is_valid(self, value):
        if value is not False:
            raise ValueError("By hand setting code_is_valid is allowed only to False.")
        self._code_is_valid = value

    @hybrid_property
    def image(self):
        """The image of the diagram. For setting the image see :function:`set_image`."""
        return self._image

    @hybrid_property
    def image_version(self):
        """The version of the image of the diagram. For setting the image see :function:`set_image`."""
        return self._image_version

    def set_image(self, image, version):
        """Set the image of the diagram and its version based on the :property:`code_version`.
        Function also sets the :property:`code_is_valid` to `True`.
        """
        self._image = image
        self._image_version = version
        self._code_is_valid = True
