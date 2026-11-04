import pytest

from app.core.ai.interface import AIInterface


def test_interface_cannot_be_instantiated():
    with pytest.raises(TypeError):
        AIInterface()


def test_incomplete_implementation_cannot_be_instantiated():
    class IncompleteAI(AIInterface):
        def generate_tests(self, request):
            pass

    with pytest.raises(TypeError):
        IncompleteAI()


def test_complete_implementation_can_be_instantiated():
    class CompleteAI(AIInterface):
        def generate_tests(self, request):
            pass

        def analyze_results(self, request):
            pass

    ai = CompleteAI()

    assert isinstance(ai, AIInterface)