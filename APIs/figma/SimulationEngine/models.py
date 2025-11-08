from typing import Any, Dict, List, Optional, Union, Literal

from pydantic import BaseModel, Field, RootModel, ConfigDict, model_validator
from typing import Annotated
from enum import Enum

# Color Model (used in various places)
class Color(BaseModel):
    r: Optional[float] = None
    g: Optional[float] = None
    b: Optional[float] = None
    a: Optional[float] = None


# Metadata Model
class Metadata(BaseModel):
    name: Optional[str] = None
    lastModified: Optional[str] = None
    thumbnailUrl: Optional[str] = None


# AbsoluteBoundingBox Model
class AbsoluteBoundingBox(BaseModel):
    x: Optional[float] = None
    y: Optional[float] = None
    width: Optional[float] = None
    height: Optional[float] = None


# Constraints Model
class Constraints(BaseModel):
    vertical: Optional[str] = None
    horizontal: Optional[str] = None


# FillItem Model (for when 'fills' is a list of objects)
class FillItem(BaseModel):
    type: Optional[str] = None
    visible: Optional[bool] = None
    opacity: Optional[float] = None
    blendMode: Optional[str] = None
    color: Optional[Color] = None
    boundVariables: Optional[Dict[str, Any]] = None  # Could be more specific
    # For IMAGE type fills
    imageRef: Optional[str] = None
    scaleMode: Optional[str] = None
    imageTransform: Optional[List[List[float]]] = None  # [[1,0,0],[0,1,0]]
    scalingFactor: Optional[float] = None
    filters: Optional[Dict[str, Any]] = None  # e.g. {"exposure": 0, "contrast": 0.1}


# Fill Model using RootModel for Union type
class Fill(RootModel[Union[str, List[FillItem]]]):
    root: Union[str, List[FillItem]]


# Stroke Model
class Stroke(BaseModel):
    type: Optional[str] = None
    visible: Optional[bool] = None
    opacity: Optional[float] = None
    blendMode: Optional[str] = None
    color: Optional[Color] = None
    boundVariables: Optional[Dict[str, Any]] = None


# Effect Model
class Effect(BaseModel):
    type: Optional[str] = None
    visible: Optional[bool] = None
    radius: Optional[float] = None
    color: Optional[Color] = None
    blendMode: Optional[str] = None
    offset: Optional[Dict[str, float]] = None
    spread: Optional[float] = None
    showShadowBehindNode: Optional[bool] = None


# Styles Model (references to shared styles)
class Styles(BaseModel):
    fills: Optional[str] = None
    text: Optional[str] = None
    strokes: Optional[str] = None
    effects: Optional[str] = None


# ExportSetting Model
class ExportSettingConstraint(BaseModel):
    type: Optional[str] = None
    value: Optional[float] = None


class ExportSetting(BaseModel):
    suffix: Optional[str] = None
    format: Optional[str] = None
    constraint: Optional[ExportSettingConstraint] = None
    contentsOnly: Optional[bool] = None


# PrototypeInteraction Model (kept generic as per schema)
class PrototypeInteraction(BaseModel):
    event: Optional[Dict[str, Any]] = None
    action: Optional[Dict[str, Any]] = None


# BoundVariable Model
class BoundVariableValue(BaseModel):
    id: Optional[str] = None
    type: Optional[str] = None


# LayoutGrid Model
class LayoutGrid(BaseModel):
    pattern: Optional[str] = None
    sectionSize: Optional[float] = None
    visible: Optional[bool] = None
    color: Optional[Color] = None
    alignment: Optional[str] = None
    gutterSize: Optional[float] = None
    offset: Optional[float] = None
    count: Optional[int] = None


# Node Style Model (inline style properties, particularly for TEXT)
class NodeStyle(BaseModel):
    fontFamily: Optional[str] = None
    fontPostScriptName: Optional[str] = None
    fontWeight: Optional[float] = None
    fontSize: Optional[float] = None
    textAlignHorizontal: Optional[str] = None
    textAlignVertical: Optional[str] = None
    letterSpacing: Optional[Union[float, str]] = None
    lineHeightPx: Optional[float] = None
    lineHeightPercent: Optional[float] = None
    lineHeightPercentFontSize: Optional[float] = None
    lineHeightUnit: Optional[str] = None
    textCase: Optional[str] = None
    textDecoration: Optional[str] = None
    textAutoResize: Optional[str] = None
    textTruncation: Optional[str] = None
    maxLines: Optional[Optional[float]] = None


# ComponentProperties Model (for instances)
class ComponentProperty(BaseModel):
    value: Optional[Any] = None
    type: Optional[str] = None


# Override Model (for instances)
class Override(BaseModel):
    id: Optional[str] = None
    overriddenFields: Optional[List[str]] = None


# ComponentPropertyDefinition Model
class ComponentPropertyDefinitionValue(BaseModel):
    type: Optional[str] = None
    defaultValue: Optional[Any] = None
    variantOptions: Optional[List[str]] = None
    preferredValues: Optional[List[Dict[str, Any]]] = None


class ComponentPropertyDefinitions(
    RootModel[Dict[str, ComponentPropertyDefinitionValue]]
):
    root: Dict[str, ComponentPropertyDefinitionValue]


# ArcData Model (for ELLIPSE nodes)
class ArcData(BaseModel):
    startingAngle: Optional[float] = None
    endingAngle: Optional[float] = None
    innerRadius: Optional[float] = None


# SliceMeasurements Model (for SLICE nodes)
class SliceMeasurements(BaseModel):
    x: Optional[float] = None
    y: Optional[float] = None
    width: Optional[float] = None
    height: Optional[float] = None


# DevStatus Model
class DevStatus(BaseModel):
    type: Optional[str] = None


# Node Model (Recursive)
class Node(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    type: Optional[str] = None
    visible: Optional[bool] = Field(default=None)
    locked: Optional[bool] = Field(default=None)
    opacity: Optional[float] = Field(default=None)
    rotation: Optional[float] = Field(default=None)
    blendMode: Optional[str] = None
    isMask: Optional[bool] = Field(default=None)
    isFixed: Optional[bool] = Field(default=None)
    absoluteBoundingBox: Optional[AbsoluteBoundingBox] = None
    absoluteRenderBounds: Optional[AbsoluteBoundingBox] = None
    constraints: Optional[Constraints] = None
    fills: Optional[Fill] = None
    strokes: Optional[List[Stroke]] = None
    strokeWeight: Optional[float] = None
    strokeAlign: Optional[str] = None
    strokeJoin: Optional[str] = None
    strokeCap: Optional[str] = None
    strokeDashes: Optional[List[float]] = None
    strokeMiterAngle: Optional[float] = None
    strokeGeometry: Optional[List[Dict[str, Any]]] = None
    fillGeometry: Optional[List[Dict[str, Any]]] = None
    cornerRadius: Optional[float] = None
    cornerSmoothing: Optional[float] = None
    rectangleCornerRadii: Optional[List[float]] = None
    borderRadius: Optional[str] = None
    effects: Optional[List[Effect]] = None
    layoutAlign: Optional[str] = None
    layoutGrow: Optional[float] = None
    layoutSizingHorizontal: Optional[str] = None
    layoutSizingVertical: Optional[str] = None
    styles: Optional[Styles] = None
    exportSettings: Optional[List[ExportSetting]] = None
    prototypeInteractions: Optional[List[PrototypeInteraction]] = None
    boundVariables: Optional[Dict[str, BoundVariableValue]] = None
    clipsContent: Optional[bool] = None
    background: Optional[List[FillItem]] = None
    backgroundColor: Optional[Color] = None
    layoutMode: Optional[str] = None
    primaryAxisSizingMode: Optional[str] = None
    counterAxisSizingMode: Optional[str] = None
    primaryAxisAlignItems: Optional[str] = None
    counterAxisAlignItems: Optional[str] = None
    paddingLeft: Optional[float] = None
    paddingRight: Optional[float] = None
    paddingTop: Optional[float] = None
    paddingBottom: Optional[float] = None
    paddingHorizontal: Optional[float] = None
    paddingVertical: Optional[float] = None
    itemSpacing: Optional[float] = None
    itemReverseZIndex: Optional[bool] = None
    strokesIncludedInLayout: Optional[bool] = None
    layoutGrids: Optional[List[LayoutGrid]] = None
    text: Optional[str] = Field(
        None, serialization_alias="characters", validation_alias="characters"
    )
    textStyle: Optional[str] = None
    style: Optional[NodeStyle] = None
    characterStyleOverrides: Optional[List[float]] = None
    styleOverrideTable: Optional[Dict[str, Any]] = None
    lineTypes: Optional[List[str]] = None
    lineIndentations: Optional[List[float]] = None
    componentId: Optional[str] = None
    componentProperties: Optional[Dict[str, ComponentProperty]] = None
    overrides: Optional[List[Override]] = None
    uniformScaleFactor: Optional[float] = None
    isExposedInstance: Optional[bool] = None
    exposedInstances: Optional[List[str]] = None
    booleanOperation: Optional[str] = None
    componentPropertyDefinitions: Optional[ComponentPropertyDefinitions] = None
    arcData: Optional[ArcData] = None
    sliceMeasurements: Optional[SliceMeasurements] = None
    devStatus: Optional[DevStatus] = None
    children: Optional[List["Node"]] = None
    layout: Optional[str] = None


Node.model_rebuild()


# Variable-related models first
class VariableValueResolved(RootModel[Union[Color, str, float, bool, Dict[str, Any]]]):
    root: Union[Color, str, float, bool, Dict[str, Any]]


class VariableCodeSyntax(BaseModel):
    WEB: Optional[str] = None
    ANDROID: Optional[str] = None
    IOS: Optional[str] = None


class VariableMetadata(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    key: Optional[str] = None
    variableCollectionId: Optional[str] = None
    resolvedType: Optional[str] = None
    valuesByMode: Optional[Dict[str, VariableValueResolved]] = None
    remote: Optional[bool] = None
    description: Optional[str] = None
    hiddenFromPublishing: Optional[bool] = None
    scopes: Optional[List[str]] = None
    codeSyntax: Optional[VariableCodeSyntax] = Field(default_factory=dict)


class VariableCollectionMode(BaseModel):
    modeId: Optional[str] = None
    name: Optional[str] = None


class VariableCollectionMetadata(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    key: Optional[str] = None
    modes: Optional[List[VariableCollectionMode]] = None
    defaultModeId: Optional[str] = None
    remote: Optional[bool] = None
    hiddenFromPublishing: Optional[bool] = None
    variableIds: Optional[List[str]] = None


# Then GlobalVars and related models
class StyleDefinition(
    RootModel[Union[List[Union[str, FillItem]], NodeStyle, Dict[str, Any]]]
):
    root: Union[List[Union[str, FillItem]], NodeStyle, Dict[str, Any]]


class GlobalVars(BaseModel):
    styles: Optional[Dict[str, StyleDefinition]] = None
    variables: Optional[Dict[str, VariableMetadata]] = None
    variableCollections: Optional[Dict[str, VariableCollectionMetadata]] = None


# Then FigmaData and related models
class FigmaData(BaseModel):
    metadata: Optional[Metadata] = None
    nodes: Optional[List[Node]] = None
    globalVars: Optional[GlobalVars] = None


class GetFigmaDataResponse(BaseModel):
    figma_data: Optional[FigmaData] = None


# --- Models for Figma_V0_DB.json structure (for completeness and validation against example) ---


class FlowStartingPoint(BaseModel):
    nodeId: Optional[str] = None
    name: Optional[str] = None
    scale: Optional[float] = None
    rotation: Optional[float] = None


class PrototypeDevice(BaseModel):
    type: Optional[str] = None
    rotation: Optional[str] = None
    size: Optional[Dict[str, float]] = None
    presetIdentifier: Optional[str] = None


class DBCanvasNode(Node):  # Extending the generic Node
    scrollBehavior: Optional[str] = None
    prototypeStartNodeID: Optional[str] = None
    flowStartingPoints: Optional[List[FlowStartingPoint]] = None
    prototypeDevice: Optional[PrototypeDevice] = None
    children: Optional[List[Node]] = (
        None  # Children are typically Frames, Groups, etc. (generic Node)
    )


class DBDocumentNode(Node):  # Extending the generic Node
    scrollBehavior: Optional[str] = None
    children: Optional[List[DBCanvasNode]] = None


DBDocumentNode.model_rebuild()
DBCanvasNode.model_rebuild()


class ComponentMetadata(BaseModel):
    key: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    remote: Optional[bool] = None
    documentationLinks: Optional[List[Any]] = None
    componentSetId: Optional[str] = None


class ComponentSetMetadata(BaseModel):
    key: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    documentationLinks: Optional[List[Any]] = None


class StyleMetadata(BaseModel):
    key: Optional[str] = None
    name: Optional[str] = None
    styleType: Optional[str] = None
    remote: Optional[bool] = None
    description: Optional[str] = None


class FigmaFile(BaseModel):
    fileKey: Optional[str] = None
    name: Optional[str] = None
    lastModified: Optional[str] = None
    thumbnailUrl: Optional[str] = None
    version: Optional[str] = None
    role: Optional[str] = None
    editorType: Optional[str] = None
    linkAccess: Optional[str] = None
    schemaVersion: Optional[int] = None
    document: Optional[DBDocumentNode] = None
    components: Optional[Dict[str, ComponentMetadata]] = None
    componentSets: Optional[Dict[str, ComponentSetMetadata]] = None
    globalVars: Optional[GlobalVars] = None


class FigmaDB(BaseModel):
    files: Optional[List[FigmaFile]] = None
    current_selection_node_ids: Optional[List[str]] = []

class FigmaFileReturnMetadata(BaseModel):
    name: str
    lastModified: str  # ISO 8601 timestamp
    thumbnailUrl: str  # URL of the file's thumbnail image

class GetFigmaDataReturnType(BaseModel):
    metadata: FigmaFileReturnMetadata
    nodes: List['Node']  # List of Node objects (Node type from existing schema)
    globalVars: 'GlobalVars'  # GlobalVars object (GlobalVars type from existing schema)

class FigmaNodeDownloadSpec(BaseModel):
    node_id: str
    file_name: str

class ClonedNodeInfo(BaseModel):
    id: str
    name: str
    type: str
    parentId: str
    x: float
    y: float
    
class ResizeNodeResponse(BaseModel):
    node_id: str
    final_width: float
    final_height: float



class FigmaPaint(BaseModel):
    model_config = ConfigDict(extra="allow")

    type: str  # The type of paint (e.g., 'SOLID', 'GRADIENT_LINEAR').
    visible: Optional[bool] = Field(default=True) # Whether the paint is visible.
    opacity: Optional[float] = Field(default=1.0) # Opacity of the paint (0 to 1).
    color: Optional[Color] = None # For 'SOLID' paint type.
    gradientStops: Optional[List[Dict[str, Any]]] = None # For gradient paint types.


class FigmaFontName(BaseModel):
    family: str  # Font family.
    style: str   # Font style.


class FigmaStyle(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str  # The unique identifier of the style.
    key: str  # A unique key for the style.
    name: str  # The user-defined name of the style.
    styleType: str  # The type of style (e.g., 'FILL', 'TEXT', 'EFFECT', 'GRID').
    description: Optional[str] = None  # An optional description for the style.
    remote: bool  # Whether the style is from a remote library.

    # Properties specific to styleType
    paints: Optional[List[FigmaPaint]] = None  # Present if 'styleType' is 'FILL'.
    fontSize: Optional[float] = None  # Present if 'styleType' is 'TEXT'.
    fontName: Optional[FigmaFontName] = None  # Present if 'styleType' is 'TEXT'.
    
# --- create_rectangle ---
class ValidParentNodeType(str, Enum):
    """
    Enum defining node types that can be valid parents for other nodes
    when creating new nodes like rectangles.
    """
    DOCUMENT = "DOCUMENT"
    CANVAS = "CANVAS"
    FRAME = "FRAME"
    GROUP = "GROUP"
    COMPONENT = "COMPONENT"
    COMPONENT_SET = "COMPONENT_SET"
    INSTANCE = "INSTANCE"
    SECTION = "SECTION"

class CreateRectangleResponse(BaseModel):
    """
    Information about the newly created rectangle node.
    """
    id: str
    name: str
    type: Literal["RECTANGLE"]
    parentId: Optional[str] = None
    x: float
    y: float
    width: float
    height: float

# --- set_fill_color ---

class FillableNodeType(str, Enum):
    """
    Enum defining node types that typically support a 'fills' property
    and can have their fill color set directly.
    """
    TEXT = "TEXT"
    FRAME = "FRAME"
    RECTANGLE = "RECTANGLE"
    ELLIPSE = "ELLIPSE"
    VECTOR = "VECTOR"
    STAR = "STAR"
    REGULAR_POLYGON = "REGULAR_POLYGON"
    COMPONENT = "COMPONENT"
    INSTANCE = "INSTANCE"
    SHAPE_WITH_TEXT = "SHAPE_WITH_TEXT"

class FailedNodeDeletionDetail(BaseModel):
    nodeId: str = Field(..., description="The ID of the node that could not be deleted.")
    reason: str = Field(..., description="A brief explanation for the failure (e.g., 'Node not found', 'Node locked').")

class DeleteMultipleNodesResponse(BaseModel):
    successfully_deleted_ids: List[str] = Field(..., description="A list of node IDs that were successfully deleted.")
    failed_to_delete: List[FailedNodeDeletionDetail] = Field(..., description="A list of nodes that failed to delete, with reasons.")

class SelectedNodeInfo(BaseModel):
    """
    Represents a summary of a selected node in Figma.
    """
    id: str = Field(..., description="The unique identifier of the selected node.")
    name: str = Field(..., description="The name of the selected node.")
    type: str = Field(..., description="The type of the node (e.g., 'FRAME', 'RECTANGLE', 'TEXT').")
    parentId: str = Field(..., description="The ID of the parent node.")

class FoundNodeInfo(BaseModel):
    """
    Represents basic information about a Figma node found during a scan.
    """
    id: str = Field(..., description="The unique identifier of the found node.")
    name: str = Field(..., description="The name of the found node.")
    type: str = Field(..., description="The type of the found node.")
    parentId: str = Field(..., description="The ID of the immediate parent of this node.")

class AnnotationCategoryDetail(BaseModel):
    """Detailed information about the category."""
    id: str
    name: str
    color: str

class AnnotationProperty(BaseModel):
    """A custom key-value property object associated with an annotation."""
    type: str
    value: Any

class Annotation(BaseModel):
    """Represents an annotation object as returned by the function."""
    id: str
    nodeId: str
    labelMarkdown: str
    createdAt: str  # ISO 8601 timestamp
    updatedAt: str  # ISO 8601 timestamp
    resolvedAt: Optional[str] = None  # ISO 8601 timestamp or null
    userId: str
    categoryId: Optional[str] = None
    category: Optional[AnnotationCategoryDetail] = None
    properties: Optional[List[AnnotationProperty]] = None

class AnnotationDetails(BaseModel):
    """
    Represents the detailed structure of an annotation, typically returned
    after creation or update.
    """
    id: str
    nodeId: str
    labelMarkdown: str
    createdAt: str  # ISO 8601 timestamp
    updatedAt: str  # ISO 8601 timestamp
    userId: str
    categoryId: Optional[str] = None
    properties: Optional[List[AnnotationProperty]] = None



# --- set_layout_mode ---

class LayoutModeEnum(str, Enum):
    """
    Enum for valid layout modes in Figma.
    """
    NONE = "NONE"
    HORIZONTAL = "HORIZONTAL"
    VERTICAL = "VERTICAL"

class LayoutWrapEnum(str, Enum):
    """
    Enum for valid layout wrap behaviors in Figma.
    """
    NO_WRAP = "NO_WRAP"
    WRAP = "WRAP"

class FigmaNodeDetailColor(BaseModel):
    r: float
    g: float
    b: float
    a: float

class FigmaNodeDetailBoundingBox(BaseModel):
    x: float
    y: float
    width: float
    height: float

class FigmaNodeDetailPaint(BaseModel):
    type: str
    visible: bool
    opacity: Optional[float] = None
    color: Optional[FigmaNodeDetailColor] = None

class FigmaNodeDetailEffectOffset(BaseModel):
    x: float
    y: float

class FigmaNodeDetailEffect(BaseModel):
    type: str
    visible: bool
    radius: float
    color: Optional[FigmaNodeDetailColor] = None
    offset: Optional[FigmaNodeDetailEffectOffset] = None

class FigmaNodeDetailFontName(BaseModel):
    family: str
    style: str

class FigmaNodeDetails(BaseModel):
    id: str
    name: str
    type: str # e.g., 'DOCUMENT', 'CANVAS', 'FRAME', 'RECTANGLE', 'TEXT', 'COMPONENT', 'INSTANCE', 'VECTOR'
    visible: bool
    locked: bool
    opacity: float
    absoluteBoundingBox: FigmaNodeDetailBoundingBox
    fills: List[FigmaNodeDetailPaint]
    strokes: List[FigmaNodeDetailPaint]
    strokeWeight: float
    strokeAlign: str # e.g., 'INSIDE', 'OUTSIDE', 'CENTER'
    effects: List[FigmaNodeDetailEffect]
    children: Optional[List['FigmaNodeDetails']] = None
    parentId: Optional[str] = None
    characters: Optional[str] = None
    fontSize: Optional[float] = None
    fontName: Optional[FigmaNodeDetailFontName] = None
    componentId: Optional[str] = None
    layoutMode: Optional[str] = None # e.g., 'NONE', 'HORIZONTAL', 'VERTICAL'
    itemSpacing: Optional[float] = None
    paddingLeft: Optional[float] = None
    paddingRight: Optional[float] = None
    paddingTop: Optional[float] = None
    paddingBottom: Optional[float] = None
    primaryAxisAlignItems: Optional[str] = None
    counterAxisAlignItems: Optional[str] = None

# Update forward reference
FigmaNodeDetails.model_rebuild()

class GetAnnotationResponse(BaseModel):
    """Represents an annotation object as returned by the function."""
    id: str
    nodeId: str
    labelMarkdown: str
    createdAt: str  # ISO 8601 timestamp
    updatedAt: str  # ISO 8601 timestamp
    resolvedAt: Optional[str] = None  # ISO 8601 timestamp or null
    userId: str
    categoryId: Optional[str] = None
    category: Optional[AnnotationCategoryDetail] = None
    properties: Optional[List[AnnotationProperty]] = None

class LocalComponent(BaseModel):
    """
    Represents a local component from the Figma document.
    """
    id: str  # The unique identifier of the component node.
    key: str  # A unique key for the component, used for creating instances or referencing in APIs.
    name: str  # The user-defined name of the component.
    description: Optional[str] = None  # An optional description for the component.
    componentSetId: Optional[str] = None  # If part of a component set, the ID of that set.
    parentId: str  # The ID of the page or frame containing this main component definition.
    
# --- Models for create_text ---
class RGBAColor(BaseModel):
    r: Annotated[float, Field(ge=0.0, le=1.0)]
    g: Annotated[float, Field(ge=0.0, le=1.0)]
    b: Annotated[float, Field(ge=0.0, le=1.0)]
    a: Annotated[float, Field(ge=0.0, le=1.0)]

class FontColor(BaseModel):
    type: str = Field(..., pattern="^SOLID$")
    color: RGBAColor
    visible: Optional[bool] = None

class CreateTextArgs(BaseModel):
    x: float
    y: float
    text: str = Field(..., min_length=1)
    font_size: Optional[Annotated[float, Field(gt=0)]] = None
    font_weight: Optional[Annotated[float, Field(gt=0)]] = None
    font_color: Optional[FontColor] = None
    name: Optional[str] = None
    parent_id: Optional[str] = None
    
class CreatedTextNodeInfo(BaseModel):
    """
    Information about a newly created text node in Figma.
    Corresponds to the return type of the create_text function.
    """
    id: str
    name: str
    type: str # Expected to be 'TEXT'
    parent_id: Optional[str] = None
    x: float
    y: float
    characters: str
    font_size: float
    fills: List['FillItem']  # Assumes FillItem is an existing model representing a Figma Paint object

# --- Pydantic model for create_frame argument validation ---

class CreateFrame_LayoutMode(str, Enum):
    """Enum for valid layout modes for frame creation."""
    NONE = "NONE"
    HORIZONTAL = "HORIZONTAL"
    VERTICAL = "VERTICAL"

class CreateFrame_LayoutWrap(str, Enum):
    """Enum for valid layout wrap behaviors for frame creation."""
    NO_WRAP = "NO_WRAP"
    WRAP = "WRAP"

class CreateFrame_PrimaryAxisAlignItems(str, Enum):
    """Enum for valid primary axis alignment for frame creation."""
    MIN = "MIN"
    MAX = "MAX"
    CENTER = "CENTER"
    SPACE_BETWEEN = "SPACE_BETWEEN"

class CreateFrame_CounterAxisAlignItems(str, Enum):
    """Enum for valid counter axis alignment for frame creation."""
    MIN = "MIN"
    MAX = "MAX"
    CENTER = "CENTER"
    BASELINE = "BASELINE"

class CreateFrame_LayoutSizing(str, Enum):
    """Enum for valid layout sizing behaviors for frame creation."""
    FIXED = "FIXED"
    HUG = "HUG"
    FILL = "FILL"


class CreateFrameArgs(BaseModel):
    """
    A Pydantic model to validate the arguments for the create_frame function.
    It enforces type constraints, value ranges, and logical dependencies
    between arguments, particularly for auto-layout settings.
    """
    x: float
    y: float
    width: float = Field(gt=0)
    height: float = Field(gt=0)
    name: Optional[str] = None
    parent_id: Optional[str] = None
    fill_color: Optional[Dict[str, Any]] = None
    stroke_color: Optional[Dict[str, Any]] = None
    stroke_weight: Optional[float] = Field(default=None, gt=0)
    layout_mode: Optional[CreateFrame_LayoutMode] = None
    layout_wrap: Optional[CreateFrame_LayoutWrap] = None
    padding_top: Optional[float] = Field(default=None, ge=0)
    padding_right: Optional[float] = Field(default=None, ge=0)
    padding_bottom: Optional[float] = Field(default=None, ge=0)
    padding_left: Optional[float] = Field(default=None, ge=0)
    primary_axis_align_items: Optional[CreateFrame_PrimaryAxisAlignItems] = None
    counter_axis_align_items: Optional[CreateFrame_CounterAxisAlignItems] = None
    layout_sizing_horizontal: Optional[CreateFrame_LayoutSizing] = None
    layout_sizing_vertical: Optional[CreateFrame_LayoutSizing] = None
    item_spacing: Optional[float] = Field(default=None, ge=0)

    @model_validator(mode='after')
    def check_layout_dependencies(self) -> 'CreateFrameArgs':
        """
        Ensures that auto-layout properties are only provided when layout_mode
        is set to HORIZONTAL or VERTICAL.
        """
        effective_layout_mode = self.layout_mode or CreateFrame_LayoutMode.NONE

        if effective_layout_mode == CreateFrame_LayoutMode.NONE:
            # These fields are only valid when layout mode is HORIZONTAL or VERTICAL
            dependent_fields = {
                "layout_wrap": self.layout_wrap,
                "padding_top": self.padding_top,
                "padding_right": self.padding_right,
                "padding_bottom": self.padding_bottom,
                "padding_left": self.padding_left,
                "item_spacing": self.item_spacing,
            }
            for field_name, value in dependent_fields.items():
                if value is not None:
                    raise ValueError(f"{field_name} requires layout_mode to be HORIZONTAL or VERTICAL.")

            if self.primary_axis_align_items is not None or self.counter_axis_align_items is not None:
                raise ValueError("Axis alignment properties require layout_mode to be HORIZONTAL or VERTICAL.")
        return self