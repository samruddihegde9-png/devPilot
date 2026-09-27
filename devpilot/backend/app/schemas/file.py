from typing import Literal, Optional

from pydantic import BaseModel, Field

FileNodeType = Literal["file", "directory"]


class FileNode(BaseModel):
    name: str
    path: str
    type: FileNodeType
    size: Optional[int] = None
    children: Optional[list["FileNode"]] = None


FileNode.model_rebuild()


class FileContent(BaseModel):
    path: str
    content: str


class FileWrite(BaseModel):
    content: str = Field(default="")


class FileCreate(BaseModel):
    path: str = Field(min_length=1, max_length=1000)
    type: FileNodeType = "file"
    content: str = Field(default="")


class FileRename(BaseModel):
    new_path: str = Field(min_length=1, max_length=1000)
