from __future__ import annotations

from typing import Any, Dict, List, Tuple


_HAVE_PYDANTIC = False
try:  # optional dependency
    from pydantic import BaseModel, Field, ValidationError
    _HAVE_PYDANTIC = True
except Exception:  # pragma: no cover - optional
    BaseModel = object  # type: ignore
    Field = object  # type: ignore
    ValidationError = Exception  # type: ignore


def have_pydantic() -> bool:
    return _HAVE_PYDANTIC


# ------------------- Annotation Model -------------------

if _HAVE_PYDANTIC:

    class AnnotationModel(BaseModel):
        user_summary: str
        assistant_summary: str
        user_polarity: str
        assistant_polarity: str
        unfinished_thread: bool
        has_useful_output: bool
        contains_preference: bool
        contains_design: bool
        contains_learning: bool
        tags: List[str] = Field(default_factory=list)

        class Config:
            extra = "ignore"

else:

    class AnnotationModel:  # type: ignore
        pass


def validate_annotation(obj: Dict[str, Any]) -> Tuple[bool, Dict[str, Any] | str]:
    if not _HAVE_PYDANTIC:
        return True, obj
    try:
        m = AnnotationModel.model_validate(obj)  # type: ignore[attr-defined]
        return True, m.model_dump(exclude_none=True)  # type: ignore[attr-defined]
    except ValidationError as e:  # type: ignore[misc]
        return False, str(e)


def schema_annotation() -> Dict[str, Any] | None:
    if not _HAVE_PYDANTIC:
        return None
    return AnnotationModel.model_json_schema()  # type: ignore[attr-defined]


# ------------------- Judge Output Model -------------------

if _HAVE_PYDANTIC:

    class JudgeScores(BaseModel):
        accuracy: float
        completeness: float
        consistency: float

        class Config:
            extra = "ignore"

    class JudgeItem(BaseModel):
        id: str
        scores: JudgeScores
        issues: List[str] = Field(default_factory=list)
        suggestions: List[str] = Field(default_factory=list)

        class Config:
            extra = "ignore"

    class JudgeOutput(BaseModel):
        per_item: List[JudgeItem]
        common_issues: List[str] = Field(default_factory=list)
        suggested_queries: List[str] = Field(default_factory=list)

        class Config:
            extra = "ignore"

else:

    class JudgeOutput:  # type: ignore
        pass


def validate_judge(obj: Dict[str, Any]) -> Tuple[bool, Dict[str, Any] | str]:
    if not _HAVE_PYDANTIC:
        return True, obj
    try:
        m = JudgeOutput.model_validate(obj)  # type: ignore[attr-defined]
        return True, m.model_dump(exclude_none=True)  # type: ignore[attr-defined]
    except ValidationError as e:  # type: ignore[misc]
        return False, str(e)


def schema_judge() -> Dict[str, Any] | None:
    if not _HAVE_PYDANTIC:
        return None
    return JudgeOutput.model_json_schema()  # type: ignore[attr-defined]


# ------------------- Cluster Summary Model -------------------

if _HAVE_PYDANTIC:

    class ClusterSummary(BaseModel):
        title: str
        themes: List[str]
        risks: List[str]
        labels: List[str]

        class Config:
            extra = "ignore"

else:

    class ClusterSummary:  # type: ignore
        pass


def validate_cluster_summary(obj: Dict[str, Any]) -> Tuple[bool, Dict[str, Any] | str]:
    if not _HAVE_PYDANTIC:
        return True, obj
    try:
        m = ClusterSummary.model_validate(obj)  # type: ignore[attr-defined]
        return True, m.model_dump(exclude_none=True)  # type: ignore[attr-defined]
    except ValidationError as e:  # type: ignore[misc]
        return False, str(e)


def schema_cluster_summary() -> Dict[str, Any] | None:
    if not _HAVE_PYDANTIC:
        return None
    return ClusterSummary.model_json_schema()  # type: ignore[attr-defined]


