from pydantic import BaseModel, Field, model_validator
from enum import Enum
from typing import List, Dict, Any, Optional, Literal, Union, ForwardRef
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Literal, ForwardRef
import uuid
from datetime import datetime

# --- Utility Models ---
# --- Enum for Range.Type ---

class RangeType(str, Enum):
    RANGE_TYPE_UNSPECIFIED = "RANGE_TYPE_UNSPECIFIED"
    FIXED_RANGE = "FIXED_RANGE"
    FROM_START_INDEX = "FROM_START_INDEX"
    ALL = "ALL"

#class RgbColor(BaseModel):
#    red: float = 0.0
#    green: float = 0.0
#    blue: float = 0.0

# --- Range Model with validation ---

class RgbColor(BaseModel):
    red: float = 0.0
    green: float = 0.0
    blue: float = 0.0
    
class Range(BaseModel):
    startIndex: Optional[int] = None
    endIndex: Optional[int] = None
    type: RangeType

    @model_validator(mode="after")
    def validate_indices(self):
        start, end, rtype = self.startIndex, self.endIndex, self.type

        if rtype == "RANGE_TYPE_UNSPECIFIED":
            raise ValueError("RangeType must not be RANGE_TYPE_UNSPECIFIED.")

        if rtype == "FIXED_RANGE":
            if start is None or end is None:
                raise ValueError("Both startIndex and endIndex must be specified for FIXED_RANGE.")
        elif rtype == "FROM_START_INDEX":
            if start is None:
                raise ValueError("startIndex must be specified for FROM_START_INDEX.")
            if end is not None:
                raise ValueError("endIndex must not be specified for FROM_START_INDEX.")
        elif rtype == "ALL":
            if start is not None or end is not None:
                raise ValueError("Neither startIndex nor endIndex may be specified for ALL.")

        return self


from typing import Dict, Any, Optional, List, Union
from pydantic import BaseModel
from enum import Enum
from pydantic import root_validator, ValidationError
from pydantic import BaseModel, field_validator, model_validator
from typing import Optional, List
from enum import Enum

# --- Enums (as Literals) ---
Unit = Literal["UNIT_UNSPECIFIED","EMU", "PT"]

PropertyState = Literal["RENDERED", "NOT_RENDERED", "INHERIT"]

ThemeColorType = Literal["THEME_COLOR_TYPE_UNSPECIFIED", "DARK1",
                         "LIGHT1", "DARK2", "LIGHT2", "ACCENT1",
                         "ACCENT2", "ACCENT3", "ACCENT4", "ACCENT5",
                         "ACCENT6", "HYPERLINK", "FOLLOWED_HYPERLINK",
                         "TEXT1", "BACKGROUND1", "TEXT2", "BACKGROUND2"]
# --- Pydantic Models ---

class Dimension(BaseModel):
    magnitude: float
    unit: str # e.g., "PT", "EMU"

class Transform(BaseModel):
    scaleX: Optional[float] = 1.0
    scaleY: Optional[float] = 1.0
    translateX: Optional[float] = 0.0
    translateY: Optional[float] = 0.0
    unit: Optional[str] = "PT"

class FontSize(BaseModel):
    magnitude: float
    unit: str

class OpaqueColor(BaseModel):
    rgbColor: Optional[RgbColor] = None
    themeColor: Optional[ThemeColorType] = None

class OptionalColor(BaseModel):
    opaqueColor: Optional[OpaqueColor] = None

class BaselineOffset(str, Enum):
    BASELINE_OFFSET_UNSPECIFIED = "BASELINE_OFFSET_UNSPECIFIED"
    NONE = "NONE"
    SUPERSCRIPT = "SUPERSCRIPT"
    SUBSCRIPT = "SUBSCRIPT"

class WeightedFontFamily(BaseModel):
    fontFamily: str
    weight: int

# --- Enum for RelativeSlideLink ---

class RelativeSlideLink(str, Enum):
    RELATIVE_SLIDE_LINK_UNSPECIFIED = "RELATIVE_SLIDE_LINK_UNSPECIFIED"
    NEXT_SLIDE = "NEXT_SLIDE"
    PREVIOUS_SLIDE = "PREVIOUS_SLIDE"
    FIRST_SLIDE = "FIRST_SLIDE"
    LAST_SLIDE = "LAST_SLIDE"


# --- Link Model ---

class Link(BaseModel):
    url: Optional[str] = None
    relativeLink: Optional[RelativeSlideLink] = None
    pageObjectId: Optional[str] = None
    slideIndex: Optional[int] = None

    def validate_union_exclusivity(self) -> None:
        """
        Ensures only one of the union fields is set.
        """
        set_fields = [field for field in ["url", "relativeLink", "pageObjectId", "slideIndex"]
                      if getattr(self, field) is not None]
        if len(set_fields) > 1:
            raise ValueError(f"Only one of url, relativeLink, pageObjectId, or slideIndex may be set, "
                             f"but got: {set_fields}")

    def __init__(self, **data):
        super().__init__(**data)
        self.validate_union_exclusivity()

class TextStyle(BaseModel):
    # Add more text style properties as needed for simulation (e.g., bold, italic, underline, color)
    backgroundColor: Optional[OptionalColor] = None
    foregroundColor: Optional[OptionalColor] = None
    bold: Optional[bool] = None
    italic: Optional[bool] = None
    fontFamily: Optional[str] = None
    fontSize: Optional[Dimension] = None
    link: Optional[Link] = None
    baselineOffset: Optional[BaselineOffset] = None
    smallCaps: Optional[bool] = None
    strikethrough: Optional[bool] = None
    underline: Optional[bool] = None
    weightedFontFamily: Optional[WeightedFontFamily] = None


class TextRun(BaseModel):
    content: Optional[str] = None
    style: Optional[TextStyle] = None

class Alignment(str, Enum):
    ALIGNMENT_UNSPECIFIED = "ALIGNMENT_UNSPECIFIED"
    START = "START"
    END = "END"
    CENTER = "CENTER"
    JUSTIFIED = "JUSTIFIED"
    
class TextDirection(str, Enum):
    TEXT_DIRECTION_UNSPECIFIED = "TEXT_DIRECTION_UNSPECIFIED"
    LEFT_TO_RIGHT = "LEFT_TO_RIGHT"
    RIGHT_TO_LEFT = "RIGHT_TO_LEFT"

class SpacingMode(str, Enum):
    SPACING_MODE_UNSPECIFIED = "SPACING_MODE_UNSPECIFIED"
    NEVER_COLLAPSE = "NEVER_COLLAPSE"
    COLLAPSE_LISTS = "COLLAPSE_LISTS"

class ParagraphStyle(BaseModel):
    lineSpacing: Optional[float] = None
    alignment: Optional[Alignment] = None
    indentStart: Optional[Dimension] = None
    indentEnd: Optional[Dimension] = None
    spaceAbove: Optional[Dimension] = None
    spaceBelow: Optional[Dimension] = None
    indentFirstLine: Optional[Dimension] = None
    direction: Optional[TextDirection] = None
    spacingMode: Optional[SpacingMode] = None
    

class Bullet(BaseModel):
    listId: Optional[str] = None
    nestingLevel: Optional[int] = None
    glyph: Optional[str] = None
    bulletStyle: Optional[TextStyle] = None

class ParagraphMarker(BaseModel):
    style: Optional[ParagraphStyle] = None
    bullet: Optional[Bullet] = None

class AutoText(BaseModel):
    text: Optional[str] = None

class TextElement(BaseModel):
    # Represents a segment of text within a shape.
    # In Google Slides API, this can be textRun, paragraphMarker, autoText.
    textRun: Optional[TextRun] = None
    startIndex: Optional[int] = None
    endIndex: Optional[int] = None
    paragraphMarker: Optional[ParagraphMarker] = None
    autoText: Optional[AutoText] = None


    @model_validator(mode="after")
    def validate_union_exclusivity(self):
        """
        Ensures only one of the union fields is set.
        """
        set_fields = [field for field in ["textRun", "paragraphMarker", "autoText"]
                      if getattr(self, field) is not None]
        if len(set_fields) > 1:
            raise ValueError(f"Only one of textRun, paragraphMarker, or autoText may be set, "
                             f"but got: {set_fields}")
        return self


class TextContent(BaseModel):
    textElements: List[TextElement] = Field(default_factory=list)

# --- Page Element Types ---

class Shape(BaseModel):
    shapeType: str
    text: Optional[TextContent] = None

class Image(BaseModel):
    """An image page element."""
    contentUrl: Optional[str] = None
    imageProperties: Optional[Dict[str, Any]] = None
    sourceUrl: Optional[str] = None
    placeholder: Optional[Dict[str, Any]] = None

class Video(BaseModel):
    """A video page element."""
    url: Optional[str] = None
    source: Optional[str] = None  # "YOUTUBE", "DRIVE"
    id: Optional[str] = None
    videoProperties: Optional[Dict[str, Any]] = None

class TableBorderRow(BaseModel):
    """A border along the row of a table."""
    tableBorderCells: Optional[List[Dict[str, Any]]] = None

class TableRow(BaseModel):
    """Properties and contents of each row in a table."""
    height: Optional[Dimension] = None
    tableCells: Optional[List[Dict[str, Any]]] = None
    tableRowProperties: Optional[Dict[str, Any]] = None

class Table(BaseModel):
    """A PageElement kind representing a table."""
    rows: Optional[int] = None
    columns: Optional[int] = None
    tableRows: Optional[List[TableRow]] = None
    horizontalBorderRows: Optional[List[TableBorderRow]] = None
    verticalBorderRows: Optional[List[TableBorderRow]] = None

class Line(BaseModel):
    """A PageElement kind representing a line, connector, or bent connector."""
    lineType: Optional[str] = None  # "TYPE_UNSPECIFIED", "STRAIGHT_CONNECTOR_1", "BENT_CONNECTOR_2", etc.
    lineProperties: Optional[Dict[str, Any]] = None
    lineCategory: Optional[str] = None  # "STRAIGHT", "BENT", "CURVED"

class WordArt(BaseModel):
    """A PageElement kind representing word art."""
    renderedText: Optional[str] = None

class SpeakerSpotlight(BaseModel):
    """A PageElement kind representing a speaker spotlight."""
    speakerSpotlightProperties: Optional[Dict[str, Any]] = None

PageElementRef = ForwardRef("PageElement")

class Group(BaseModel):
    children: List[PageElementRef]
      
class AffineTransform(BaseModel):
    scaleX: Optional[float] = 1.0
    scaleY: Optional[float] = 1.0
    shearX: Optional[float] = 0.0
    shearY: Optional[float] = 0.0
    translateX: Optional[float] = 0.0
    translateY: Optional[float] = 0.0
    unit: Optional[Unit] = "PT"

class Size(BaseModel):
    width: Optional[Dimension] = None
    height: Optional[Dimension] = None

class PageElement(BaseModel):
    objectId: str = Field(default_factory=lambda: str(uuid.uuid4()))
    size: Optional[Size] = None
    transform: Optional[AffineTransform] = None
    title: Optional[str] = None
    description: Optional[str] = None
    shape: Optional[Shape] = None
    image: Optional[Image] = None
    video: Optional[Video] = None
    table: Optional[Table] = None
    line: Optional[Line] = None
    wordArt: Optional[WordArt] = None
    speakerSpotlight: Optional[SpeakerSpotlight] = None
    elementGroup: Optional[Group] = None

class BackgroundColor(BaseModel):
    opaqueColor: Optional[OpaqueColor]

class PageProperties(BaseModel):
    backgroundColor: BackgroundColor

PageModelRef = ForwardRef("PageModel")

class SolidFill(BaseModel):
    color: OpaqueColor
    alpha: Optional[float] = 1.0

class StretchedPictureFill(BaseModel):
    contentUrl: Optional[str] = None
    size: Optional[Size] = None

class PageBackgroundFill(BaseModel):
    propertyState: Optional[PropertyState] = "INHERIT"
    solidFill: Optional[SolidFill] = None
    stretchedPictureFill: Optional[StretchedPictureFill] = None

class ThemeColorPair(BaseModel):
    type: Optional[ThemeColorType] = None
    color: Optional[RgbColor] = None

class ColorScheme(BaseModel):
    colors: Optional[List[ThemeColorPair]] = None

# class PageProperties(BaseModel):
#     pageBackgroundFill: PageBackgroundFill
#     colorScheme: Optional[ColorScheme] = None

#class OpaqueColor(BaseModel):
#    rgbColor: RgbColor

class BackgroundColor(BaseModel):
    opaqueColor: Optional[OpaqueColor]

class PageProperties(BaseModel):
    backgroundColor: BackgroundColor


class SlideProperties(BaseModel):
    layoutObjectId: Optional[str] = None
    notesPage : Optional[PageModelRef] = None
    masterObjectId: Optional[str] = None
    isSkipped: Optional[bool] = False

class NotesPageProperties(BaseModel):
    speakerNotesObjectId: Optional[str]
    # Add more slide specific properties as needed

class MasterProperties(BaseModel):
    displayName: Optional[str] = None

class LayoutProperties(BaseModel):
    masterObjectId: Optional[str] = None
    name: Optional[str] = None
    displayName: Optional[str] = None


class NotesProperties(BaseModel):
    speakerNotesObjectId: str

# PageType Enum
class PageType(str, Enum):
    SLIDE = "SLIDE"
    MASTER = "MASTER"
    LAYOUT = "LAYOUT"
    NOTES = "NOTES"
    NOTES_MASTER = "NOTES_MASTER"

    @model_validator(mode="after")
    def check_type_specific_fields(self) -> "PageModel":
        if self.pageType == PageType.LAYOUT:
            if self.layoutProperties is None:
                raise ValueError("layoutProperties must be present when pageType is 'LAYOUT'.")
            if self.slideProperties is not None:
                raise ValueError("slideProperties must not be set when pageType is 'LAYOUT'.")
            if self.masterProperties is not None:
                raise ValueError("masterProperties must not be set when pageType is 'LAYOUT'.")
            if self.notesProperties is not None:
                raise ValueError("notesProperties must not be set when pageType is 'LAYOUT'.")
        
        elif self.pageType == PageType.MASTER:
            if self.masterProperties is None:
                raise ValueError("masterProperties must be present when pageType is 'MASTER'.")
            if self.layoutProperties is not None:
                raise ValueError("layoutProperties must not be set when pageType is 'MASTER'.")
            if self.slideProperties is not None:
                raise ValueError("slideProperties must not be set when pageType is 'MASTER'.")
            if self.notesProperties is not None:
                raise ValueError("notesProperties must not be set when pageType is 'MASTER'.")
        
        elif self.pageType == PageType.SLIDE:
            if self.slideProperties is None:
                raise ValueError("slideProperties must be present when pageType is 'SLIDE'.")
            if self.layoutProperties is not None:
                raise ValueError("layoutProperties must not be set when pageType is 'SLIDE'.")
            if self.masterProperties is not None:
                raise ValueError("masterProperties must not be set when pageType is 'SLIDE'.")
            if self.notesProperties is not None:
                raise ValueError("notesProperties must not be set when pageType is 'SLIDE'.")
        
        elif self.pageType == PageType.NOTES:
            if self.notesProperties is None:
                raise ValueError("notesProperties must be present when pageType is 'NOTES'.")
            if self.slideProperties is not None:
                raise ValueError("slideProperties must not be set when pageType is 'NOTES'.")
            if self.layoutProperties is not None:
                raise ValueError("layoutProperties must not be set when pageType is 'NOTES'.")
            if self.masterProperties is not None:
                raise ValueError("masterProperties must not be set when pageType is 'NOTES'.")
        
        else:
            # For NOTES, NOTES_MASTER, etc.
            if self.layoutProperties is not None:
                raise ValueError(f"layoutProperties must not be set when pageType is '{self.pageType}'.")
            if self.masterProperties is not None:
                raise ValueError(f"masterProperties must not be set when pageType is '{self.pageType}'.")
            if self.slideProperties is not None:
                raise ValueError(f"slideProperties must not be set when pageType is '{self.pageType}'.")

        return self


# class Transform(BaseModel):
#     # This is a simplified representation. A full transform would have more matrix components.
#     # For simulation, we might just store a placeholder or simple x, y, scale, rotation.
#     # For now, a generic dict.
#     scaleX: Optional[float] = None
#     scaleY: Optional[float] = None
#     translateX: Optional[float] = None
#     translateY: Optional[float] = None
#     shearX: Optional[float] = None
#     shearY: Optional[float] = None



# --- Page Elements ---

class TextContent(BaseModel):
    textElements: List[TextElement] = Field(default_factory=list)


class MasterProperties(BaseModel):
    displayName: Optional[str] = None

class LayoutProperties(BaseModel):
    masterObjectId: Optional[str] = None
    name: Optional[str] = None
    displayName: Optional[str] = None


class NotesProperties(BaseModel):
    speakerNotesObjectId: str

# PageType Enum
class PageType(str, Enum):
    SLIDE = "SLIDE"
    MASTER = "MASTER"
    LAYOUT = "LAYOUT"
    NOTES = "NOTES"
    NOTES_MASTER = "NOTES_MASTER"

# Page with Pydantic v2 validators
class Page(BaseModel):
    objectId: str
    pageType: PageType
    pageElements: List[PageElement]
    revisionId: Optional[str] = None
    pageProperties: Optional[PageProperties] = None
    slideProperties: Optional[SlideProperties] = None
    layoutProperties: Optional[LayoutProperties] = None
    notesProperties: Optional[NotesProperties] = None
    masterProperties: Optional[MasterProperties] = None
    
    @model_validator(mode="after")
    def check_type_specific_fields(self) -> "Page":
        if self.pageType == PageType.LAYOUT:
            if self.layoutProperties is None:
                raise ValueError("layoutProperties must be present when pageType is 'LAYOUT'.")
            if self.slideProperties is not None:
                raise ValueError("slideProperties must not be set when pageType is 'LAYOUT'.")
            if self.masterProperties is not None:
                raise ValueError("masterProperties must not be set when pageType is 'LAYOUT'.")
            if self.notesProperties is not None:
                raise ValueError("notesProperties must not be set when pageType is 'LAYOUT'.")
        
        elif self.pageType == PageType.MASTER:
            if self.masterProperties is None:
                raise ValueError("masterProperties must be present when pageType is 'MASTER'.")
            if self.layoutProperties is not None:
                raise ValueError("layoutProperties must not be set when pageType is 'MASTER'.")
            if self.slideProperties is not None:
                raise ValueError("slideProperties must not be set when pageType is 'MASTER'.")
            if self.notesProperties is not None:
                raise ValueError("notesProperties must not be set when pageType is 'MASTER'.")
        
        elif self.pageType == PageType.SLIDE:
            if self.slideProperties is None:
                raise ValueError("slideProperties must be present when pageType is 'SLIDE'.")
            if self.layoutProperties is not None:
                raise ValueError("layoutProperties must not be set when pageType is 'SLIDE'.")
            if self.masterProperties is not None:
                raise ValueError("masterProperties must not be set when pageType is 'SLIDE'.")
            if self.notesProperties is not None:
                raise ValueError("notesProperties must not be set when pageType is 'SLIDE'.")
        
        elif self.pageType == PageType.NOTES:
            if self.notesProperties is None:
                raise ValueError("notesProperties must be present when pageType is 'NOTES'.")
            if self.slideProperties is not None:
                raise ValueError("slideProperties must not be set when pageType is 'NOTES'.")
            if self.layoutProperties is not None:
                raise ValueError("layoutProperties must not be set when pageType is 'NOTES'.")
            if self.masterProperties is not None:
                raise ValueError("masterProperties must not be set when pageType is 'NOTES'.")
        
        else:
            # For NOTES, NOTES_MASTER, etc.
            if self.layoutProperties is not None:
                raise ValueError(f"layoutProperties must not be set when pageType is '{self.pageType}'.")
            if self.masterProperties is not None:
                raise ValueError(f"masterProperties must not be set when pageType is '{self.pageType}'.")
            if self.slideProperties is not None:
                raise ValueError(f"slideProperties must not be set when pageType is '{self.pageType}'.")

        return self



# class OpaqueColor(BaseModel):
#     rgbColor: RgbColor

class Color(BaseModel):
    opaqueColor: Optional[OpaqueColor] = None


class LayoutProperties(BaseModel):
    masterObjectId: Optional[str] = None
    name: Optional[str] = None
    displayName: Optional[str] = None


class NotesProperties(BaseModel):
    speakerNotesObjectId: str

# PageType Enum
class PageType(str, Enum):
    SLIDE = "SLIDE"
    MASTER = "MASTER"
    LAYOUT = "LAYOUT"
    NOTES = "NOTES"
    NOTES_MASTER = "NOTES_MASTER"

# PageModel with Pydantic v2 validators
class PageModel(BaseModel):
    objectId: str
    pageType: Optional[PageType] = None
    revisionId: Optional[str] = None
    pageProperties: Optional[PageProperties] = None
    notesProperties: Optional[NotesProperties] = None
    slideProperties: Optional[SlideProperties] = None
    layoutProperties: Optional[LayoutProperties] = None
    masterProperties: Optional[MasterProperties] = None
    pageElements: Optional[List[PageElement]] = Field(default_factory=list)

    @model_validator(mode="after")
    def check_type_specific_fields(self) -> "PageModel":
        if self.pageType == PageType.LAYOUT:
            if self.layoutProperties is None:
                raise ValueError("layoutProperties must be present when pageType is 'LAYOUT'.")
            if self.slideProperties is not None:
                raise ValueError("slideProperties must not be set when pageType is 'LAYOUT'.")
            if self.masterProperties is not None:
                raise ValueError("masterProperties must not be set when pageType is 'LAYOUT'.")
            if self.notesProperties is not None:
                raise ValueError("notesProperties must not be set when pageType is 'LAYOUT'.")
        
        elif self.pageType == PageType.MASTER:
            if self.masterProperties is None:
                raise ValueError("masterProperties must be present when pageType is 'MASTER'.")
            if self.layoutProperties is not None:
                raise ValueError("layoutProperties must not be set when pageType is 'MASTER'.")
            if self.slideProperties is not None:
                raise ValueError("slideProperties must not be set when pageType is 'MASTER'.")
            if self.notesProperties is not None:
                raise ValueError("notesProperties must not be set when pageType is 'MASTER'.")
        
        elif self.pageType == PageType.SLIDE:
            if self.slideProperties is None:
                raise ValueError("slideProperties must be present when pageType is 'SLIDE'.")
            if self.layoutProperties is not None:
                raise ValueError("layoutProperties must not be set when pageType is 'SLIDE'.")
            if self.masterProperties is not None:
                raise ValueError("masterProperties must not be set when pageType is 'SLIDE'.")
            if self.notesProperties is not None:
                raise ValueError("notesProperties must not be set when pageType is 'SLIDE'.")
        
        elif self.pageType == PageType.NOTES:
            if self.notesProperties is None:
                raise ValueError("notesProperties must be present when pageType is 'NOTES'.")
            if self.slideProperties is not None:
                raise ValueError("slideProperties must not be set when pageType is 'NOTES'.")
            if self.layoutProperties is not None:
                raise ValueError("layoutProperties must not be set when pageType is 'NOTES'.")
            if self.masterProperties is not None:
                raise ValueError("masterProperties must not be set when pageType is 'NOTES'.")
        
        else:
            # For NOTES, NOTES_MASTER, etc.
            if self.layoutProperties is not None:
                raise ValueError(f"layoutProperties must not be set when pageType is '{self.pageType}'.")
            if self.masterProperties is not None:
                raise ValueError(f"masterProperties must not be set when pageType is '{self.pageType}'.")
            if self.slideProperties is not None:
                raise ValueError(f"slideProperties must not be set when pageType is '{self.pageType}'.")

        return self


# class Transform(BaseModel):
#     # This is a simplified representation. A full transform would have more matrix components.
#     # For simulation, we might just store a placeholder or simple x, y, scale, rotation.
#     # For now, a generic dict.
#     scaleX: Optional[float] = None
#     scaleY: Optional[float] = None
#     translateX: Optional[float] = None
#     translateY: Optional[float] = None
#     shearX: Optional[float] = None
#     shearY: Optional[float] = None



class CreatePresentationRequest(BaseModel):
    """Request model for creating a new Google Slides presentation.
    
    Based on the official Google Slides API specification for presentations.create.
    All fields are optional except that at least one field should be provided.
    """
    presentationId: Optional[str] = Field(None, description="The ID of the presentation. If not provided, a new ID is generated.")
    pageSize: Optional[Size] = Field(None, description="The size of pages in the presentation.")  
    slides: Optional[List[PageModel]] = Field(None, description="The slides in the presentation.")
    title: Optional[str] = Field(None, min_length=1, max_length=1000, description="The title of the presentation.")
    masters: Optional[List[PageModel]] = Field(None, description="The slide masters in the presentation.")
    layouts: Optional[List[PageModel]] = Field(None, description="The layouts in the presentation.")
    locale: Optional[str] = Field(None, description="The locale of the presentation, as an IETF BCP 47 language tag.")
    revisionId: Optional[str] = Field(None, description="The revision ID of the presentation (output only, ignored in create requests).")
    notesMaster: Optional[PageModel] = Field(None, description="The notes master in the presentation.")

    @model_validator(mode="after")
    def validate_at_least_one_field(self) -> "CreatePresentationRequest":
        """Ensure at least one field is provided in the request."""
        fields_provided = [
            self.presentationId, self.pageSize, self.slides, self.title,
            self.masters, self.layouts, self.locale, self.revisionId, self.notesMaster
        ]
        if all(field is None for field in fields_provided):
            raise ValueError("At least one field must be provided in the create presentation request.")
        return self

class PresentationModel(BaseModel):
    presentationId: str
    title: Optional[str] = None
    pageSize: Optional[Size] = None
    slides: List[PageModel] = []
    masters: List[PageModel] = []
    layouts: List[PageModel] = []
    notesMaster: Optional[PageModel] = None
    locale: Optional[str] = None
    revisionId: Optional[str] = None

# --- Top-level Database Model ---

class GoogleSlidesDB(BaseModel):
    presentations: Dict[str, PresentationModel] = Field(default_factory=dict)
    # The key for the dictionary will be presentationId for quick lookup.
    # In a real scenario, you might also want to simulate users and their ownership.

# --- batch_update_presentation ---
FontSizeUnitEnum = Literal["PT"] # As per docstring for UpdateTextStyleRequest.style.fontSize

PredefinedLayout = Literal[
    "PREDEFINED_LAYOUT_UNSPECIFIED", "BLANK", "CAPTION_ONLY",
    "TITLE", "TITLE_AND_BODY", "TITLE_AND_TWO_COLUMNS",
    "TITLE_ONLY", "SECTION_HEADER", "SECTION_TITLE_AND_DESCRIPTION",
    "ONE_COLUMN_TEXT", "MAIN_POINT", "BIG_NUMBER"
]

OtherType = Literal[
    "TITLE", "BODY", "CHART", "CLIP_ART", "CENTERED_TITLE",
    "DIAGRAM", "DATE_AND_TIME", "FOOTER", "HEADER", "MEDIA",
    "OBJECT", "PICTURE", "SLIDE_NUMBER", "SUBTITLE", "TABLE",
    "SLIDE_IMAGE" 
]

ShapeType = Literal[
    "TYPE_UNSPECIFIED", "TEXT_BOX", "RECTANGLE", "ROUND_RECTANGLE",
    "ELLIPSE", "ARC", "BENT_ARROW", "BENT_UP_ARROW", "BEVEL",
    "BLOCK_ARC", "BRACE_PAIR", "BRACKET_PAIR", "CAN", "CHEVRON",
    "CHORD", "CLOUD", "CORNER", "CUBE", "CURVED_DOWN_ARROW",
    "CURVED_LEFT_ARROW", "CURVED_RIGHT_ARROW", "CURVED_UP_ARROW",
    "DECAGON", "DIAGONAL_STRIPE", "DIAMOND", "DODECAGON", "DONUT",
    "DOUBLE_WAVE", "DOWN_ARROW", "DOWN_ARROW_CALLOUT",
    "FOLDED_CORNER", "FRAME", "HALF_FRAME", "HEART", "HEPTAGON",
    "HEXAGON", "HOME_PLATE", "HORIZONTAL_SCROLL", "IRREGULAR_SEAL_1",
    "IRREGULAR_SEAL_2", "LEFT_ARROW", "LEFT_ARROW_CALLOUT",
    "LEFT_BRACE", "LEFT_BRACKET", "LEFT_RIGHT_ARROW",
    "LEFT_RIGHT_ARROW_CALLOUT", "LEFT_RIGHT_UP_ARROW",
    "LEFT_UP_ARROW", "LIGHTNING_BOLT", "MATH_DIVIDE", "MATH_EQUAL",
    "MATH_MINUS", "MATH_MULTIPLY", "MATH_NOT_EQUAL", "MATH_PLUS",
    "MOON", "NO_SMOKING", "NOTCHED_RIGHT_ARROW", "OCTAGON",
    "NOTCHED_RIGHT_ARROW", "OCTAGON", "PARALLELOGRAM", "PENTAGON",
    "PIE", "PLAQUE", "PLUS", "QUAD_ARROW", "QUAD_ARROW_CALLOUT",
    "QUAD_ARROW_CALLOUT", "RIBBON", "RIBBON_2", "RIGHT_ARROW",
    "RIGHT_ARROW_CALLOUT", "RIGHT_BRACE", "RIGHT_BRACKET",
    "ROUND_1_RECTANGLE", "ROUND_2_DIAGONAL_RECTANGLE",
    "ROUND_2_SAME_RECTANGLE", "RIGHT_TRIANGLE", "SMILEY_FACE",
    "SNIP_1_RECTANGLE", "SNIP_2_DIAGONAL_RECTANGLE", "SNIP_2_SAME_RECTANGLE",
    "SNIP_ROUND_RECTANGLE", "STAR_10", "STAR_12", "STAR_16", "STAR_24",
    "STAR_32", "STAR_4", "STAR_5", "STAR_6", "STAR_7", "STAR_8",
    "STRIPED_RIGHT_ARROW", "SUN", "TRAPEZOID", "TRIANGLE",
    "UP_ARROW", "UP_ARROW_CALLOUT", "UP_DOWN_ARROW", "UTURN_ARROW",
    "VERTICAL_SCROLL", "WAVE", "WEDGE_ELLIPSE_CALLOUT", "WEDGE_RECTANGLE_CALLOUT",
    "STRIPED_RIGHT_ARROW", "SUN", "TRAPEZOID", "TRIANGLE", "UP_ARROW",
    "UP_ARROW_CALLOUT", "UP_DOWN_ARROW", "UTURN_ARROW", "VERTICAL_SCROLL",
    "WAVE", "WEDGE_ELLIPSE_CALLOUT", "WEDGE_RECTANGLE_CALLOUT",
    "WEDGE_ROUND_RECTANGLE_CALLOUT", "FLOW_CHART_ALTERNATE_PROCESS",
    "FLOW_CHART_COLLATE", "FLOW_CHART_CONNECTOR", "FLOW_CHART_DECISION",
    "FLOW_CHART_DECISION", "FLOW_CHART_DELAY", "FLOW_CHART_DISPLAY",
    "FLOW_CHART_DOCUMENT", "FLOW_CHART_EXTRACT", "FLOW_CHART_INPUT_OUTPUT",
    "FLOW_CHART_INTERNAL_STORAGE", "FLOW_CHART_MAGNETIC_DISK",
    "FLOW_CHART_MAGNETIC_DRUM", "FLOW_CHART_MAGNETIC_TAPE",
    "FLOW_CHART_MANUAL_INPUT", "FLOW_CHART_MANUAL_OPERATION",
    "FLOW_CHART_MERGE", "FLOW_CHART_MULTIDOCUMENT",
    "FLOW_CHART_OFFLINE_STORAGE", "FLOW_CHART_OFFPAGE_CONNECTOR",
    "FLOW_CHART_ONLINE_STORAGE", "FLOW_CHART_OR", "FLOW_CHART_PREDEFINED_PROCESS",
    "FLOW_CHART_PREPARATION", "FLOW_CHART_PROCESS", "FLOW_CHART_PUNCHED_CARD",
    "FLOW_CHART_PUNCHED_TAPE", "FLOW_CHART_SORT", "FLOW_CHART_SUMMING_JUNCTION",
    "FLOW_CHART_TERMINATOR", "ARROW_EAST", "ARROW_NORTH_EAST", "ARROW_NORTH",
    "SPEECH", "STARBURST", "TEARDROP", "ELLIPSE_RIBBON", "ELLIPSE_RIBBON_2",
    "CLOUD_CALLOUT", "CUSTOM"
]

RangeType = Literal[
    "RANGE_TYPE_UNSPECIFIED", "FIXED_RANGE", "FROM_START_INDEX", "ALL"
]

# --- Common Reusable Models for Requests ---

OBJECT_ID_PATTERN = r"^[a-zA-Z0-9_][a-zA-Z0-9_:\-]*$"

class LayoutReference(BaseModel):
    predefinedLayout: Optional[PredefinedLayout] = None
    layoutId: Optional[str] = None
    
class Placeholder(BaseModel):
    type: OtherType
    index: int
    parentObjectId: Optional[str] = None

class LayoutPlaceholderIdMapping(BaseModel):
    objectId: Optional[str] = Field(None, min_length=5, max_length=50, pattern=OBJECT_ID_PATTERN)
    layoutPlaceholder: Optional[Placeholder] = None
    layoutPlaceholderObjectId: Optional[str] = None
    
class PageElementProperties(BaseModel):
    pageObjectId: Optional[str] = None
    size: Optional[Size] = None
    transform: Optional[AffineTransform] = None

class TableCellLocation(BaseModel):
    rowIndex: Optional[int] = None
    columnIndex: Optional[int] = None

class SubstringMatchCriteria(BaseModel):
    text: str
    matchCase: Optional[bool] = False
    searchByRegex: Optional[bool] = False

class RequestFontSize(BaseModel):
    magnitude: Optional[float] = None
    unit: Optional[FontSizeUnitEnum] = None

class RequestTextStyle(BaseModel):
    bold: Optional[bool] = None
    italic: Optional[bool] = None
    underline: Optional[bool] = None
    strikethrough: Optional[bool] = None
    fontFamily: Optional[str] = None
    fontSize: Optional[RequestFontSize] = None
    foregroundColor: Optional[Any] = None # Should be 'Optional[Color]' where Color is from existing schema. Using Any for placeholder.
                                        # Assumes `from .SimulationEngine.models import Color` is present.

class NotesPagePropertiesUpdatePayload(BaseModel):
    speakerNotesObjectId: Optional[str] = None # Based on existing NotesPageProperties

class NotesPageUpdatePayload(BaseModel):
    notesPageProperties: Optional[NotesPagePropertiesUpdatePayload] = None

class SlidePropertiesUpdatePayload(BaseModel):
    layoutObjectId: Optional[str] = None
    masterObjectId: Optional[str] = None
    notesPage: Optional[Page] = None
    isSkipped: Optional[bool] = None
    
# --- Request Parameter Models (contents of the request type dict) ---

class CreateSlideRequestParams(BaseModel):
    objectId: Optional[str] = Field(None, min_length=5, max_length=50, pattern=OBJECT_ID_PATTERN)
    insertionIndex: Optional[int] = None
    slideLayoutReference: Optional[LayoutReference] = None
    placeholderIdMappings: Optional[List[LayoutPlaceholderIdMapping]] = None

class CreateShapeRequestParams(BaseModel):
    objectId: Optional[str] = Field(None, min_length=5, max_length=50, pattern=OBJECT_ID_PATTERN)
    elementProperties: Optional[PageElementProperties] = None
    shapeType: ShapeType

class InsertTextRequestParams(BaseModel):
    objectId: str = Field(..., min_length=5, max_length=50, pattern=OBJECT_ID_PATTERN)
    cellLocation: Optional[TableCellLocation] = None
    text: str
    insertionIndex: Optional[int] = None

class ReplaceAllTextRequestParams(BaseModel):
    replaceText: str
    pageObjectIds: Optional[List[str]] = None
    containsText: SubstringMatchCriteria
    
class DeleteObjectRequestParams(BaseModel):
    objectId: str

class DeleteTextRequestParams(BaseModel):
    objectId: str
    cellLocation: Optional[TableCellLocation] = None
    textRange: Range

class DuplicateObjectRequestParams(BaseModel):
    objectId: str
    objectIds: Optional[Dict[str, str]] = None
    # Validation Note: Values in objectIds dict should also match object ID constraints (5-50 chars, pattern).
    # This would require a custom validator for the dictionary values.

class CellLocation(BaseModel):
    rowIndex: Optional[int] = None
    columnIndex: Optional[int] = None

class UpdateTextStyleRequestParams(BaseModel):
    objectId: str
    cellLocation: Optional[CellLocation] = None
    style: TextStyle
    textRange: Optional[Range] = None
    fields: str

class GroupObjectsRequestParams(BaseModel):
    groupObjectId: Optional[str] = Field(None, min_length=5, max_length=50, pattern=OBJECT_ID_PATTERN)
    childrenObjectIds: List[str] = Field(..., min_length=2)

class UngroupObjectsRequestParams(BaseModel):
    objectIds: List[str] = Field(..., min_length=1)

class UpdatePageElementAltTextRequestParams(BaseModel):
    objectId: str
    title: Optional[str] = None
    description: Optional[str] = None

class UpdateSlidePropertiesRequestParams(BaseModel):
    objectId: str
    slideProperties: SlideProperties
    fields: str

# --- Request Wrapper Models (structure for each item in the 'requests' list) ---

class CreateSlideRequestModel(BaseModel):
    createSlide: CreateSlideRequestParams

class CreateShapeRequestModel(BaseModel):
    createShape: CreateShapeRequestParams

class InsertTextRequestModel(BaseModel):
    insertText: InsertTextRequestParams

class ReplaceAllTextRequestModel(BaseModel):
    replaceAllText: ReplaceAllTextRequestParams

class DeleteObjectRequestModel(BaseModel):
    deleteObject: DeleteObjectRequestParams

class DeleteTextRequestModel(BaseModel):
    deleteText: DeleteTextRequestParams

class DuplicateObjectRequestModel(BaseModel):
    duplicateObject: DuplicateObjectRequestParams

class UpdateTextStyleRequestModel(BaseModel):
    updateTextStyle: UpdateTextStyleRequestParams

class GroupObjectsRequestModel(BaseModel):
    groupObjects: GroupObjectsRequestParams

class UngroupObjectsRequestModel(BaseModel):
    ungroupObjects: UngroupObjectsRequestParams

class UpdatePageElementAltTextRequestModel(BaseModel):
    updatePageElementAltText: UpdatePageElementAltTextRequestParams

class UpdateSlidePropertiesRequestModel(BaseModel):
    updateSlideProperties: UpdateSlidePropertiesRequestParams

# Union of all possible request types.
# The function signature `requests: List[Dict[str, Any]]` means Pydantic would validate
# each dict in the list against this Union if these models are used for input validation.
AnyGoogleSlidesRequest = Union[
    CreateSlideRequestModel, CreateShapeRequestModel, InsertTextRequestModel,
    ReplaceAllTextRequestModel, DeleteObjectRequestModel, DeleteTextRequestModel,
    DuplicateObjectRequestModel, UpdateTextStyleRequestModel, GroupObjectsRequestModel,
    UngroupObjectsRequestModel, UpdatePageElementAltTextRequestModel, UpdateSlidePropertiesRequestModel
]

# --- WriteControl Model (for 'writeControl' argument) ---

class WriteControlRequest(BaseModel):
    requiredRevisionId: Optional[str] = None
    targetRevisionId: Optional[str] = None # Deprecated

# --- Response Models ---

class CreateSlideResponsePayload(BaseModel):
    objectId: str

class CreateSlideResponse(BaseModel): # Example of a specific reply structure
    createSlide: CreateSlideResponsePayload

# The 'replies' field in BatchUpdatePresentationResponse is List[Dict[str, Any]].
# CreateSlideResponse is an example of what an element in that list might conform to.

class WriteControlResponse(BaseModel):
    requiredRevisionId: str

class BatchUpdatePresentationResponse(BaseModel):
    presentationId: str
    replies: List[Dict[str, Any]]
    writeControl: WriteControlResponse
