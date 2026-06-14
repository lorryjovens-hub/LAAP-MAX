"""LAAP Protocol Layer — 数字生命体协议栈"""
from __future__ import annotations

from laap.protocol.laap_ui import (
    Component, ComponentType, ComponentFactory, LayoutTree, RenderEngine, 
    ThemeDefinition, UIComponent, UILayout, UIRenderer
)
from laap.protocol.laap_sync import (
    CRDTDocument, VersionVector, ConflictResolver, StateSynchronizer
)
from laap.protocol.laap_com import Message, MessageBus
from laap.protocol.laap_id import IdentityDocument, IdentityRegistry
from laap.protocol.laap_life import LifecycleStateMachine, StateMachine
from laap.protocol.laap_mem import ForgettingCurve
from laap.protocol.memory_curve import MemoryCurve, MemoryCurvePoint
