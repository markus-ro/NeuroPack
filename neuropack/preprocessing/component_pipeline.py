from enum import Enum

from ..containers import EventContainer
from .signal_components import SignalComponentBase


class ComponentType(Enum):
    Desired = 1
    Undesired = 2


class ComponentPipeline():
    def __init__(self) -> None:
        """Check event to contain a set of desired and undesired components.
        Components need to be added to pipeline before checking event.
        If a desired component is not found, event is rejected.
        Likewise, if an undesired component is found, event is rejected.
        """
        self.desired_components = []
        self.undesired_components = []

    def add_component(self, component: SignalComponentBase,
                      component_type: ComponentType = ComponentType.Undesired):
        """Add component to pipeline. If component_type is not specified, component is added as undesired.

        :param component: Component to add to pipeline.
        :type component: SignalComponentBase
        :param component_type: Specification if component is desired to be present or not, defaults to ComponentType.Undesired
        :type component_type: ComponentType, optional
        """
        if component_type == ComponentType.Desired:
            self.desired_components.append(component)
        else:
            self.undesired_components.append(component)

    def check_event(self, data: EventContainer) -> bool:
        """Check if event contains all desired components and no undesired components.

        :param data: Event to check.
        :type data: EventContainer
        :return: True if event contains all desired components and no undesired components.
        :rtype: bool
        """
        for des in self.desired_components:
            if not des.find(data):
                return False

        for des in self.undesired_components:
            if des.find(data):
                return False

        return True
