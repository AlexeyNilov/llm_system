import pytest
from pydantic import BaseModel, TypeAdapter, ValidationError

from llm_system.game_packages import (
    CharacterDefinition,
    DecisionPolicyReference,
    EntityCollectionDefinition,
    EntityDefinition,
    GoalDefinition,
    LocationPlacementDefinition,
    NpcCharacterDefinition,
    ObjectDefinition,
    ObjectPlacementDefinition,
    PlayerCharacterDefinition,
    PossessedPlacementDefinition,
)


def _valid_npc_data() -> dict[str, object]:
    return {
        "entity_type": "npc_character",
        "id": "sela",
        "name": "Sela",
        "character_archetype_id": "medic",
        "initial_location_id": "field-clinic",
        "identity_summary": "A focused field medic.",
        "goals": [{"id": "keep-people-safe", "description": "Protect patients."}],
        "decision_policy": {"policy_type": "rule", "policy_id": "medic-routine"},
    }


def test_entity_definition_discriminator_parses_each_concrete_variant() -> None:
    adapter: TypeAdapter[EntityDefinition] = TypeAdapter(EntityDefinition)

    object_definition = adapter.validate_python(
        {
            "entity_type": "object",
            "id": "medicine-kit",
            "name": "Medicine Kit",
            "object_archetype_id": "medical-supplies",
            "initial_placement": {
                "placement_type": "location",
                "location_id": "field-clinic",
            },
        }
    )
    player_definition = adapter.validate_python(
        {
            "entity_type": "player_character",
            "id": "marin",
            "name": "Marin",
            "character_archetype_id": "scout",
            "initial_location_id": "field-clinic",
        }
    )
    npc_definition = adapter.validate_python(
        {
            "entity_type": "npc_character",
            "id": "sela",
            "name": "Sela",
            "character_archetype_id": "medic",
            "initial_location_id": "field-clinic",
            "identity_summary": "A focused field medic.",
            "goals": [{"id": "keep-people-safe", "description": "Protect patients."}],
            "decision_policy": {"policy_type": "rule", "policy_id": "medic-routine"},
        }
    )

    assert isinstance(object_definition, ObjectDefinition)
    assert isinstance(player_definition, PlayerCharacterDefinition)
    assert isinstance(npc_definition, NpcCharacterDefinition)


def test_entity_variants_reject_foreign_and_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        PlayerCharacterDefinition.model_validate(
            {
                "entity_type": "player_character",
                "id": "marin",
                "name": "Marin",
                "character_archetype_id": "scout",
                "initial_location_id": "field-clinic",
                "identity_summary": "Not allowed.",
            }
        )
    with pytest.raises(ValidationError):
        ObjectDefinition.model_validate(
            {
                "entity_type": "object",
                "id": "medicine-kit",
                "name": "Medicine Kit",
                "object_archetype_id": "medical-supplies",
                "initial_placement": {
                    "placement_type": "location",
                    "location_id": "field-clinic",
                },
                "unknown": True,
            }
        )


def test_character_definition_discriminator_parses_both_character_variants() -> None:
    adapter: TypeAdapter[CharacterDefinition] = TypeAdapter(CharacterDefinition)

    player = adapter.validate_python(
        {
            "entity_type": "player_character",
            "id": "marin",
            "name": "Marin",
            "character_archetype_id": "scout",
            "initial_location_id": "field-clinic",
        }
    )
    npc = adapter.validate_python(_valid_npc_data())

    assert isinstance(player, PlayerCharacterDefinition)
    assert isinstance(npc, NpcCharacterDefinition)


def test_entity_definition_rejects_unknown_discriminator() -> None:
    adapter: TypeAdapter[EntityDefinition] = TypeAdapter(EntityDefinition)

    with pytest.raises(ValidationError):
        adapter.validate_python({"entity_type": "unknown"})


def test_object_placement_is_discriminated_strict_and_immutable() -> None:
    adapter: TypeAdapter[ObjectPlacementDefinition] = TypeAdapter(
        ObjectPlacementDefinition
    )
    location = adapter.validate_python(
        {"placement_type": "location", "location_id": "field-clinic"}
    )
    possessed = adapter.validate_python(
        {"placement_type": "possessed", "character_id": "sela"}
    )

    assert isinstance(location, LocationPlacementDefinition)
    assert isinstance(possessed, PossessedPlacementDefinition)
    with pytest.raises(ValidationError):
        location.location_id = "elsewhere"
    for value in (
        {
            "placement_type": "location",
            "location_id": "field-clinic",
            "character_id": "sela",
        },
        {"placement_type": "location"},
        {"placement_type": "location", "location_id": 1},
        {"placement_type": "unknown", "location_id": "field-clinic"},
    ):
        with pytest.raises(ValidationError):
            adapter.validate_python(value)


def test_npc_goals_and_collection_preserve_yaml_order_as_immutable_tuples() -> None:
    npc = NpcCharacterDefinition.model_validate(
        {
            "entity_type": "npc_character",
            "id": "sela",
            "name": "Sela",
            "character_archetype_id": "medic",
            "initial_location_id": "field-clinic",
            "identity_summary": "A focused field medic.",
            "goals": [
                {"id": "keep-people-safe", "description": "Protect patients."},
                {"id": "preserve-supplies", "description": "Avoid waste."},
            ],
            "initial_plan": "Check the injured.",
            "decision_policy": {"policy_type": "hybrid", "policy_id": "medic-routine"},
        }
    )
    collection = EntityCollectionDefinition.model_validate(
        {
            "entities": [
                {
                    "entity_type": "player_character",
                    "id": "marin",
                    "name": "Marin",
                    "character_archetype_id": "scout",
                    "initial_location_id": "field-clinic",
                },
                npc.model_dump(),
            ]
        }
    )

    assert [goal.id for goal in npc.goals] == ["keep-people-safe", "preserve-supplies"]
    assert isinstance(npc.goals, tuple)
    assert isinstance(collection.entities, tuple)
    with pytest.raises(ValidationError):
        npc.goals[0].description = "Changed"
    with pytest.raises(ValidationError):
        collection.entities = ()


@pytest.mark.parametrize("goals", [[], "goal", {"id": "goal"}])
def test_npc_rejects_empty_or_non_collection_goals(goals: object) -> None:
    data = _valid_npc_data()
    data["goals"] = goals

    with pytest.raises(ValidationError):
        NpcCharacterDefinition.model_validate(data)


def test_npc_rejects_blank_initial_plan() -> None:
    data = _valid_npc_data()
    data["initial_plan"] = "   "

    with pytest.raises(ValidationError):
        NpcCharacterDefinition.model_validate(data)


@pytest.mark.parametrize("policy_type", ["rule", "llm", "hybrid"])
def test_decision_policy_reference_accepts_each_supported_type(
    policy_type: str,
) -> None:
    policy = DecisionPolicyReference.model_validate(
        {"policy_type": policy_type, "policy_id": "supported-policy"}
    )

    assert policy.policy_type == policy_type


@pytest.mark.parametrize("value", ["entity", {"id": "marin"}, 1])
def test_entity_collection_rejects_non_list_or_tuple_values(value: object) -> None:
    with pytest.raises(ValidationError):
        EntityCollectionDefinition.model_validate({"entities": value})


def test_models_defer_semantic_reference_and_player_count_validation() -> None:
    collection = EntityCollectionDefinition.model_validate(
        {
            "entities": [
                {
                    "entity_type": "player_character",
                    "id": "duplicate",
                    "name": "First",
                    "character_archetype_id": "missing-archetype",
                    "initial_location_id": "missing-location",
                },
                {
                    "entity_type": "player_character",
                    "id": "duplicate",
                    "name": "Second",
                    "character_archetype_id": "missing-archetype",
                    "initial_location_id": "missing-location",
                },
            ]
        }
    )

    assert len(collection.entities) == 2


def test_models_defer_possession_goal_and_policy_reference_validation() -> None:
    npc_data = _valid_npc_data()
    npc_data["initial_location_id"] = "missing-location"
    npc_data["goals"] = [
        {"id": "duplicate-goal", "description": "First."},
        {"id": "duplicate-goal", "description": "Second."},
    ]
    npc_data["decision_policy"] = {
        "policy_type": "llm",
        "policy_id": "missing-policy",
    }
    collection = EntityCollectionDefinition.model_validate(
        {
            "entities": [
                npc_data,
                {
                    "entity_type": "object",
                    "id": "medicine-kit",
                    "name": "Medicine Kit",
                    "object_archetype_id": "missing-archetype",
                    "initial_placement": {
                        "placement_type": "possessed",
                        "character_id": "missing-character",
                    },
                },
            ]
        }
    )

    assert len(collection.entities) == 2


@pytest.mark.parametrize("model", [GoalDefinition, DecisionPolicyReference])
def test_auxiliary_models_reject_invalid_identifiers_and_blank_text(
    model: type[BaseModel],
) -> None:
    if model is GoalDefinition:
        value = {"id": "Invalid_ID", "description": "   "}
    else:
        value = {"policy_type": "llm", "policy_id": "Invalid_ID"}

    with pytest.raises(ValidationError):
        model.model_validate(value)
